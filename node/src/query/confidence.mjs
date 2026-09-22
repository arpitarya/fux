/** The confidence band — what fux says out loud about its own answer.
 *  Twin of `confidence.py`.
 *
 * Four signals and two floors. **The floors arrive from the CALLER**, never
 * from this module, so a single query cannot be judged by one floor and
 * reported with another — and both are published on the block, because a
 * `grounded` judged at 0.02 is a different claim from one judged at 0.10 and
 * absent publication the difference would be invisible.
 *
 * Owned, with its Python twin, by [SR-CONFIDENCE](../../../records/0141_confidence.md).
 */
import { idf } from "./bm25f.mjs";
import { termHash } from "../store/format.mjs";
import { tokenizePairs } from "./tokenize.mjs";

export const GROUNDED = "grounded";
export const WEAK = "weak";
export const PARTIAL = "partial";
export const NONE = "none";

/** The `grounded`/`weak` cutoff. ⚠ `weak` is a SIGNAL, not a refusal
 *  (Arpit 2026-09-22, W-214) — the label is published, nothing abstains on it. */
export const SEPARATION_FLOOR = 0.10;
/** `0.0` means the clause is OFF — a measured ruling, not an oversight. */
export const DOC_COVERAGE_FLOOR = 0.0;

function round4(x) { return Math.round(x * 1e4) / 1e4; }
function clamp01(x) { return Math.max(0.0, Math.min(1.0, x)); }

export class Confidence {
  constructor({
    coverage = 0.0, separation = 0.0, support = 0, verified = "unverified",
    missing = [], docCoverage = 1.0,
    separationFloor = SEPARATION_FLOOR, docCoverageFloor = DOC_COVERAGE_FLOOR,
  } = {}) {
    this.coverage = coverage;
    this.separation = separation;
    this.support = support;
    this.verified = verified;
    this.missing = missing;
    this.docCoverage = docCoverage;
    this.separationFloor = separationFloor;
    this.docCoverageFloor = docCoverageFloor;
  }

  /** `grounded` · `partial` · `weak` · `none` — **first true clause wins.**
   *
   * `stale` demotes to `partial` rather than `weak` because stale bytes are a
   * KNOWABLE defect a consumer can name, which is what `partial` means; `weak`
   * is where nothing is identifiably wrong and the ranking cannot choose. */
  get band() {
    if (this.support === 0) return NONE;
    if (this.missing.length || this.verified === "stale") return PARTIAL;
    // The clause the decoy control bought: corpus-wide coverage cannot see
    // that a question's terms are scattered across four documents while no
    // single one discusses it, and separation cannot either — a corpus of
    // near-misses is decisive about its best near-miss.
    if (this.docCoverage < this.docCoverageFloor) return PARTIAL;
    if (this.separation < this.separationFloor) return WEAK;
    return GROUNDED;
  }

  /** **A refusal, not a low number** — and since W-214 it refuses on one thing
   *  only: nothing scored at all. An agent handed `0.3` will use it anyway and
   *  hedge in prose; one handed `answerable: false` has nothing to hedge.
   *
   * 🔴 **`weak` STOPPED being a refusal on 2026-09-22 (Arpit, W-214)**,
   * reversing his own W-176 gate 1 ruling of 2026-09-14, under which this read
   * `band !== NONE && band !== WEAK`. W-213 measured, over 2 992 questions and
   * three independently authored sets, that **what the band withheld was more
   * likely RIGHT than what it answered** — `separation` does not carry
   * correctness, and no floor fixed it, including 0.00.
   *
   * **`weak` is still banded and still named in `failed`**, so a consumer that
   * wants the old behaviour implements it from the payload. ⚠ The cost, taken
   * knowingly: `band !== none` is structurally almost never false, so
   * `answerable: false` now fires essentially only on an empty result set. The
   * band table says *signal* rather than *do not answer*, so two fields on one
   * payload never again contradict each other. `partial` stays answerable for
   * the reason it always did: it is a NAMEABLE defect. */
  get answerable() { return this.band !== NONE; }

  /** The same signals with the refer plane's verdict filled in. `answer` ranks
   *  before it fetches, so the verdict does not exist when the rest are
   *  computed. A new object — `band` re-derives and cannot go stale. */
  withVerified(verdict) {
    return new Confidence({
      coverage: this.coverage, separation: this.separation, support: this.support,
      verified: verdict, missing: this.missing, docCoverage: this.docCoverage,
      separationFloor: this.separationFloor, docCoverageFloor: this.docCoverageFloor,
    });
  }

