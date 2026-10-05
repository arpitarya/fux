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
 * 🔴 Node reads `.fux/runtime/graph.json` when it is fresh and rebuilds the
 * plane in memory from the committed records when it is not (W-259,
 * SR-NODE-SEARCH decision 9) — `graph/plane.mjs::planeFor`. The differential
 * arm forces the rebuild: the digest must EQUAL Python's, and Node reading
 * Python's file would prove nothing.
 *
 * **The records are read only when a refusal needs them.** A plane read from
 * `graph.json` needs no pass over the shards, and the one question it cannot
 * answer — *is this id a document at all?* — is asked of the records, lazily,
 * exactly as before.
 */
import { planeFor } from "../graph/plane.mjs";
import { TAG_PREFIX } from "../graph/model.mjs";
import { ALL_KINDS, EDGE_KINDS, EXPANSION_BUDGET, expand, routes } from "../graph/walk.mjs";
import { graphRecords, Shards } from "../store/reader.mjs";
import { runQuery } from "../query/run.mjs";
import { loadTune } from "../config/tune.mjs";
import { FuxError } from "../errors.mjs";
import { fixed } from "../config/constants.mjs";

const JSON_INDENT = fixed("json", "indent");

/** Accept either a doc id (`file:docs/a.md`) or the `loc` a human types.
 *  A user reads `docs/a.md` out of `find` and types it back; requiring the
 *  prefix would make the two verbs disagree about what a document is called. */
function resolveDoc(given) {
  if (given.startsWith("file:") || given.startsWith("url:") || given.startsWith(TAG_PREFIX)) {
    return given;
  }
  return `file:${given}`;
}

/** The committed records' `{id, edges}`, read on first use through the call's
 *  `Shards` — never when the plane came from `graph.json` and nothing asks. */
export function lazyRecords(root, shards) {
  let records = null;
  return () => (records ??= graphRecords(root, shards));
}

/** Refuse a node nothing knows about, naming which kind it was.
 *
 * ⚠ **Three states, not two.** *No route* and *no such document* are different
 * answers, and reporting the first for the second is a true sentence about a
 * document that does not exist. A tag is a node in the plane rather than a
 * record in the index, so the plane is what knows it. */
