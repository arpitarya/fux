---
type: Verdict
name: VERDICT-R10-SEPARATION-FLOOR
prediction: R10
pre_registration: work/regression/2026-08-27-r10-separation-floor/evidence/PRE-REGISTRATION.md
verdict: INCONCLUSIVE
description: "Two rules frozen in the same pre-registration give two different answers on this data. Handed to Arpit, not adjudicated."
timestamp: 2026-08-27T17:05:00Z
---

# R10 — INCONCLUSIVE, and the reason is the pre-registration itself

**Prediction:** R10, the `SEPARATION_FLOOR`.
**Ruled against:**
[`evidence/PRE-REGISTRATION.md`](evidence/PRE-REGISTRATION.md), frozen
2026-08-27, **unedited**.

## The ruling

**`INCONCLUSIVE`. `SEPARATION_FLOOR` does not move; it stays `0.10`.**

Three of the four frozen outcomes changed nothing, and the pre-registration said
in advance that *"the most likely honest answer on 50 queries is not yet."* It
was right, though not for the reason it expected.

## Why it is not `PASS` and not `FAIL`

The curve reaches `t = 0.75` at `separation 0.3`, **falls back to 0.60 at
`0.4`**, then rises to 1.00. Two frozen rules read that differently:

- **§The measurement** defines the floor as the lowest bin reaching `t` **and
  staying at or above it for every higher bin** → **`0.5`** (outcome **A**).
- **§Frozen verdict rules row 4** says a crossing that is **non-monotone** is
  *"too noisy to read → no change"* (outcome **D**).

**Both fit.** `CLAUDE.md` §A pre-registered threshold may never move is explicit
about what to do here: *"If a result lands between 'clearly passes' and 'clearly
fails', write it up as ambiguous and hand it to Arpit. Do not adjudicate it, and
do not restate the threshold in looser words."* **This verdict does not pick,
and no session may pick without Arpit.**

⚠ **Picking `0.5` would be the moving-threshold failure in its most natural
costume** — it is a defensible reading of a frozen sentence, it produces a
usable number, and it quietly discards the row that says not to.

## What is true whichever way it is ruled

**The data cannot support a shipped constant.** Bins at or above `0.5` hold
**six queries in total**; the bin that first reaches `t` holds **four**, where
one query flipping moves it to `0.50` or `1.00`; the top two bins are **empty**.
The pre-registration's own power section conceded ±0.2 at best, and this is
worse at the top of the range.

**And it was never going to ship one.** The pre-registration: *"a crossing
yields a recommendation plus the named blocker, not a shipped constant"* — 50
queries over 10 documents is three orders of magnitude below the 10 000-document
design point.

## What this verdict does NOT claim

- **Not that the signal is useless.** `P(correct)` does rise across the range,
  from 0.44 in the lowest bin to 1.00 in the highest occupied ones. The curve is
  the wrong shape to read a boundary off, which is a different statement.
- **Not that the floor `0.10` is correct.** Nothing here validates it; it stays
  because nothing displaced it.
- **Not calibrated, anywhere.** `separation` is ordinal. The pre-registration
  fixed this wording in advance precisely so a later session could not upgrade
  it, and it is honoured.
- ⚠ **Not a delta.** This run is `informed` and states no comparison.

## What Arpit is being asked

**One question:** on a curve that crosses `t`, falls back one bin, then rises —
does §The measurement's "stays at or above it" clause govern (floor `0.5`), or
does row 4's non-monotone rule (no change)?

**Either answer is a new pre-registration for the next run, not an edit to this
one.** The contradiction is recorded in
[ADR-RS](../../../docs/adr/0036_predictions.md), which is where a correction to
a frozen document lives (W-82 ruling 8).
