---
type: Verdict
run: 2026-09-15-b-sweep
item: W-144
name: "Does lowering `b` fix what a table-inflated `flen` breaks?"
prediction: W-144-B-SWEEP
pre_registration: work/regression/2026-09-15-b-sweep/PRE-REGISTRATION.md
classification: informed
verdict: FAIL
ruling: "No pre-registered value clears: 0.6, 0.5 and 0.4 leave all five families exactly where 0.75 does, zero discordant pairs. The pre-registration's own fallback fires. ⚠ The lever is NOT inert — a mechanism probe outside the arms shows `content` flipping at b <= 0.3 and `main` at b <= 0.15, with nothing regressing anywhere down to b = 0 — so whether to pre-register a lower range is a decision for Arpit and is NOT taken here."
filed: 2026-09-15
---

# VERDICT — no pre-registered value clears

**Ruled against** [the pre-registration](PRE-REGISTRATION.md), frozen 2026-09-15
before any number existed.

> **The rule:** ship the FIRST value, in descending order `0.6 → 0.5 → 0.4`,
> that nets positive on `dump`, `content` **and** `main`, with `inverse` moving
> the other way and `placebo` not moving, and the net clearing SR-RS decision
> 19's floor.

| value | families netting positive | verdict |
|---|---|---|
| `0.6` | **none** — 0 discordant on all five | does not clear |
| `0.5` | **none** — 0 discordant on all five | does not clear |
| `0.4` | **none** — 0 discordant on all five | does not clear |

**`FAIL`.** No value clears, so nothing ships, and `b` stays at **0.75**.

## What fires next, by the pre-registration's own words

> *"If no value clears: fall back to **(b) plus an idf guard** — a document whose
> only match is a row label may not win on length alone — under its own
> pre-registration, at this same bar. **That is a separate run**, not a
> continuation of this one."*

## 🔴 What this verdict must NOT be read as

**It is not "`b` cannot fix this".** A mechanism probe — explicitly outside the
arms, run because SR-RS decision 22c requires an endpoint to be shown capable of
moving — locates two crossovers **below the frozen floor**:

| family | flips between |
|---|---|
| `content` (the table IS the answer) | **0.4 and 0.3** |
| `main` (prose with a table appendix) | **0.2 and 0.15** |

and **nothing regresses at any value, down to `b = 0`** — including `dump`, the
family whose destruction is why option (b) was ruled out.

**So the frozen range was set above where the effect is.** That is a fact about
the pre-registration, discovered by running it, and it is exactly the shape the
descending rule was written to guard against from the other direction — *"a
sweep that reported the best value would pick the extreme whenever the curve is
flat"*.

🔴 **Widening the range is a NEW pre-registration and Arpit's call**, not this
run's. Picking `0.15` because the probe found it would be the moving-threshold
failure the rule exists to prevent — and `0.15` is a very long way from the
literature's `0.75`, which is precisely why the guard is there.

## What it costs to be wrong in either direction

| | |
|---|---|
| **take the fallback as written** | option (b) + an idf guard, a new pre-registration, and W-155's `dump` problem to solve again — the thing lowering `b` demonstrably does **not** have |
| **pre-register a lower range** | cheap to run (the arm exists), and ⚠ **both controls are saturated in this corpus**, so a regression it would cause may be invisible here. A lower range needs a control with regression headroom before it means anything |

Both are stated so the ruling is between two named options.

## Reproduce

```console
$ python tools/quality-controls/w144_graded.py gen --dest <dir>
$ python tools/quality-controls/w144_graded.py bsweep --corpus <dir>
```