function refuseUnknown(recordsOf, plane, nodeId, flag) {
  if (nodeId.startsWith(TAG_PREFIX)) {
    if (!plane.graph.nodes.includes(nodeId)) {
      throw new FuxError(
        `${nodeId} is not a tag in this index. \`fux explain\` on a document ` +
        "lists the tags it declares",
      );
    }
    return;
  }
  if (!recordsOf().some((r) => r.id === nodeId)) {
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

// -- the payloads: ONE builder per verb, read by the CLI AND the library ------
//
// 🔴 **W-262 (Arpit, 2026-10-04, W-251 #4): the library returns what `--json`
// prints.** `index.mjs` mirrored `api.py`'s older helpers — `{id, community,
// members, edges}`, a breadth-first best route, a hop-ring walk seeded from the
// BOOSTED ranking — and both differed from both CLIs. The CLI's shapes carry
// rulings (SR-CLI decision 13, SR-GRAPH decision 13, `truncated` on `path`), so
// the library moved to them, and the computation lives here once. Twins of
// `graph/__init__.py::explain_payload / graph_payload / path_payload`.
//
// Each takes the plane and the lazy record reader its caller chose: the CLI's
// `planeFor` (graph.json when fresh), the library's in-memory rebuild.

/** `fux explain --json`'s payload: `{doc, edges, community}`. Throws
 *  `FuxError` for an id neither the index nor the plane knows. */
export function explainPayload(recordsOf, plane, doc) {
  const docId = resolveDoc(doc);
  const edges = plane.graph.outEdges(docId);
  const label = plane.communityOf(docId);
  if (!edges.length && label === null) {
    // **Three states, not two** (W-63): a `fux remove`d document answering as
    // though it were still indexed is the case that made it visible.
    refuseUnknown(recordsOf, plane, docId, "");
  }
  return {
    doc: docId,
    edges: edges.map((e) => ({ kind: e.kind, dst: e.dst, grade: e.grade })),
    community: label,
  };
}

/** One document's outbound edges and its community. */
export function runExplain(root, args) {
  if (!args._[0]) { process.stderr.write("error: explain needs a document id\n"); return 1; }
  const shards = new Shards(root);
  const plane = planeFor(root, shards);
  const payload = explainPayload(lazyRecords(root, shards), plane, args._[0]);
  const { doc: docId, community: label } = payload;

  if (args.json) {
    process.stdout.write(JSON.stringify(payload, null, JSON_INDENT) + "\n");
    return 0;
  }
  if (!payload.edges.length && label === null) {
    process.stdout.write(`${docId} has no recorded relationships.\n`);
    return 0;
  }

  process.stdout.write(`${docId}\n`);
  for (const edge of payload.edges) {
    process.stdout.write(`  ${edge.kind.padEnd(5)} ${edge.dst}  (grade ${edge.grade})\n`);
  }
  if (label !== null) {
    const siblings = plane.members(label).filter((n) => n !== docId);
    process.stdout.write(`\n  community ${label} — ${siblings.length} other node(s)\n`);
  }
  return 0;
}

/** The three W-160 parameters off `opts`, as `expand` wants them.
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
function seedsOf(root, args, recordsOf, plane, tune, shards) {
  const given = args.seed ?? [];
  const query = args.query ?? "";
  if (given.length && query) {
    throw new FuxError(
      'pass a query or --seed, not both. `fux graph "<q>"` walks from the ' +
      "query's best answers; `fux graph --seed <id>` walks from the documents " +
      "you name, in the order you name them",
    );
  }
  if (given.length) {
    const seeds = given.map(resolveDoc);
    for (const seed of seeds) refuseUnknown(recordsOf, plane, seed, " (--seed)");
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
  // 🔴 **The seed query is `lexical`, NOT `ask`** — `compose: false`. After
  // W-161 `ask` composes a graph tier, and seeding the walk from a list the
  // walk already re-ordered would make `fux graph "<q>"` a walk over its own
  // output: the seeds would move when the tier moved, and the orientation verb
  // would quietly become path-dependent. SR-GRAPH decision 13.
  const { results } = runQuery(root, query, tune.seedDepth, {
    tune, useTune: true, wantConfidence: false, compose: false, shards,
    // `--fast` for the seed query, as `fux graph --fast` in Python (W-242 Tier 1).
    fast: args.fast === true,
  });
  return [
    results.map((r) => ({ path: locOf(r.id), id: r.id, role: "seed", score: r.score })),
    results.map((r) => r.id),
  ];
}

/** `fux graph --json`'s payload: `{nodes}` — seeds first, then the walk.
 *
 * `opts` carries `query`, `seed`, `kinds` (comma-separated), `linkIdf`,
 * `maxHops` and `fast`; an absent one is not requested. `tune` is loaded ONCE
 * by the caller and used twice — for the seed query and for the walk. */
export function graphPayload(root, recordsOf, plane, tune, shards, opts) {
  const [seedRows, seeds] = seedsOf(root, opts, recordsOf, plane, tune, shards);

  // `seedDepth` and `expandLimit` are separately tunable because they answer
  // different questions: how much of the ranking to trust as a starting point,
  // and how far the walk may wander from it.
  const expanded = expand(plane.graph, seeds, {
    limit: tune.expandLimit,
    damping: tune.damping,
    iterations: tune.iterations,
    laziness: tune.laziness,
    ...walkParameters(opts),
  });

  return {
    nodes: [
      ...seedRows,
      ...expanded.map(([node, score]) => ({ path: locOf(node), id: node, role: "expanded", score })),
    ],
  };
}

/** The neighbourhood around a query's best answers, or around named seeds. */
export function runGraph(root, args) {
  // W-242 Tier 0 — one read of each shard, for the plane AND the seed query.
  const shards = new Shards(root);
  const plane = planeFor(root, shards);
  // Loaded ONCE and used twice — for the seed query and for the walk. Two loads
  // could disagree if the file changed between them, producing a neighbourhood
  // around seeds that were ranked under different weights.
  const tune = loadTune(root, { enabled: args.noTune !== true });
  const payload = graphPayload(root, lazyRecords(root, shards), plane, tune, shards, {
    query: args._.join(" "), seed: args.seed, kinds: args.kinds,
    linkIdf: args.linkIdf, maxHops: args.maxHops, fast: args.fast,
  });
  const { nodes } = payload;

  if (args.json) {
    process.stdout.write(JSON.stringify(payload, null, JSON_INDENT) + "\n");
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

/** `fux path --json`'s payload: `{from, to, paths, truncated}`. */
export function pathPayload(recordsOf, plane, tune, srcGiven, dstGiven, hops) {
  const src = resolveDoc(srcGiven);
  const dst = resolveDoc(dstGiven);
  // Both ends, BEFORE the search: *no route* and *no such document* are
  // different answers and `path` gave the first one for both.
  refuseUnknown(recordsOf, plane, src, " (FROM)");
  refuseUnknown(recordsOf, plane, dst, " (TO)");
  // `--hops` bounds the search and stays a CLI argument; `hop_decay` only
  // orders what the search found.
  const { routes: found, truncated } = routes(plane.graph, src, dst, {
    hops, limit: tune.pathLimit, hopDecay: tune.hopDecay, budget: EXPANSION_BUDGET,
  });
  return {
    from: src,
    to: dst,
    paths: found.map((route) => ({
      hops: route.hops.map((e) => ({ kind: e.kind, src: e.src, dst: e.dst, grade: e.grade })),
      reliability: route.reliability,
    })),
    // 🔴 **The half that matters.** stderr is invisible to exactly the callers
    // most likely to ask for a deep walk, so the boolean is in the payload —
    // and, since W-262, in the library's return value. Always present; `false`
    // is a claim, not an absence (W-48).
    truncated,
  };
}

/** Every simple directed route between two documents, within `--hops`. */
export function runPath(root, args) {
  if (!args._[0] || !args._[1]) {
    process.stderr.write("error: path needs two document ids\n");
    return 1;
  }
  const shards = new Shards(root);
  const plane = planeFor(root, shards);
  const hops = args.hops; // `.fux/output.toml [cli.path] hops`, resolved before dispatch
  const tune = loadTune(root, { enabled: args.noTune !== true });
  const payload = pathPayload(lazyRecords(root, shards), plane, tune, args._[0], args._[1], hops);
  const { from: src, to: dst, truncated } = payload;

  if (args.json) {
    process.stdout.write(JSON.stringify(payload, null, JSON_INDENT) + "\n");
    return 0;
  }
  const found = payload.paths;

  if (!found.length) {
    if (truncated) {
      // ⚠ Two different claims, and this is the one that was being made
      // wrongly: *no route within N hops* asserts the search finished.
      process.stdout.write(
        `No route from ${src} to ${dst} found within ${hops} hop(s) - the search was ` +
        `cut short after ${EXPANSION_BUDGET} steps. This is NOT the same as no route ` +
        "existing; narrow it with fewer --hops, or start from a more specific document.\n",
      );
    } else {
      process.stdout.write(`No route from ${src} to ${dst} within ${hops} hop(s).\n`);
    }
    return 0;
  }
  for (const route of found) {
    const trail = route.hops.map((e) => `[${e.kind}] ${e.dst}`).join(" -> ");
    process.stdout.write(`${route.reliability.toFixed(4)}  ${src} -> ${trail}\n`);
  }
  if (truncated) {
    process.stdout.write(
      `\n(the search was cut short after ${EXPANSION_BUDGET} steps - there may be ` +
      "routes, including better ones, that were not reached)\n",
    );
  }
  return 0;
}
