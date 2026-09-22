---
type: Verdict
name: W-213-BAND-OPERATING-POINT
description: "W-213 — KEEP `separation_floor = 0.10`. No candidate floor clears the SR-RS d19 paired bar in all three sets at the primary rung, which is outcome 2 of the frozen pre-registration and a PASS of it. The reason no floor wins is the finding: the separation signal does not carry correctness information at any operating point on this corpus."
verdict: PASS
prediction: W-213-BAND-OPERATING-POINT
pre_registration: work/regression/2026-09-22-band-operating-point/PRE-REGISTRATION.md
run: 2026-09-22-band-operating-point
item: W-213
filed: 2026-09-22
classification: informed
---

# VERDICT — `separation_floor` STAYS `0.10`

**Ruled against** [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md), frozen at
`4cdf0dfd` before any number existed. **Evidence:** [`report.md`](report.md).

## The ruling

**Outcome 2 of the three the pre-registration fixed: KEEP `0.10`.**

> *"🔴 **KEEP `0.10`** — no candidate clears in all three sets. **This is a PASS
> of this pre-registration, not a failure to find something.** A recorded
> negative that stops a threshold being moved is the outcome
> [SR-RS](../../../records/0133_predictions.md) decision 10b exists to
> protect."*

At the primary rung `rung-01000`, across the six candidate floors and three
sets — **eighteen comparisons — not one clears in the improving direction.**
Three clear, and all three say the **incumbent is better**: `0.20` on set-1
(net −13, `p = 0.0146`), `0.30` on set-1 (net −24, `p = 0.0003`) and `0.30` on
set-3 (net −14, `p = 0.0243`).

**Nothing in the engine changes. `SEPARATION_FLOOR` stays `0.10`, no test is
edited, and no `tune.toml` default moves.**

⚠ **The run was not underpowered.** Improvement headroom was **49 / 64 / 65**
questions against a floor of 6 flips. A win was reachable in every set and none
appeared.

## Why no floor wins, which is the part worth keeping

🔴 **The threshold is not in the wrong place. The quantity it thresholds does
not carry the information it is being asked for.**

- **Risk RISES with the floor on all three sets** — set-1 `0.333 → 0.394`,
  set-2 `0.502 → 0.534`, set-3 `0.461 → 0.600` as coverage falls from 1.00 to
  ~0.47. A working abstention gate makes risk **fall**.
- **At the shipped floor the band withheld fewer wrong answers than a coin
  withholding at the band's own rate would have, in all three sets** — 62 vs
  63.6, 135 vs 144.6, 104 vs 124.5 (`p = 0.878`, `0.263`, **`0.0123`**).
- **The questions it withheld were more likely to be RIGHT than the ones it
  answered** — risk 0.325 vs 0.335, 0.469 vs 0.516, 0.385 vs 0.489 — and
  removing the unanswerable class, which can only flatter the gate, widens every
  gap.

🔴 **What is supported, stated at its real strength:** *there is no evidence the
band's abstention is better than chance at this operating point, and its point
estimate is on the wrong side of chance in all three sets and both slices.*
**It is NOT supported that the band is worse than random** — three sets agreeing
in direction is `p = 0.25` on a sign test, and only set-3 is individually
distinguishable.

## What this verdict does NOT do

- 🔴 **It does not turn the band off.** `0.00` — the clause off — was in the grid
  and **did not clear either** (net +8 / 0 / +8, `p = 0.15 / 1.00 / 0.24`). The
  pre-registration permits exactly one adoption path and `0.00` did not take it.
- 🔴 **It does not reverse W-176 gate 1.** *"`weak` IS a refusal"* is **Arpit's
  ruling of 2026-09-14**, and a measurement is not a licence to undo one. What
  the measurement does is put a number where the ruling's premise was — *ten
  wrong links produce a confident wrong answer* — and the number does not
  support the premise on this corpus. **That goes to him.** Filed as **W-214**.
- **It does not price the judged series.** The endpoint's `correct` is the named
  proxy `evidence_quoted`, and the one assumption Result 2 rests on — that the
  proxy under-detects correctness *equally on both sides of the gate* — is
  unmeasured and is what a judged arm should check first.

## Classification

🔴 **`informed`, permanently**, three independent ways: L11 decision 14, two
Claude-authored sets, and retired data read in full by the session that
measured it. **Not a generalisation estimate**; not comparable with a blind run.
Sufficient to decide that a threshold does not move, which is what it was asked.
