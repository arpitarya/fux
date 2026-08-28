---
type: Analysis
title: A signal worth publishing is not automatically a threshold worth setting
description: doc_coverage ships and reports; the gate is held because the populations overlap. The general lesson is that finding a real case does not tell you how often it happens.
timestamp: 2026-08-28T00:00:00Z
---

# Analysis — `doc_coverage`

## 1 · A real case is not a rate

The decoy control found a genuine defect: a question no document answers,
reported `grounded`. **That finding was correct and it was also unquantified.**
Measuring it produced two facts the original write-up could not have:

- **Fourteen of fifteen decoys never reach the clause.** They are `partial` via
  `missing` — the corpus-wide signal doing its job. The scattered-terms case is
  **one in fifteen**, not a general failure of the band.
- **The one that reaches it is not extreme.** At `0.710` it sits comfortably
  inside the real goldens' `0.401–1.000`, so it is not separable from a correct
  answer by this signal.

⚠ **The lesson is the shape, not the number:** *"we found a case"* answers
whether a defect exists and says nothing about whether a threshold can catch it.
**Those are different questions and the second one needs its own measurement.**

## 2 · Why no floor was picked

The obvious floor is `1.0` — *every term the corpus has, the cited document has
too* — and it reads structural rather than tuned, which is exactly why it was
tempting. **It costs 19 of 50 correct answers**, demoted to `partial`.

Anything lower is a number chosen from a table of 65 queries with no gap in it.
**That is R10's failure in a different costume**, and R10 is `INCONCLUSIVE` on
this repository right now for precisely that reason.

**Repro:** `evidence/separate.py`.

## 3 · What shipping the signal buys anyway

**A consumer can now see the case even though fux does not act on it.**
`doc_coverage: 0.42` beside `band: grounded` is actionable by an agent that
cares; before, the information did not exist at any layer.

**And it cost nothing to add.** `coverage` is unchanged, so no consumer's reading
of it moved; `rank()` gained one line into a dict it already fills; **both
scoring paths derive it from the same record**, so the differential law is
untouched by construction rather than by test.

## 4 · The specific improvement, if someone wants the gate

1. **Grow the decoy set** until the two distributions can be *estimated* rather
   than sampled. One decoy reaching the clause is not a distribution.
2. **Pre-register the floor** before any score exists under it — ADR-RS decision
   1, and the discipline R10 is currently paying for the absence of.
3. ⚠ **Consider that `doc_coverage` may be the wrong instrument.** The decoy's
   distinguishing property is not *how much* of the question the top document
   holds, but that **no single document holds a coherent subset** — every term
   present, spread across four files. A measure of *concentration* across the
   candidate set might separate where a per-document fraction cannot. **Named as
   a direction, not proposed as a design.**

## 5 · Unresolved

- **Whether to gate at all.** Arpit's; the ruling said gate, the measurement says
  the obvious gate is expensive, and he has not seen the measurement.
- **R10 is untouched by this.** The `0.58` decoy is still above the `0.5` R10
  would pick, and `doc_coverage` does not change `separation`.
