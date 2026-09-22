/** The confidence twin — run with `node --test node/test/`.
 *
 * `confidence.mjs` is a twin of `confidence.py`, and until 2026-09-22 nothing
 * under `node/test/` touched it at all: the only thing holding the two halves
 * together was the differential arm, which needs a corpus that exercises the
 * branch. **A near-tie is exactly the branch a small corpus misses**, so the
 * band rule could have drifted between the planes for as long as it took
 * somebody to notice a `weak` in one reader and a `grounded` in the other.
 *
 * Added with [W-214](../../work/open/W-214-separation-does-not-carry-correctness.md)
 * because that ruling moved one expression on each side, and a ruling applied
 * to one plane only is the failure this file exists to make loud.
 *
 * Owned, with its twin, by [SR-CONFIDENCE](../../records/0141_confidence.md).
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { Confidence, GROUNDED, NONE, PARTIAL, WEAK } from "../src/query/confidence.mjs";

/** A block with everything healthy except what the caller overrides. */
const block = (over = {}) => new Confidence({
  coverage: 1.0, separation: 0.5, support: 3, verified: "unverified",
  missing: [], docCoverage: 1.0, ...over,
});

test("the band is first-true-wins, in the same order as Python", () => {
  assert.equal(block({ support: 0 }).band, NONE);
  assert.equal(block({ missing: ["mTLS"] }).band, PARTIAL);
  assert.equal(block({ verified: "stale" }).band, PARTIAL);
  assert.equal(block({ separation: 0.05 }).band, WEAK);
  assert.equal(block().band, GROUNDED);

  // Absence beats ambiguity: both true, and `partial` is the one reported,
  // because a nameable defect is more useful than an unnameable one.
  assert.equal(block({ missing: ["mTLS"], separation: 0.0 }).band, PARTIAL);
});

test("W-214 — `weak` is a signal, so only `none` refuses", () => {
  // Arpit, 2026-09-22, reversing his own W-176 gate 1 ruling: across 2 992
  // questions the answers the band withheld were more likely RIGHT than the
  // ones it let through. This assertion read `false` for eight days.
  assert.equal(block({ separation: 0.05 }).answerable, true);
  assert.equal(block({ support: 0 }).answerable, false);
  assert.equal(block({ missing: ["mTLS"] }).answerable, true);
  assert.equal(block().answerable, true);
});

test("W-214 — and the `weak` SIGNAL is still emitted, which is the other half", () => {
  // *Keep the signal, drop the refusal* is not *drop both*. Once nothing
  // branches on it, the `WEAK` arm looks like dead code to anyone reading the
  // expression without the date.
  const weak = block({ separation: 0.05, separationFloor: 0.10 });
  assert.equal(weak.band, WEAK);
  assert.deepEqual(weak.failed, ["separation"]);

  const payload = weak.asDict();
  assert.equal(payload.band, WEAK);
  assert.equal(payload.answerable, true);
  assert.deepEqual(payload.failed, ["separation"]);
  assert.equal(payload.separation_floor, 0.10, "the floor it was judged under");
});

test("a named gate may fire without refusing, and `no_candidates` still does", () => {
  assert.deepEqual(block({ support: 0 }).failed, ["no_candidates"]);
  assert.deepEqual(block({ missing: ["mTLS"] }).failed, [], "partial is not a gate");
  assert.deepEqual(block().failed, []);
});

test("the floor arrives from the CALLER, and the band carries the one it used", () => {
  // A `grounded` judged at 0.02 is not the same claim as one judged at 0.10,
  // and without the published floor the difference would be invisible.
  const slack = block({ separation: 0.05, separationFloor: 0.01 });
  assert.equal(slack.band, GROUNDED);
  assert.equal(slack.asDict().separation_floor, 0.01);
  assert.equal(slack.separation, 0.05, "the SIGNAL is untouched; only the verdict moved");
});

test("withVerified re-derives the band rather than carrying a stale one", () => {
  const grounded = block();
  assert.equal(grounded.band, GROUNDED);
  assert.equal(grounded.withVerified("stale").band, PARTIAL);
  assert.equal(grounded.withVerified("current").band, GROUNDED);
  assert.equal(grounded.band, GROUNDED, "the original is untouched — it is a new object");
});
