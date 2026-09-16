/**
 * The graph stage of `ask` — two tiers, one walk (W-161). Python's
 * `src/fux/query/compose.py`, twin for twin.
 *
 * `fux ask` is the composition SR-ASK names:
 *
 *     lexical ─► graph ─► split ─► confidence ─► refer
 *
 * This module is the middle two arrows: it takes the lexical core's ordered
 * window, walks the committed graph out of it, and splits what the walk
 * reached into **Tier A** (documents the words already retrieved, re-ordered
 * by `RRF(lexical rank, PPR rank)`) and **Tier B** (documents the words could
 * not retrieve at all, labelled `related` and never counted as an answer).
 *
 * 🔴 **Where this reader legitimately differs from Python, and why.**
 * Python's `compose.py` reads the derived `.fux/runtime/graph.json` and has no
 * tier when that file is absent or stale. **Node rebuilds the plane in memory
 * from the committed records instead**, exactly as `verbs/graph.mjs` already
 * does — SR-NODE-SEARCH decision 9, which ruled that behaviour *"the right one
 * for its audience"*: this reader exists for a clone with no Python, and
 * `.fux/runtime/` is written by `fux build`, which is Python. Requiring it
 * would make the tier absent precisely where this reader is the only one
 * present.
 *
 * **So the two readers are byte-equal wherever Python has a fresh plane**, and
 * diverge only on a corpus with no fresh build, where Python has no tier and
 * Node has one. That is decision 9's existing asymmetry showing through a new
 * surface, not a new one, and SR-NODE-SEARCH decision 16 states it rather than
 * leaving the harness to find it.
 *
 * ⚠ **This paragraph claimed a fresh plane was "every corpus the differential
 * arm runs on, because the golden ladder rungs are built" — and that was wrong
 * about the arm that actually gates a merge.** `node-arm.yml` runs the arm over
 * THIS repo from a bare checkout, where nothing had built anything, so CI sat at
 * **44 of 202 discordant** on 2026-09-16 with the workflow reporting it as a
 * Node transcription defect. Nothing was wrong with either reader. The ladder
 * rungs were built; this repo was not, and the sentence generalised from the
 * corpus that happened to be fine to the one that was not. `node-arm.yml` runs
 * `fux build` before both arms now, and a STALE plane counts as absent, which is
 * why the adversarial step rebuilds too.
 *
 * ⚠ **And it is not free.** Rebuilding the plane parses every committed record,
 * which is the work the B2 prefilter exists to avoid — so a Node `ask` with the
 * tier on pays a full parse the lexical answer alone does not. Node's latency
 * is unmeasured (W-148 row 2) and this is now one more reason it should not
 * stay that way. `ask_boost = false` and `ask_related = false` are what turn it
 * off.
 */

import { buildPlane } from "../graph/plane.mjs";
import { ppr } from "../graph/walk.mjs";
import { iterShardPaths, rawRecordLines, recordFor } from "../store/reader.mjs";
import { displayTitle } from "../store/format.mjs";
import { rrf } from "./fuse.mjs";
import { queryTermHashes } from "./scan.mjs";
// `pyRound9` and `cmpCodePoints`, not JS `toFixed` and `<`: the boosted
// order has to break exactly where Python's does, and JS `<` on strings is
// UTF-16 (W-107 hazard H1).
import { cmpCodePoints, pyRound9 } from "../compat/pyfloat.mjs";

/**
 * One Tier B document: reached by a link, matched by no word.
 *
 * **A different shape from a result on purpose.** A `related` document has no
 * BM25F score — that is the definition of the tier — so a shape carrying a
 * `score` would have to put something in it, and every candidate for that
 * something is a claim fux cannot make. The walk's PPR `mass` is reported under
 * its own name, and it is not comparable with a `score`.
 */
export class Related {
  constructor({ id, title, loc, mass, archived, route }) {
    this.id = id;
    this.title = title;
    this.loc = loc;
    this.mass = mass;
    this.archived = archived;
    this.route = route;
  }
}

