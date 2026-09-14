/** `explain` · `graph` · `path` — the group that does NOT rank.
 *  Twin of `src/fux/graph/__init__.py` (R4's one-to-many off the verb split).
 *
 * | verb | question | answer |
 * |---|---|---|
 * | `explain` | what does this document point at? | its outbound edges, and its community |
 * | `graph` | what surrounds the answer to this query? | ranked seeds, PPR-expanded |
 * | `path` | how is A connected to B? | every simple directed route, most reliable first |
 *
 * **None of them ranks documents by relevance.** That is `ask`. The lane
 * answers the questions term statistics *cannot* — supersession, near
 * duplication, "what else was decided when this was decided" — with
 * relationships the documents themselves stated.
 *
 * **Emptiness is an answer here.** `path` returning no route is a fact about
 * the corpus, not a failure to search hard enough.
 *
 * 🔴 Node rebuilds the plane in memory from the committed records; it does not
 * read Python's derived `.fux/runtime/graph.json` (SR-NODE-SEARCH decision 6's
 * reasoning applied to the graph plane — the digest must EQUAL Python's, and
 * reading Python's file would prove nothing).
 */
import { buildPlane } from "../graph/plane.mjs";
import { TAG_PREFIX } from "../graph/model.mjs";
import { ALL_KINDS, EDGE_KINDS, expand, routes } from "../graph/walk.mjs";
import { iterShardPaths, rawRecordLines } from "../store/reader.mjs";
import { runQuery } from "../query/run.mjs";
import { loadTune } from "../config/tune.mjs";
import { FuxError } from "../errors.mjs";

function allRecords(root) {
  const out = [];
  for (const path of iterShardPaths(root)) {
    const [, lines] = rawRecordLines(path);
    for (const line of lines) out.push(JSON.parse(line.toString("utf8")));
  }
  return out;
}

/** Accept either a doc id (`file:docs/a.md`) or the `loc` a human types.
 *  A user reads `docs/a.md` out of `find` and types it back; requiring the
 *  prefix would make the two verbs disagree about what a document is called. */
function resolveDoc(given) {
  if (given.startsWith("file:") || given.startsWith("url:") || given.startsWith(TAG_PREFIX)) {
    return given;
  }
  return `file:${given}`;
}

/** Refuse a node nothing knows about, naming which kind it was.
 *
 * ⚠ **Three states, not two.** *No route* and *no such document* are different
 * answers, and reporting the first for the second is a true sentence about a
 * document that does not exist. A tag is a node in the plane rather than a
 * record in the index, so the plane is what knows it. */
function refuseUnknown(records, plane, nodeId, flag) {
  if (nodeId.startsWith(TAG_PREFIX)) {
    if (!plane.graph.nodes.includes(nodeId)) {
      throw new FuxError(
        `${nodeId} is not a tag in this index. \`fux explain\` on a document ` +
        "lists the tags it declares",
      );
    }
    return;
  }
  if (!records.some((r) => r.id === nodeId)) {
    throw new FuxError(
      `${nodeId} is not in the index${flag}. \`fux find\` locates a document; ` +
      "`fux add` puts one in",
    );
  }
}

/** The human-facing name of a node. Tags have no location and stay as-is. */
function locOf(nodeId) {
  if (nodeId.startsWith(TAG_PREFIX)) return nodeId;
  const at = nodeId.indexOf(":");
  return at >= 0 ? nodeId.slice(at + 1) : nodeId;
}

/** One document's outbound edges and its community. */
export function runExplain(root, args) {
  if (!args._[0]) { process.stderr.write("error: explain needs a document id\n"); return 1; }
  const records = allRecords(root);
  const plane = buildPlane(records);
  const docId = resolveDoc(args._[0]);

  const edges = plane.graph.outEdges(docId);
  const label = plane.communityOf(docId);

  if (!edges.length && label === null) {
    // **Three states, not two** (W-63): a `fux remove`d document answering as
    // though it were still indexed is the case that made it visible.
    refuseUnknown(records, plane, docId, "");
    if (args.json) {
      process.stdout.write(JSON.stringify({ doc: docId, edges: [], community: null }, null, 2) + "\n");
    } else {
      process.stdout.write(`${docId} has no recorded relationships.\n`);
    }
    return 0;
  }

  if (args.json) {
    process.stdout.write(JSON.stringify({
      doc: docId,
      edges: edges.map((e) => ({ kind: e.kind, dst: e.dst, grade: e.grade })),
      community: label,
    }, null, 2) + "\n");
    return 0;
  }

  process.stdout.write(`${docId}\n`);
  for (const edge of edges) {
    process.stdout.write(`  ${edge.kind.padEnd(5)} ${edge.dst}  (grade ${edge.grade})\n`);
  }
  if (label !== null) {
    const siblings = plane.members(label).filter((n) => n !== docId);
    process.stdout.write(`\n  community ${label} — ${siblings.length} other node(s)\n`);
  }
  return 0;
}

/** The three W-160 parameters off `args`, as `expand` wants them.
 *  All three resolve to their inert values when the flags are absent. */
function walkParameters(args) {
  let kinds = ALL_KINDS;
  if (args.kinds) {
    const named = args.kinds.split(",").map((k) => k.trim()).filter(Boolean);
    const unknown = named.filter((k) => !EDGE_KINDS.includes(k)).sort();
    if (unknown.length) {
      throw new FuxError(
        `--kinds names ${unknown.join(", ")}, which is not an edge kind. ` +
        `The kinds this index mints are ${EDGE_KINDS.join(", ")}`,
      );
    }
    kinds = new Set(named);
  }
  return {
    kinds,
    linkIdfOn: args.linkIdf === true,
    maxHops: args.maxHops ?? null,
  };
}

