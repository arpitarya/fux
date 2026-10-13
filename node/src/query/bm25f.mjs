/** BM25F — weight THEN saturate, once. Twin of `src/fux/query/bm25f.py`.
 *
 * Every number here appears on both sides of the same fraction, which is why
 * `Scoring` is ONE object and not three parameters: a caller that passes the
 * weights and forgets `k1` reweights half a formula.
 */
import { TF_FIELDS } from "../store/format.mjs";
import { fixed } from "../config/constants.mjs";

const IDF_OFFSET = fixed("bm25f", "idf_offset");

//: `k1`, `b`, the five field weights and `anchor` are `.fux/tune.toml [bm25f]`'s
//: and arrive on a `Scoring` built by `config/tune.mjs` (L12). Why each is what
//: the template ships — `b` MEASURED at 0.15 (W-144), anchor MEASURED at 1.0
//: (W-168 step 1) — is said once, beside its key in `templates/tune.toml.txt`.

export class Scoring {
  constructor(k1, b, weights, anchor, section) {
    if (!Array.isArray(weights) || weights.length !== TF_FIELDS.length) {
      throw new Error("field weights must align with TF_FIELDS");
    }
    if (typeof k1 !== "number" || typeof b !== "number" || typeof anchor !== "number") {
      throw new Error("Scoring needs k1, b and anchor — read from .fux/tune.toml [bm25f]");
    }
    if (typeof section !== "number") {
      throw new Error("Scoring needs section — read from .fux/tune.toml [ranking] section_weight");
    }
    this.k1 = k1; this.b = b; this.weights = weights;
    /** W-168 step 1 — the anchor field's weight (0 = OFF). Kept out of
     *  `weights` because that array is aligned index-for-index with TF_FIELDS,
     *  the five fields a record commits an `flen` for; anchor has no committed
     *  slot and is folded at read time from other documents' edges. */
    this.anchor = anchor;
    /** W-236 — `[ranking] section_weight`, B2's λ (SR-SECTIONS decision 5).
     *  `0.0` is OFF exactly as `anchor` is: neither candidate generator opens
     *  the section plane and `rank()` performs no section arithmetic. */
    this.section = section;
    Object.freeze(this);
  }
  /** The one test for *is the anchor fold live?* — twin of `Scoring.anchor_on`. */
  get anchorOn() { return this.anchor !== 0.0; }
  /** The one test for *is B2's best-section term live?* — twin of `Scoring.section_on`. */
  get sectionOn() { return this.section !== 0.0; }
}

/** ⚠ `Math.log` and Python's `math.log` disagree in the last ulp on ~0.7 % of
 *  inputs (Phase 0, measured on darwin and glibc). **Every difference is one
 *  ulp and none survives `round(9)`**, which is the sort key's own resolution
 *  — SR-RANKING decision 8a. This is the tolerance Arpit ruled, option (b). */
export function idf(df, n) { return Math.log((n - df + IDF_OFFSET) / (df + IDF_OFFSET) + 1); }

/** The BM25F numerator for one term in one document.
 *  `tf` may be shorter than `weights` — trailing zeros are omitted on the wire,
 *  so iterating `tf` rather than `weights` makes the short form free. */
export function weightedTf(tf, scoring) {
  let total = 0.0;
  const weights = scoring.weights;
  for (let i = 0; i < tf.length; i++) {
    const count = tf[i];
    if (count) total += weights[i] * count;
  }
  return total;
}

/** The length normaliser, from committed per-field counts and live weights.
 *  **The one place this arithmetic exists** — four callers need it, and four
 *  copies is how they drift. */
export function deriveWlen(flen, scoring, anchorLen = 0) {
  let total = 0.0;
  const weights = scoring.weights;
  for (let i = 0; i < flen.length; i++) {
    const count = flen[i];
    if (count) total += weights[i] * count;
  }
  // W-168 step 1: a heavily linked-to document is a LONGER document. Leaving
  // anchor out of the normaliser is what lets a link farm max out a term with
  // no length price, so it is in, at the weight the numerator uses.
  if (anchorLen) total += scoring.anchor * anchorLen;
  return total;
}

/** One term's summand — **the only place this arithmetic is written.**
 *
 *  Extracted from `scoreRecord`'s loop so the per-term attribution `--why`
 *  prints (W-210) is the *same* expression the score was built from rather
 *  than a second copy of it. Same operations in the same order, so the double
 *  result is bit-identical and the differential law against Python cannot pick
 *  up a difference from the extraction.
 *
 *  ⚠ **`wtf` arrives already weighted**, not as a `tf` list, because the anchor
 *  fold adds to it before saturation — BM25F is weight-then-saturate ONCE — and
 *  a signature taking `tf` would invite a caller to saturate twice.
 *
 *  ⚠ **Nothing in `node/` calls this yet.** The Node reader has no `--why`
 *  surface, so the attribution itself is Python-only today; the seam is
 *  transcribed with the formula so that a future port has one place to reach
 *  for, rather than re-deriving the expression from the Python.
 */
export function termContribution(wtf, wlen, dfH, n, avgWlen, scoring) {
  const denom = wtf + scoring.k1 * (1 - scoring.b + scoring.b * wlen / avgWlen);
  return idf(dfH, n) * wtf * (scoring.k1 + 1) / denom;
}

/** Sum of each matched query term's weight-then-saturate contribution.
 *
 * ⚠ `termWeights === null` performs **no multiply at all** — not a multiply by
 * 1.0. An unexpanded query must do exactly the float arithmetic it did before
 * `--expand` existed, or the differential law picks up a last-bit difference
 * from the feature merely being present.
 */
export function scoreRecord(
  terms, flen, queryHashes, df, n, avgWlen,
  scoring, termWeights = null, anchorTf = null, anchorLen = 0,
) {
  if (n <= 0 || avgWlen <= 0) return 0.0;
  let wlen;
  if (typeof flen === "number") wlen = flen;
  else wlen = anchorTf !== null ? deriveWlen(flen, scoring, anchorLen) : deriveWlen(flen, scoring);
  const anchorWeight = scoring.anchor;
  let total = 0.0;
  for (const h of queryHashes) {
    const tf = terms[h];
    let wtf;
    if (anchorTf === null) {
      // ⚠ No arithmetic at all when the field is off — not a multiply by zero.
      if (tf === undefined) continue;
      wtf = weightedTf(tf, scoring);
    } else {
      // 🔴 `tf === undefined` is NOT a reason to skip: a document whose own
      // body never uses the word can still be reached by what its linkers
      // called it. That is the retrieval half of W-168 step 1, and this early
      // return was the second place it would have died silently.
      wtf = tf === undefined ? 0.0 : weightedTf(tf, scoring);
      const count = anchorTf[h];
      if (count) wtf += anchorWeight * count;
    }
    if (wtf === 0) continue;
    let contribution = termContribution(wtf, wlen, df[h] ?? 0, n, avgWlen, scoring);
    if (termWeights !== null) contribution *= (termWeights[h] ?? 1.0);
    total += contribution;
  }
  return total;
}