/** Every committed record. The plane needs all of them: edges live on the
 *  documents that declare them, and a candidate set is by definition a subset
 *  that shares the query's vocabulary — which is exactly the wrong subset for
 *  finding what the vocabulary missed. */
function allRecords(root) {
  const out = [];
  for (const path of iterShardPaths(root)) {
    const [, lines] = rawRecordLines(path);
    for (const line of lines) out.push(JSON.parse(line.toString("utf8")));
  }
  return out;
}

/**
 * Split the lexical window into the boosted tier and the related tier.
 *
 * `ordered` is the lexical core's output over the **window**, not over `top`,
 * so the walk has something to promote from — W-76 Phase 6's argument for the
 * reranker, word for word, applied to a second re-orderer.
 *
 * **Never throws.** The graph tier is an enhancement to an answer that has
 * already been computed in full; a corpus with no edges, an unreadable shard or
 * a record that left between two reads all degrade to *no tier*.
 */
export function tiers(root, query, ordered, top, tune, { wantRelated = true } = {}) {
  const relatedOn = tune.askRelated && wantRelated;
  const on = tune.askBoost || relatedOn;
  if (ordered.length === 0 || !on) return { results: ordered.slice(0, top), related: [] };

  let plane;
  try {
    plane = buildPlane(allRecords(root));
  } catch {
    return { results: ordered.slice(0, top), related: [] };
  }

  const seeds = ordered.slice(0, tune.seedDepth).map((r) => r.id);
  // 🔴 **`ppr`, not `expand` — and the difference is the whole correctness of
  // arm A.** `expand()` drops the seeds, because `fux graph`'s question is
  // *what is AROUND these documents*; arm A's question is *how should these
  // documents be ordered*. A rank list the seeds cannot appear in gives every
  // seed a lexical contribution alone while every walked non-seed gets a
  // lexical contribution PLUS a PPR one — at `k = 60` that is `1/61 = 0.01639`
  // against `1/67 + 1/61 = 0.03132`, so every neighbour outranks every seed on
  // every query. See the Python twin: measured on fux's own repository, it
  // turned `ask --top 3` into the documents the words ranked 6th, 7th and 9th.
  const walkedAll = ppr(plane.graph, seeds, {
    damping: tune.damping,
    iterations: tune.iterations,
    laziness: tune.laziness,
    kinds: new Set(tune.askKinds.split(",")),
    linkIdfOn: tune.askLinkIdf,
    maxHops: tune.askMaxHops,
  });
  if (walkedAll.size === 0) return { results: ordered.slice(0, top), related: [] };

  // `(-score, id)` — `expand()`'s own key, so the Tier B list below is the list
  // `fux graph --seed <these ids>` prints, and `cmpCodePoints` because JS `<`
  // on strings is UTF-16 (W-107 hazard H1).
  const ranked = [...walkedAll].sort(
    (a, b) => (a[1] !== b[1] ? (a[1] > b[1] ? -1 : 1) : cmpCodePoints(a[0], b[0])),
  );
  const seedSet = new Set(seeds);
  const walked = ranked.filter(([node]) => !seedSet.has(node)).slice(0, tune.expandLimit);

  const inWindow = new Map(ordered.map((r, i) => [r.id, i]));
  const boostedIds = ranked.map(([node]) => node).filter((node) => inWindow.has(node));

  return {
    results: tune.askBoost ? boost(ordered, boostedIds, top, inWindow) : ordered.slice(0, top),
    related: relatedOn ? related(root, plane, query, walked, inWindow, tune) : [],
  };
}