/** `[seed rows, seed ids]` — from `--seed`, or from the query's top-k.
 *
 * ⚠ **The query form is DEFINED as `--seed` over `lexical`'s top-k**, which is
 * why both come back through one function: two code paths would be free to
 * disagree about `seedDepth`, about mass order, or about which candidate
 * generator ran. Twin of `graph/__init__.py::_seeds_of`. */
function seedsOf(root, args, records, plane, tune) {
  const given = args.seed ?? [];
  const query = args._.join(" ");
  if (given.length && query) {
    throw new FuxError(
      'pass a query or --seed, not both. `fux graph "<q>"` walks from the ' +
      "query's best answers; `fux graph --seed <id>` walks from the documents " +
      "you name, in the order you name them",
    );
  }
  if (given.length) {
    const seeds = given.map(resolveDoc);
    for (const seed of seeds) refuseUnknown(records, plane, seed, " (--seed)");
    // 🔴 **`score` is `null` and `rank` carries the order.** A seed named by
    // hand has a rank and not a ranking, and the walk's internal `1/(i+1)`
    // mass would be a third incomparable number in that column. It would also
    // DIVERGE: seed 0's mass is exactly 1.0, which Python writes `1.0` and
    // `JSON.stringify` writes `1`. `null` is `null` in both. Twin of
    // `graph/__init__.py::_seeds_of`.
    return [
      seeds.map((s, i) => ({ path: locOf(s), id: s, role: "seed", score: null, rank: i + 1 })),
      seeds,
    ];
  }
  if (!query) {
    throw new FuxError(
      "`fux graph` needs a query or at least one --seed. " +
      '`fux graph "how does ranking work"` walks from the best answers; ' +
      "`fux graph --seed docs/a.md` walks from a document you name",
    );
  }
  const { results } = runQuery(root, query, tune.seedDepth, { tune });
  return [
    results.map((r) => ({ path: locOf(r.id), id: r.id, role: "seed", score: r.score })),
    results.map((r) => r.id),
  ];
}

/** The neighbourhood around a query's best answers, or around named seeds. */
export function runGraph(root, args) {
  const records = allRecords(root);
  const plane = buildPlane(records);
  // Loaded ONCE and used twice — for the seed query and for the walk. Two loads
  // could disagree if the file changed between them, producing a neighbourhood
  // around seeds that were ranked under different weights.
  const tune = loadTune(root, { enabled: args.noTune !== true });

  const [seedRows, seeds] = seedsOf(root, args, records, plane, tune);

  // `seedDepth` and `expandLimit` are separately tunable because they answer
  // different questions: how much of the ranking to trust as a starting point,
  // and how far the walk may wander from it.
  const expanded = expand(plane.graph, seeds, {
    limit: tune.expandLimit,
    damping: tune.damping,
    iterations: tune.iterations,
    laziness: tune.laziness,
    ...walkParameters(args),
  });

  const nodes = [
    ...seedRows,
    ...expanded.map(([node, score]) => ({ path: locOf(node), id: node, role: "expanded", score })),
  ];

  if (args.json) {
    process.stdout.write(JSON.stringify({ nodes }, null, 2) + "\n");
    return 0;
  }
  if (!nodes.length) { process.stdout.write("No confident matches.\n"); return 0; }
  for (const node of nodes) {
    // A hand-named seed has no score — its column carries `#rank` instead.
    const cell = node.score !== null && node.score !== undefined
      ? node.score.toFixed(4)
      : `#${node.rank}`.padStart(6);
    process.stdout.write(`${cell}  ${node.role.padEnd(8)} ${node.path}\n`);
  }
  return 0;
}

/** Every simple directed route between two documents, within `--hops`. */
export function runPath(root, args) {
  if (!args._[0] || !args._[1]) {
    process.stderr.write("error: path needs two document ids\n");
    return 1;
  }
  const records = allRecords(root);
  const plane = buildPlane(records);
  const src = resolveDoc(args._[0]);
  const dst = resolveDoc(args._[1]);
  // Both ends, BEFORE the search: *no route* and *no such document* are
  // different answers and `path` gave the first one for both.
  refuseUnknown(records, plane, src, " (FROM)");
  refuseUnknown(records, plane, dst, " (TO)");

  const hops = args.hops ?? 2;
  // `--hops` bounds the search and stays a CLI argument; `hop_decay` only
  // orders what the search found.
  const tune = loadTune(root, { enabled: args.noTune !== true });
  const found = routes(plane.graph, src, dst, { hops, hopDecay: tune.hopDecay });

  if (args.json) {
    process.stdout.write(JSON.stringify({
      from: src,
      to: dst,
      paths: found.map((route) => ({
        hops: route.hops.map((e) => ({ kind: e.kind, src: e.src, dst: e.dst, grade: e.grade })),
        reliability: route.reliability,
      })),
    }, null, 2) + "\n");
    return 0;
  }

  if (!found.length) {
    process.stdout.write(`No route from ${src} to ${dst} within ${hops} hop(s).\n`);
    return 0;
  }
  for (const route of found) {
    const trail = route.hops.map((e) => `[${e.kind}] ${e.dst}`).join(" -> ");
    process.stdout.write(`${route.reliability.toFixed(4)}  ${src} -> ${trail}\n`);
  }
  return 0;
}
