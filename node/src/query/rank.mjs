/** The scorer and the sort — ONE function, both candidate paths.
 *
 * Twin of `src/fux/query/rank.py`. This is why the differential law is
 * achievable: float addition is not associative, so a second implementation
 * that accumulates its own scores would diverge in the last bit. The
 * accelerator produces candidates and statistics; this does every arithmetic
 * operation, once, for both.
 *
 * Owned, with its Python twin, by [SR-RANKING](../../../records/0111_ranking.md).
 */
import { DEFAULT_SCORING, deriveWlen, scoreRecord } from "./bm25f.mjs";
import { displayTitle } from "../store/format.mjs";
import { isArchivedLoc } from "../ingest/gitdir.mjs";
import { pyRound9, cmpCodePoints } from "../compat/pyfloat.mjs";

export class Corpus {
  constructor(n = 0, totalWlen = 0.0) {
    this.n = n; this.totalWlen = totalWlen;
  }
  get avgWlen() { return this.n ? this.totalWlen / this.n : 0.0; }
}

// `isArchivedLoc` is `ingest/gitdir.mjs`'s, imported rather than copied — the
// same single definition `rank.py` imports from `ingest.gitdir`, so the marker
// and the demotion cannot disagree about one document.
export { isArchivedLoc };

function recordIsArchived(record, archivedDirs) {
  if (record.archived) return true;
  return archivedDirs.size > 0 && isArchivedLoc(record.loc, archivedDirs);
}

/** The score multiplier policy, in ONE place, for both candidate paths. */
export class Weighting {
  constructor({
    archivedDirs = new Set(), priority = [],
  } = {}) {
    // 🔴 The three DOCUMENT priors were REMOVED on 2026-09-13 (W-151, W-152):
    // supersession, retirement and age are FACTS, not weights. `archivedDirs`
    // stays because it is the fact's fallback for an index built before the
    // `archived` record property shipped — it scales nothing.
    this.archivedDirs = archivedDirs;
    this.priority = priority;   // [[prefix, weight], ...], longest-prefix wins
    Object.freeze(this);
  }
  get trivial() {
    return this.priority.length === 0;
  }
  priorityFor(loc) {
    let best = 1.0, bestLen = -1;
    for (const [prefix, w] of this.priority) {
      if (loc === prefix || loc.startsWith(prefix.endsWith("/") ? prefix : prefix + "/")) {
        if (prefix.length > bestLen) { best = w; bestLen = prefix.length; }
      }
    }
    return best;
  }
  /** The multiplier for one record: per-source priority, and nothing else. */
  of(record) {
    if (this.trivial) return 1.0;
    return this.priorityFor(record.loc || "");
  }
}

/** Rank candidates. `expansion` is `{hashes, required, weights}` or null. */
export function rank(
  candidates, queryHashes, df, corpus, top,
  { weighting = null, scoring = DEFAULT_SCORING, statsOut = null, expansion = null } = {},
) {
  const termWeights = expansion && expansion.weights && Object.keys(expansion.weights).length
    ? expansion.weights : null;
  const required = expansion && expansion.required ? expansion.required : queryHashes;
  const avgWlen = corpus.avgWlen;

  const w = weighting || new Weighting();
  const demote = !w.trivial;

  const scored = [];
  for (const record of candidates) {
    const terms = record.terms || {};
    // 🔴 The hallucinated-citation guard, before anything is scored: a
    // document matching ONLY expansion terms is not an answer to the question.
    let matches = false;
    for (const h of required) { if (h in terms) { matches = true; break; } }
    if (!matches) continue;

    let s = scoreRecord(
      terms, record.flen || [], queryHashes, df, corpus.n, avgWlen, scoring, termWeights,
    );
    const archived = recordIsArchived(record, w.archivedDirs);
    if (demote) s *= w.of(record);
    if (s > 0) scored.push([record, s, archived]);
  }

  // W-111 — the DECLARED tie-break, in Arpit's ratified order:
  //     superseded -> recency -> priority -> id
  // NONE of these is a weight: all three document priors were REMOVED on
  // 2026-09-13 (W-151, W-152), so `superseded` and `mtime` reach ranking here
  // and nowhere else. This reads the FACTS, only where the rounded scores tie.
  //
  // 🔴 `id` is compared by CODE POINT, never with `<` — W-107 hazard H1.
  scored.sort((A, B) => {
    const ra = -pyRound9(A[1]), rb = -pyRound9(B[1]);
    if (ra !== rb) return ra < rb ? -1 : 1;
    const sa = A[0].superseded ? 1 : 0, sb = B[0].superseded ? 1 : 0;
    if (sa !== sb) return sa - sb;
    const ma = -(A[0].mtime || 0), mb = -(B[0].mtime || 0);
    if (ma !== mb) return ma < mb ? -1 : 1;
    const pa = -w.priorityFor(A[0].loc || ""), pb = -w.priorityFor(B[0].loc || "");
    if (pa !== pb) return pa < pb ? -1 : 1;
    return cmpCodePoints(A[0].id, B[0].id);
  });

  // Marked AFTER the sort and over the WHOLE list: a neighbour comparison on
  // the truncated window would un-mark the last row, which is the one most
  // likely to have been decided by a coin-toss.
  const tied = new Set();
  for (let i = 0; i < scored.length - 1; i++) {
    if (pyRound9(scored[i][1]) === pyRound9(scored[i + 1][1])) { tied.add(i); tied.add(i + 1); }
  }

  if (statsOut !== null && scored.length) {
    const topTerms = scored[0][0].terms || {};
    statsOut.top_doc_hashes = queryHashes.filter((h) => h in topTerms);
  }

  return scored.slice(0, top).map(([record, s, archived], i) => ({
    id: record.id,
    title: displayTitle(record),
    loc: record.loc,
    score: s,
    archived,
    tie: tied.has(i),
    // W-153 — the committed git timestamp in whole unix seconds, or `null` for
    // a document outside git history. `null` is a claim, never an absence.
    mtime: record.mtime ?? null,
  }));
}
