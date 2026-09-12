---
type: Verdict
description: "The heading-matched distractor control is RETIRED. Its endpoint sits at the corpus base rate under every setting of both bm25f.heading and bm25f.body, so it measures corpus composition rather than ranking and cannot discharge anything."
item: W-142
prediction: C4 (the `heading` negative control)
run: 2026-09-12-reaim-and-instruments
pre_registration: work/regression/2026-09-12-reaim-and-instruments/PRE-REGISTRATION.md
classification: informed
name: "the heading-matched distractor control — is body similarity the mechanism?"
verdict: FAIL
ruling: "FAIL, and the retire follows from it — body similarity is NOT the mechanism either, and neither is heading matching — the endpoint sits at the corpus base rate under every setting of both fields, so it measures composition rather than ranking and cannot discharge anything"
filed: 2026-09-12
---

# Verdict — W-142: retire the control

## The question, and the bar

The pre-registration asked: the heading rebuild found `bm25f.heading` 3.0 → 0.0
moves the heading-matched distractor count by a net of 5 over 124 queries, below
the floor. **Is body similarity the mechanism instead?**

**The bar, frozen:** the exact two-sided binomial p-value on the discordant
pairs clearing α = 0.05, between `bm25f.body` 1.0 and 0.0. And:
*"whichever way the number falls, the item closes."*

## The measurement

`rung-01000`, 124 released questions, k = 5, no answer key read.

| `bm25f.body` | siblings in top-5 | **per query** | seed hits |
|---:|---:|---:|---:|
| 1.0 (shipped) | 256 | 2.06 | 272 |
| 0.5 | 259 | 2.09 | 274 |
| 0.25 | 261 | 2.10 | 281 |
| 0.0 (off) | 262 | 2.11 | **158** |
| **base rate** | — | **1.96** | — |

`b = 42`, `c = 41`, **discordant 83, net 1, p = 1.0000.** The bar at 83
discordant pairs is a net of 19.

## The verdict: **RETIRE**

**Not re-aim again.** 392 of 1 001 documents are `ext/sibling/`, so a top-5
drawn at random holds **1.96** of them. Every arm of both fields observes
**2.06–2.14**. The endpoint has never left its base rate and no field weight
moves it.

**The count is measuring corpus composition, not ranking.** A third field would
reproduce this.

⚠ **The arm is not broken — the endpoint is.** Seed hits fall 272 → 158 and five
queries return nothing when `body` goes to 0.0, so the weight is genuinely being
applied.

## What follows, and it is stated rather than deferred

1. 🔴 **C1 and C3 rest on generator assertions, and have since 2026-08-28.**
   No live control backs them. This is recorded in
   [ADR-RS](../../../docs/adr/0133_predictions.md) rather than left as a pending
   item, because the item that was going to resolve it cannot.
2. **A future distractor control must state its base rate before its arms.**
   `body_control.py` computes and prints it first, so the next one cannot repeat
   this. That is the mechanical part of the lesson.
3. **`heading_control.py` and `body_control.py` are both kept.** They are the
   evidence for this verdict; neither is run again for C4's purpose.

## What this verdict does not say

- It does **not** say `bm25f.heading` or `bm25f.body` are useless. Both
  demonstrably move results — 37 and 83 queries respectively. It says neither
  moves **this endpoint**.
- It does **not** re-judge C4 itself. Nothing supersedes a measurement except a
  better measurement;
  [C4's verdict](../2026-08-28-benchmark-contested/VERDICT-C4.md) stands as
  filed, and this is the record of what it could never have discharged.
- It does **not** propose a replacement control. Building one is not owed by
  this item and nothing in the queue is blocked on it.

## Reference

- [`report.md`](report.md) §1 · [`evidence/body-control-rung-01000.jsonl`](evidence/) — 496 per-query rows
- [`evidence/body-control-rung-01000.txt`](evidence/) — the run as printed
- The prior arm: [the priors run](../2026-09-12-priors-and-tables/report.md) §2, 372 rows
- [ADR-RS](../../../docs/adr/0133_predictions.md) decisions 19, 22c
