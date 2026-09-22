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
 * discordant. [SR-NODE-SEARCH](../../../records/0153_node-search.md)
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
import { FB_DOCS, feedbackTerms } from "./rm3.mjs";
import { rank, Weighting } from "./rank.mjs";
import { signals } from "./confidence.mjs";
import { headingsFor } from "./headings.mjs";
import { fuseResults } from "./fuse.mjs";
import * as expandMod from "./expand.mjs";
import { tokenizePairs } from "./tokenize.mjs";
import { rerank, DEPTH as RERANK_DEPTH } from "./rerank.mjs";
import { applyPin } from "../correct.mjs";
import { loadTune } from "../config/tune.mjs";
import { archivedDirSet } from "../ingest/gitdir.mjs";
import { tiers } from "./compose.mjs";
import { recordFor } from "../store/reader.mjs";
import { idf } from "./bm25f.mjs";

export { RERANK_DEPTH };

/** The document-level multipliers and the directories they apply to.
 *
 * The weights come from `.fux/tune.toml`; the archived **declaration** still
 * comes from the committed dirs list, never from a path convention
 * (SR-DIR-LIST decision 4). `archivedDirSet` carries the tolerance: a corpus
 * whose dirs list cannot be read still answers, demoting nothing. */
export function archivedRanking(root, tune) {
  const dirs = archivedDirSet(root);
  return new Weighting({
    archivedWeight: tune.archivedWeight,
    archivedDirs: dirs,
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

/**
 * **A graph-lifted #1 may LOWER the band. It may never raise it.**
 *
 * SR-CONFIDENCE §Consequences names this as the graph half of decision 4's
 * guard. Decision 4 stops an expansion term raising a document's own band by
 * never handing the block the expansion; the graph tier needs an active guard
 * instead, because it adds no terms — it changes **which document the band is
 * describing**.
 *
 * `rank()` computes `top_doc_hashes` from the document it ranked first. When
 * the walk promotes a different one, that field describes a document the reader
 * was never shown. Both obvious answers are wrong on their own: leaving it
 * bands a document nobody saw, and recomputing it lets a document the LINKS
 * lifted arrive with a higher `doc_coverage` than the words ever gave it.
 *
 * So: recompute for the shown document, and keep the lexical #1's value
 * whenever the shown document's is higher. Weighted by `idf` and not counted,
 * because that is how `doc_coverage` itself is computed — comparing counts
 * would let three stopwords outrank one rare term and reverse the guard on
 * exactly the queries it matters for. **Never throws.**
 */
function bandGuard(root, query, statsOut, results) {
  if (!results.length || !results[0].boosted) return;
  try {
    const lexical = statsOut.top_doc_hashes;
    if (lexical === null || lexical === undefined) return;
    const record = recordFor(root, results[0].id);
    if (record === null || record === undefined) return;
    const terms = record.terms ?? {};
    const shown = queryTermHashes(query).filter((h) => h in terms);
    const df = statsOut.df ?? {};
    const n = statsOut.n ?? 0;
    const weight = (hashes) => hashes.reduce((sum, h) => sum + idf(df[h] ?? 0, n), 0);
    statsOut.top_doc_hashes = weight(shown) <= weight(lexical) ? shown : lexical;
  } catch {
    // A signal must not be able to take an answer down with it.
  }
}

/** A `Tune` with some fields overridden, prototype and getters intact. */
function withTier(tune, overrides) {
  return Object.assign(Object.create(Object.getPrototypeOf(tune)), tune, overrides);
}

/** One arm: tune, scan, rank, rerank, band.
 *
 * `useTune=false` is `--no-tune`: `.fux/tune.toml` is not read at all, so the
 * answer is the engine's own (SR-TUNE decision 11). A caller that has already
 * loaded a `Tune` passes it as `tune` rather than paying for a second parse. */
export function runQuery(root, query, top, {
  tune = null, useTune = true, expand = "", wantConfidence = false,
  compose = true, related: wantRelated = true,
} = {}) {
  let resolved = tune ?? loadTune(root, { enabled: useTune });
  // 🔴 **The freeze, enforced on the one line where it could be lost.**
  // `compose: false` is `fux lexical`, which has no graph tier by definition;
  // forcing both booleans off here rather than trusting the caller means a
  // repository whose `tune.toml` turns the tier on cannot make the frozen
  // baseline verb stop being a baseline.
  //
  // ⚠ **`Object.create` + `assign`, never a `{...spread}`.** `Tune.scoring` is
  // a PROTOTYPE GETTER, and spreading an instance into an object literal keeps
  // the own properties and silently drops it — `resolved.scoring` two lines
  // below would then be `undefined` and every score would be computed at
  // default weights, on the frozen baseline verb, with nothing failing.
  // W-168 step 5: RM3 is off on the frozen baseline too — feedback terms are
  // words the engine chose, and `lexical` is the words the user typed.
  if (!compose) resolved = withTier(resolved, { askBoost: false, askRelated: false, rm3Weight: 0.0 });
  else if (wantRelated === false) resolved = withTier(resolved, { askRelated: false });
  // After the two lines above, `wantRelated` and `resolved.askRelated` agree, so
  // the tier reads one of them and the verb reads the other without either
  // having to know about the flag that set it.
  const scoring = resolved.scoring;
  const weighting = archivedRanking(root, resolved);

  // W-76 Phase 6: when the reranker is on, retrieve DEEPER than the caller
  // asked and hand back `top` from the reordered list. A reranker that can only
  // shuffle the five documents already shown cannot promote the sixth, and the
  // sixth is where most of the recoverable failures are.
  //
  // W-161: the graph tier retrieves deeper for the same reason. A walk that can
  // only shuffle the five documents already shown cannot promote the sixth
  // either. `graphOn` is read from the tune, so `--no-tune` turns the tier off
  // with everything else and the depth goes back with it.
  const rerankWeight = resolved.rerankWeight;
  const graphOn = resolved.askBoost || resolved.askRelated;
  const depth = (rerankWeight > 0 || graphOn) ? Math.max(top, RERANK_DEPTH) : top;

  const queryHashes = queryTermHashes(query);
  let expansion = expandMod.build(
    queryHashes, expand ? queryTermHashes(expand) : [], resolved.expandWeight,
  );
  // W-168 step 5 — RM3. Off at 0.0, and off runs no first pass. A caller's own
  // `expand` wins. The first pass is un-expanded and writes no stats: the band
  // and `--why` describe the final pass only. Twin of `run_query`'s block.
  if (resolved.rm3Weight > 0 && !expand && queryHashes.length) {
    const first = scanAsk(root, query, Math.max(depth, FB_DOCS), { weighting, scoring });
    expansion = expandMod.build(
      queryHashes, feedbackTerms(root, first, queryHashes, scoring), resolved.rm3Weight,
    );
  }

  const statsOut = {};
  const window = scanAsk(root, query, depth, { weighting, scoring, statsOut, expansion });
  // W-162. **After the reranker, and the confidence block is built from the
  // PINNED list** — the band describes the answer the reader was shown, so a
  // pinned #1 the corpus barely supports must still say `weak`.
  //
  // ⚠ **The lexical core runs over the WINDOW, not over `top`**, so the graph
  // stage has something to promote from. The two agree exactly when the tier is
  // off: `rerank(window)[:depth][:top] === rerank(window)[:top]`, and
  // `applyPin` puts a pinned document at position 0 under either truncation.
  //
  // ⚠ **The pin goes in BEFORE the walk, and the order is a decision.** A pin
  // is an editorial override for one exact question; a walk is a corpus-wide
  // signal. Letting the walk re-order a pinned document off the top would mean
  // a person's explicit intervention could be overruled, silently, by a link
  // somebody else drew.
  const ordered = applyPin(root, query, maybeRerank(root, query, window, rerankWeight, depth), depth);
  // 🔴 **`find` shares Tier A and never computes Tier B.** `find` is `ask`'s
  // terse sibling — both are *ranked documents* — so a boost that moved one and
  // not the other would make the two verbs rank the same corpus differently,
  // which is a worse defect than the one the tier is for. But `find` pipes bare
  // paths and has no `related` rendering, and skipping the work here is not an
  // optimisation on this reader: `related` costs a `recordFor` per candidate on
  // top of a plane rebuild that already parses every committed record.
  const split = graphOn
    ? tiers(root, query, ordered, top, resolved, { wantRelated })
    : { results: ordered.slice(0, top), related: [] };
  const results = split.results;
  bandGuard(root, query, statsOut, results);

  return {
    results,
    // `null`, not `[]`, when the tier did not run: absent means NOT ASKED FOR
    // or NOT AVAILABLE, and `[]` means *no neighbours*. The `--json` key is
    // omitted on `null`, which is the distinction the schema declares.
    related: resolved.askRelated ? split.related : null,
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
