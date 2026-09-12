/** `run_query` — the shared spine of `ask`, `find` and `answer`.
 *
 * Twin of the pure half of `src/fux/query/__init__.py`. Everything that
 * decides an answer lives here; the verbs are projections of it, which is why
 * `find` cannot rank differently from `ask`.
 *
 * 🔴 **This is where `.fux/tune.toml` enters, and where it did not until
 * 2026-09-12.** The gap was invisible for a month because the differential
 * arm's Python side called `scan.ask` directly — the same seam Node's `find`
 * called — so **both readers were ignoring the same file**. Pointed at
 * `run_query`, the path `fux find` actually uses, fux's own repo went 90 of 174
 * discordant. [ADR-NODE-SEARCH](../../../docs/adr/0155_node-search.md)
 * decision 8.
 *
 * The order of stages is load-bearing and is Python's, exactly:
 *
 *     tune -> weighting + scoring -> scan at DEPTH -> rank -> rerank -> top
 *                                                                       |
 *                                             confidence, on the FINAL list <
 *
 * **Confidence is computed after the truncation, never before it.** `rank()`
 * supplies `df` and `n`; the scores come from the list the caller will
 * actually see. Reading them off the pre-rerank window would report a
 * `separation` for an ordering nobody was shown — and the reranker exists
 * precisely to change which document is first.
 */
import { ask as scanAsk, queryTermHashes } from "./scan.mjs";
import { rank, Weighting } from "./rank.mjs";
import { signals } from "./confidence.mjs";
import { headingsFor } from "./headings.mjs";
import { fuseResults } from "./fuse.mjs";
import * as expandMod from "./expand.mjs";
import { tokenizePairs } from "./tokenize.mjs";
import { rerank, DEPTH as RERANK_DEPTH } from "./rerank.mjs";
import { loadTune } from "../config/tune.mjs";
import { archivedDirSet } from "../ingest/gitdir.mjs";

export { RERANK_DEPTH };

/** The document-level multipliers and the directories they apply to.
 *
 * The weights come from `.fux/tune.toml`; the archived **declaration** still
 * comes from the committed dirs list, never from a path convention
 * (ADR-DIR-LIST decision 4). `archivedDirSet` carries the tolerance: a corpus
 * whose dirs list cannot be read still answers, demoting nothing. */
export function archivedRanking(root, tune) {
  const dirs = archivedDirSet(root);
  return new Weighting({
    archivedWeight: tune.archivedWeight,
    archivedDirs: dirs,
    supersededWeight: tune.supersededWeight,
    recencyHalfLifeDays: tune.recencyHalfLifeDays,
    priority: tune.priority,
  });
}

/** Proximity rerank, then truncate to what the caller asked for. */
function maybeRerank(root, query, results, weight, top) {
  if (weight <= 0) return results.slice(0, top);
  return rerank(root, query, results, { weight }).slice(0, top);
}

/** The confidence block, or `null`. **Never throws** — a signal that can fail a
 *  query is worse than no signal, and a caller that gets nothing sees an absent
 *  key, which is the honest report of *"not computed"*. */
function buildConfidence(query, stats, results, tune) {
  try {
    return signals(
      tokenizePairs(query), queryTermHashes(query),
      stats.df ?? {}, stats.n ?? 0, results.map((r) => r.score),
      {
        topDocHashes: stats.top_doc_hashes ?? null,
        separationFloor: tune.separationFloor,
        docCoverageFloor: tune.docCoverageFloor,
      },
    );
  } catch {
    return null;
  }
}

/** One arm: tune, scan, rank, rerank, band.
 *
 * `useTune=false` is `--no-tune`: `.fux/tune.toml` is not read at all, so the
 * answer is the engine's own (ADR-TUNE decision 11). A caller that has already
 * loaded a `Tune` passes it as `tune` rather than paying for a second parse. */
export function runQuery(root, query, top, {
  tune = null, useTune = true, expand = "", wantConfidence = false,
} = {}) {
  const resolved = tune ?? loadTune(root, { enabled: useTune });
  const scoring = resolved.scoring;
  const weighting = archivedRanking(root, resolved);

  // W-76 Phase 6: when the reranker is on, retrieve DEEPER than the caller
  // asked and hand back `top` from the reordered list. A reranker that can only
  // shuffle the five documents already shown cannot promote the sixth, and the
  // sixth is where most of the recoverable failures are.
  const rerankWeight = resolved.rerankWeight;
  const depth = rerankWeight > 0 ? Math.max(top, RERANK_DEPTH) : top;

  const queryHashes = queryTermHashes(query);
  const expansion = expandMod.build(
    queryHashes, expand ? queryTermHashes(expand) : [], resolved.expandWeight,
  );

  const statsOut = {};
  const window = scanAsk(root, query, depth, { weighting, scoring, statsOut, expansion });
  const results = maybeRerank(root, query, window, rerankWeight, top);

  return {
    results,
    confidence: wantConfidence ? buildConfidence(query, statsOut, results, resolved) : null,
    queryHashes,
    stats: statsOut,
    window,
    tune: resolved,
  };
}

/** Several phrasings, fused by rank. Arm 1 owns the confidence block.
 *
 * ⚠ **The band always describes ARM 1 only**, and that is deliberate: the
 * `separation_floor` is calibrated against BM25F, and a fused top-2 differs by
 * ~0.0003, so a band computed over fused scores would be measuring a different
 * quantity under the same name.
 *
 * ⚠ **Every arm carries the SAME expansion**, and the same `Tune` object: an
 * expansion describes the documents' vocabulary rather than one phrasing of the
 * question, and a second tune parse per arm would be pure cost. */
export function runFused(root, queries, top, opts = {}) {
  // De-duplicated in order, and NOT filtered: Python's `_queries_of` keeps the
  // positional query first and present whatever it is, which is what lets the
  // confidence block name one query rather than a set.
  const unique = [...new Set(queries)];
  const first = runQuery(root, unique[0] ?? "", top, opts);
  if (unique.length <= 1) return { ...first, fused: false };

  const arms = [first.results];
  for (const q of unique.slice(1)) {
    arms.push(runQuery(root, q, top, { ...opts, tune: first.tune, wantConfidence: false }).results);
  }
  return { ...first, results: fuseResults(arms, top), fused: true };
}

export { headingsFor, rank, expandMod as expand };
