---
type: Analysis
description: "W-256 section 2 - how to read an INCONCLUSIVE that is close to a FAIL: the one floor that satisfies the point criteria does so by 3 correct answers on a base of 212, from 21 reachable unanswerables, and the AUC is 0.60. What it licenses, what it does not, and the next measurement."
run: 2026-10-04-doc-coverage-replay
item: W-256
classification: informed
filed: 2026-10-04
---

# ANALYSIS - a floor that is right by three answers

## What the number says

`doc_coverage` has a **weak** separating signal and not none: AUC 0.60, so a
random unanswerable has a lower `doc_coverage` than a random answerable 60 % of
the time. That is above the coin, and the floors show the same thing as a
trade: raising the floor buys catch (0 -> 0.81) and costs correct answers
(0 -> 102 of 212) at roughly the rate a coin would. Along the whole grid the
demoted-correct count sits **within 7 of the coin's expectation** and never
beyond a p of 0.10 in either direction. The gate is a rate-matched coin with a
slight lean, which is the same shape W-213 found for `separation`.

## Why 0.80 is not a finding

- It passes by **3 answers of 212 correct** (61 against 64.1), a gap well inside
  binomial noise: p = 0.35.
- The catch rate of 0.571 is **12 of 21** - one row either way is 0.524 or 0.619,
  so the 50 % bar is crossed by roughly one question.
- It fails two of the three sets. Set-3 contributes **3** reachable
  unanswerables, so the per-set criterion is close to unmeasurable there; this
  is what the per-set clause was written to catch, and it did.
- Eight floors were tried; the Bonferroni level exists because one of eight
  nearing the bar is expected.

## What this does and does not license

- **Licenses:** nothing to move. `doc_coverage_floor` stays `0.0`; SR-CONFIDENCE
  decision 12's *off* is not contradicted. The result does not say the gate
  can never work - it says this data cannot show that it does.
- **Does not license:** reading INCONCLUSIVE as FAIL, or 0.80 as a candidate
  value. The frozen rule sends this to Arpit, and no record sentence beyond a
  pointer is written.
- **Not a decoy test.** The 36 unanswerables are the retired key's, authored
  for the benchmark; decision 12's original decoys were a different construct.

## Binding limits

One corpus (generated rung-01000), three question sets, two of them authored by
the model family that tunes the engine (`informed`); `correct` is a substring
proxy; the headroom is 21 rows. A larger reachable-unanswerable population would
move this from INCONCLUSIVE to a decided result either way - that is the real
cost of the question, not the threshold.

## What would settle it

More unanswerables reaching the clause: the next sealed generation's
`unanswerable` class at rung-01000 and rung-10000 (the other seven W-213 rungs
repeat the same questions and are correlated, so they would not help). Gates 3
and 4 (the u017 pair, replayable on `answer_text`) are a successor item as the
item says.

Reproduce: `.venv/bin/python tools/quality-controls/doc_coverage_replay.py
--evidence work/regression/2026-09-22-band-operating-point/evidence --out
<dir>`.
