/** BM25F — weight THEN saturate, once. Twin of `src/fux/query/bm25f.py`.
 *
 * Every number here appears on both sides of the same fraction, which is why
 * `Scoring` is ONE object and not three parameters: a caller that passes the
 * weights and forgets `k1` reweights half a formula.
 */
import { TF_FIELDS } from "../store/format.mjs";

export const FIELD_WEIGHTS = [1.0, 3.0, 2.0, 1.5, 1.0];
if (FIELD_WEIGHTS.length !== TF_FIELDS.length) {
  throw new Error("field weights must align with TF_FIELDS");
}
export const K1 = 1.2;
export const B = 0.75;

export class Scoring {
  constructor(k1 = K1, b = B, weights = FIELD_WEIGHTS) {
    this.k1 = k1; this.b = b; this.weights = weights;
    Object.freeze(this);
  }
  /** True when this is the engine default, so callers can skip work. */
  get trivial() {
    return this.k1 === K1 && this.b === B
      && this.weights.length === FIELD_WEIGHTS.length
      && this.weights.every((w, i) => w === FIELD_WEIGHTS[i]);
  }
}

export const DEFAULT_SCORING = new Scoring();

/** ⚠ `Math.log` and Python's `math.log` disagree in the last ulp on ~0.7 % of
 *  inputs (Phase 0, measured on darwin and glibc). **Every difference is one
 *  ulp and none survives `round(9)`**, which is the sort key's own resolution
 *  — SR-RANKING decision 8a. This is the tolerance Arpit ruled, option (b). */
export function idf(df, n) { return Math.log((n - df + 0.5) / (df + 0.5) + 1); }

/** The BM25F numerator for one term in one document.
 *  `tf` may be shorter than `weights` — trailing zeros are omitted on the wire,
 *  so iterating `tf` rather than `weights` makes the short form free. */
export function weightedTf(tf, scoring = DEFAULT_SCORING) {
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
export function deriveWlen(flen, scoring = DEFAULT_SCORING) {
  let total = 0.0;
  const weights = scoring.weights;
  for (let i = 0; i < flen.length; i++) {
    const count = flen[i];
    if (count) total += weights[i] * count;
  }
  return total;
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
  scoring = DEFAULT_SCORING, termWeights = null,
) {
  if (n <= 0 || avgWlen <= 0) return 0.0;
  const wlen = typeof flen === "number" ? flen : deriveWlen(flen, scoring);
  const k1 = scoring.k1, b = scoring.b;
  let total = 0.0;
  for (const h of queryHashes) {
    const tf = terms[h];
    if (tf === undefined) continue;
    const wtf = weightedTf(tf, scoring);
    if (wtf === 0) continue;
    const denom = wtf + k1 * (1 - b + b * wlen / avgWlen);
    let contribution = idf(df[h] ?? 0, n) * wtf * (k1 + 1) / denom;
    if (termWeights !== null) contribution *= (termWeights[h] ?? 1.0);
    total += contribution;
  }
  return total;
}