/**
 * Arm A. Re-order the window by `RRF(lexical rank, PPR rank)`, take `top`.
 *
 * **Only the ORDER changes** — every result keeps the score `rank()` gave it.
 * See the Python twin's module docstring for why that shape was chosen here
 * and rejected for `-q` fusion: the deciding clause in `fuse.mjs`'s objection
 * is *with nothing saying why*, and here the moved row carries `boosted` and
 * its route.
 *
 * The sort key is `(-round9(fused), id)` with `id` compared by code point —
 * `fuseResults`' key exactly, so a boosted list breaks ties the way every other
 * list in this engine does and the two runtimes cannot order it differently.
 */
function boost(ordered, boostedIds, top, inWindow) {
  if (boostedIds.length === 0) return ordered.slice(0, top);

  const fused = rrf([ordered.map((r) => r.id), boostedIds]);
  const moved = new Set(boostedIds);
  const reordered = [...ordered].sort((a, b) => {
    const fa = -pyRound9(fused[a.id]);
    const fb = -pyRound9(fused[b.id]);
    if (fa !== fb) return fa < fb ? -1 : 1;
    return cmpCodePoints(a.id, b.id);
  });
  return reordered.slice(0, top).map((r, i) => {
    if (!moved.has(r.id)) return r;
    // `boosted` marks a row the WALK reached, not a row that moved. A walked
    // document already at #1 is still the reason #1 is #1, and marking only
    // movers would hide the tier's effect exactly where it agreed with the
    // words — the case a reader most needs to be able to see, because it is
    // the one that looks like nothing happened.
    return { ...r, boosted: true, route: `#${inWindow.get(r.id) + 1} -> #${i + 1} via graph` };
  });
}

/**
 * Arm B. Link-reached documents with no lexical match, each with its route.
 *
 * The lexical test reads the candidate's committed record — the same per-
 * document read `ask` already pays to print a heading — and tests the
 * **original query's** hashes, never an expansion's. That is SR-EXPAND's
 * refusal reaching this tier: a document matching only words a model invented
 * is not `related` to a question nobody asked.
 */
function related(root, plane, query, walked, inWindow, tune) {
  const hashes = new Set(queryTermHashes(query));
  const kinds = new Set(tune.askKinds.split(","));
  const out = [];
  for (const [node, mass] of walked) {
    if (inWindow.has(node) || out.length >= tune.askRelatedLimit) continue;
    const record = recordFor(root, node);
    if (record === null || record === undefined) continue;
    const terms = record.terms ?? {};
    if (Object.keys(terms).some((h) => hashes.has(h))) continue;
    out.push(new Related({
      id: node,
      title: displayTitle(record),
      loc: record.loc ?? node,
      mass,
      archived: Boolean(record.archived),
      route: routeOf(plane, node, inWindow, kinds),
    }));
  }
  return out;
}

/**
 * `#2 via ref` — the best-ranked seed that links to `node`, and the kind.
 *
 * **Best-ranked, not first-found.** A document reached from several seeds is
 * most honestly attributed to the one the reader is likeliest to have already
 * read; taking whatever the edge list yielded first would make the route a
 * function of shard order.
 */
function routeOf(plane, node, inWindow, kinds) {
  let best = null;
  for (const edge of plane.graph.edges) {
    // 🔴 The walk's own kind set, and filtering by it is not an optimisation:
    // with `ask_kinds = "ref"` an unfiltered scan reported `#2 via code`,
    // crediting an edge the walk was forbidden to follow and had not followed.
    // A route a reader cannot verify is worse than no route.
    if (!kinds.has(edge.kind)) continue;
    let other = null;
    if (edge.dst === node && inWindow.has(edge.src)) other = edge.src;
    else if (edge.src === node && inWindow.has(edge.dst)) other = edge.dst;
    if (other === null) continue;
    const rank = inWindow.get(other);
    if (best === null || rank < best[0]) best = [rank, edge.kind];
  }
  // Reached at more than one hop, so no seed links to it directly. Say that
  // rather than naming a hop that does not exist.
  if (best === null) return "via the walk";
  return `#${best[0] + 1} via ${best[1]}`;
}
