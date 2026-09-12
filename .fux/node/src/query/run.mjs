/** `run_query` — the shared spine of `ask`, `find` and `answer`.
 *
 * Twin of the pure half of `src/fux/query/__init__.py`. Everything that
 * decides an answer lives here; the verbs are projections of it, which is why
 * `find` cannot rank differently from `ask`.
 */
import { ask as scanAsk, queryTermHashes } from "./scan.mjs";
import { rank } from "./rank.mjs";
import { signals } from "./confidence.mjs";
import { headingsFor } from "./headings.mjs";
import { fuseResults } from "./fuse.mjs";
import * as expandMod from "./expand.mjs";
import { tokenizePairs } from "./tokenize.mjs";
import { DEFAULT_SCORING } from "./bm25f.mjs";

/** Retrieval depth when the proximity reranker is on. Off by default, so the
 *  default depth is `top` and the extra 15 candidates are never scored. */
export const RERANK_DEPTH = 20;

/** One arm: scan, rank, band. `expand` is a term slot, not a second question. */
export function runQuery(root, query, top, {
  weighting = null, scoring = DEFAULT_SCORING, expand = null,
  separationFloor = undefined, docCoverageFloor = undefined,
  wantConfidence = false, rerankWeight = 0.0,
} = {}) {
  const queryHashes = queryTermHashes(query);
  const expansion = expand
    ? expandMod.build(queryHashes, queryTermHashes(expand), expand.weight ?? 0.2)
    : null;

  const depth = rerankWeight > 0 ? Math.max(top, RERANK_DEPTH) : top;
  const statsOut = {};
  const results = scanAsk(root, query, depth, { weighting, scoring, statsOut, expansion });

  const out = results.slice(0, top);
  let confidence = null;
  if (wantConfidence) {
    const opts = { topDocHashes: statsOut.top_doc_hashes ?? null };
    if (separationFloor !== undefined) opts.separationFloor = separationFloor;
    if (docCoverageFloor !== undefined) opts.docCoverageFloor = docCoverageFloor;
    confidence = signals(
      tokenizePairs(query), queryHashes, statsOut.df ?? {}, statsOut.n ?? 0,
      results.map((r) => r.score), opts,
    );
  }
  return { results: out, confidence, queryHashes, stats: statsOut };
}

/** Several phrasings, fused by rank. Arm 1 owns the confidence block.
 *
 * ⚠ **The band always describes ARM 1 only**, and that is deliberate: the
 * `separation_floor` is calibrated against BM25F, and a fused top-2 differs by
 * ~0.0003, so a band computed over fused scores would be measuring a different
 * quantity under the same name. */
export function runFused(root, queries, top, opts = {}) {
  const unique = [...new Set(queries.filter((q) => q && q.trim()))];
  if (unique.length <= 1) {
    return { ...runQuery(root, unique[0] ?? "", top, opts), fused: false };
  }
  const first = runQuery(root, unique[0], top, opts);
  const arms = [first.results];
  for (const q of unique.slice(1)) {
    arms.push(runQuery(root, q, top, { ...opts, wantConfidence: false }).results);
  }
  return {
    results: fuseResults(arms, top),
    confidence: first.confidence,
    queryHashes: first.queryHashes,
    stats: first.stats,
    fused: true,
  };
}

export { headingsFor, rank, expandMod as expand };
