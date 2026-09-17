---
type: Verdict
run: 2026-09-16-b-sweep-2
item: W-144
name: "Does a lower `b` rank better, and which value is the smallest that does?"
prediction: W-144-B-SWEEP-2
pre_registration: work/regression/2026-09-16-b-sweep-2/PRE-REGISTRATION.md
classification: informed
verdict: PASS
ruling: "`b = 0.15` is the first value in the frozen descending order that nets positive on both benefit families — `content` +30 and `main` +30, each p = 0.0000 on 30 discordant pairs against a required net of 12 — with all four controls holding at +0: `inverse`, `placebo`, `verbose` and `dump`. `0.4`, `0.3` and `0.2` do not clear, because `main` nets +0 at each. The control set contains one family proven able to lose (`verbose`, 30/30 to 0/30 at b = 0), so the controls' holding is informative rather than vacuous."
filed: 2026-09-16
---

# VERDICT — PASS at `b = 0.15`, and not before

**Ruled against** [the pre-registration](PRE-REGISTRATION.md), frozen and
committed alone before the sweep ran.

## The rule, applied in order

> the FIRST value, descending `0.4 → 0.3 → 0.2 → 0.15`, that nets positive on
> **`content` AND `main`**, each individually and neither negative, with **every
> control holding** — `inverse`, `placebo`, `verbose` and `dump` — and the net
> clearing decision 19's floor.

| `b` | `content` | `main` | `inverse` | `placebo` | `dump` | `verbose` | clears? |
|---|---:|---:|---:|---:|---:|---:|---|
| 0.4 | +0 | +0 | +0 | +0 | +0 | +0 | **no** — neither benefit family moves |
| 0.3 | **+30** | +0 | +0 | +0 | +0 | +0 | **no** — `main` does not net positive |
| 0.2 | **+30** | +0 | +0 | +0 | +0 | +0 | **no** — same reason |
| **0.15** | **+30** | **+30** | +0 | +0 | +0 | +0 | ✅ **YES** |

**At `b = 0.15`**, both benefit families: `b = 30, c = 0`, discordant 30,
**net 30**, `p = 0.0000`, against a **required net of 12** at that count.

**All four controls hold at +0**, including `dump`.

🔴 **Descending order is what makes this `0.15` and not a lower number.** The
sweep does not report the best value; it reports the **smallest departure from
the literature's `0.75` that works**, and it stops there.

## Why the controls' holding is informative here and was not before

**`inverse` and `placebo` are saturated 30/30 in every arm at every value** — they
have never moved, so *"nothing regressed"* on them is consistent with safety and
is not evidence of it. That is Arpit's own reason for demanding a fourth control.

✅ **`verbose` is proven able to lose.** [The control probe](../2026-09-16-b-sweep-2-control/report.md)
put it at **30/30 across this whole range and 0/30 at `b = 0`**, `p = 0.0000`.
**So its `+0` at `0.15` is a measurement, not a tautology** — and without it,
`b = 0` and `b = 0.15` are indistinguishable on every other instrument in the set.

✅ **`dump` keeps its teeth as a control.** W-155 showed option (b) drove it
**30/30 → 0/30**. It holds here, which is the specific harm this sweep had to
rule out and did.

## What the reclassification did and did not do

**`dump` moved from the benefit set to the control set on 2026-09-16**, ruled a
**specification defect** rather than a threshold change: it is 30/30 at the
baseline and can never net positive, so the old rule was unsatisfiable at any
`b`. **The justification is its role, quoted from its own generator before any
number existed**, and the reclassification would be correct if the sweep had
never run.

⚠ **It did not lower the bar.** `dump` is still required to hold, and the same
decision 19 floor applies to the same two benefit families. **What changed is
that a saturated family is no longer asked to improve.**

## What this PASS authorises, and what it does not

**It authorises step 4 of [W-144](../../open/W-144-structure-aware-extraction.md)'s
order**, which Arpit's ruling left unchanged: ship `0.15` as the `[bm25f] b`
default, amend SR-TUNING and SR-RANKING in the same change, L3 check, two-reader
byte equality, and a CHANGELOG line.

🔴 **It does not transfer.** The corpus is **generated and synthetic**, 510
documents built by this project's own tool, and the run is `informed`. It says a
lower `b` ranks better **on documents shaped like these** — prose with table
appendices, rate cards whose subject is their rows, and data dumps.

⚠ **`0.15` is a long way from the literature's `0.75`**, and that discomfort is
what the descending order and the fourth control were built for. Neither was
optional and neither was skipped.

⚠ **Not comparable with [the 2026-09-15 sweep](../2026-09-15-b-sweep/VERDICT.md).**
Adding 30 terms for `verbose` moved every probe term's `df`, so `main`, `dump`
and `content` here are a **replication on a different corpus**, not a
continuation.