  /** The `--json` shape, declared in `output.schema.json#confidence`.
   *  `band` and `answerable` are written out rather than left derivable — a
   *  consumer re-implementing the band rules would be a second copy of this
   *  policy, in another language, drifting from the day it was written. */
  /** **Which gate fired, by name** — W-176's output surface, step 3.
   *
   * `no_candidates` is a refusal (`answerable: false`); 🔴 **`separation` is
   * NOT, since W-214** — it is still emitted and still means what it meant,
   * and a consumer that wants the old abstention reads this key and refuses on
   * it itself. **A cleanup that drops this branch because nothing refuses on
   * it any more would complete the wrong half of the ruling.**
   *
   * `[]` on `partial`, deliberately: its defect is already named in `missing`
   * or `verified: stale`. **The shape lands before the gates that fill it**,
   * so a consumer written today keeps working as each of W-176's eight
   * measured gates appends a name here. */
  get failed() {
    if (this.band === NONE) return ["no_candidates"];
    if (this.band === WEAK) return ["separation"];
    return [];
  }

  asDict() {
    return {
      band: this.band,
      answerable: this.answerable,
      // Always present, `[]` when no gate fired — an absent key could not be
      // told from a reader too old to have gates (W-48), which is the one
      // reading that would make a consumer answer where it should abstain.
      failed: this.failed,
      coverage: this.coverage,
      separation: this.separation,
      separation_floor: this.separationFloor,
      doc_coverage: this.docCoverage,
      doc_coverage_floor: this.docCoverageFloor,
      support: this.support,
      verified: this.verified,
      missing: [...this.missing],
    };
  }
}

/** Compute the block from what `rank()` already had in hand.
 *
 * `scores` is every score above zero, already sorted descending.
 * **`missing` reports the SURFACE form, never the analyzed one** — *"`mtl` is
 * not in this corpus"* is worse than silence; *"`mTLS` is"* is actionable.
 *
 * `support` is bounded by `--top` deliberately: a corpus-wide count would
 * differ between `--fast` and `--scan`, which is the differential-law break
 * the accelerator record exists to forbid. The law is worth more than the
 * better number. */
export function signals(
  pairs, queryHashes, df, n, scores,
  {
    verified = "unverified", topDocHashes = null,
    separationFloor = SEPARATION_FLOOR, docCoverageFloor = DOC_COVERAGE_FLOOR,
  } = {},
) {
  if (!queryHashes.length || n <= 0) {
    return new Confidence({ verified, separationFloor, docCoverageFloor });
  }

  // First token per hash, mirroring `queryTermHashes`' de-duplication so the
  // two lists cannot fall out of step on a repeated word.
  const first = new Map();
  for (const [surface, analyzed] of pairs) {
    const h = termHash(analyzed);
    if (!first.has(h)) first.set(h, surface);
  }

  let total = 0.0, matched = 0.0;
  const missing = [];
  for (const h of queryHashes) {
    const weight = idf(df[h] ?? 0, n);
    total += weight;
    if ((df[h] ?? 0) > 0) matched += weight;
    else missing.push(first.get(h) ?? h);
  }
  const coverage = total > 0 ? matched / total : 0.0;

  // The same idf weighting, over the TOP document's own terms rather than the
  // corpus's. Weighted, not counted: missing `the` is nothing, missing `mTLS`
  // is the question.
  let docCoverage;
  if (topDocHashes === null) docCoverage = 1.0;   // not supplied — never demote on absence
  else if (total > 0) {
    const present = new Set(topDocHashes);
    let s = 0.0;
    for (const h of queryHashes) if (present.has(h)) s += idf(df[h] ?? 0, n);
    docCoverage = s / total;
  } else docCoverage = 1.0;

  // One result separates perfectly: there is no runner-up to confuse it with.
  let separation;
  if (scores.length >= 2 && scores[0] > 0) separation = (scores[0] - scores[1]) / scores[0];
  else if (scores.length === 1) separation = 1.0;
  else separation = 0.0;

  return new Confidence({
    coverage: round4(clamp01(coverage)),
    docCoverage: round4(clamp01(docCoverage)),
    separation: round4(clamp01(separation)),
    support: scores.length,
    verified,
    missing,
    separationFloor,
    docCoverageFloor,
  });
}

export { tokenizePairs };
