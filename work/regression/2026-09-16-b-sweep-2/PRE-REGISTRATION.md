---
type: Pre-Registration
description: "W-144's lower `b` range, re-specified: `dump` is a CONTROL, not a benefit family. Benefit is `content` + `main`; controls are `inverse`, `placebo`, `verbose` and `dump`. Range 0.4 -> 0.3 -> 0.2 -> 0.15, descending, first-that-clears. The bar, the range and every other step are unchanged."
run: 2026-09-16-b-sweep-2
item: W-144
prediction: W-144-B-SWEEP-2
status: frozen
filed: 2026-09-16
---

# PRE-REGISTRATION — the lower `b` range, with `dump` reclassified

🔴 **FROZEN. Nothing below may be edited after the first number exists**
([SR-RS](../../../records/0133_predictions.md) decision 10b). **Committed
alone**, before the sweep runs, so the freeze is checkable in `git log`.

**It supersedes [the 2026-09-15 pre-registration](../2026-09-15-b-sweep/PRE-REGISTRATION.md)
in place. That file is not edited** — a frozen document is superseded, never
amended.

---

## 1 · What changed, and why it is not a moving threshold

**One thing changed: `dump` moves from the benefit families to the controls.**
Ruled by Arpit on 2026-09-16 as a **specification defect in the decision rule**.

The 2026-09-15 rule asked for a value *"netting positive on all three families —
`dump`, `content` and `main`"*. **`dump` sits at 30/30 at the baseline** and can
never net positive: its correct answer is the prose document, which already wins
at `b = 0.75`. The rule was unsatisfiable at any `b`, forever.

🔴 **The justification is `dump`'s ROLE, quoted from its own generator, and not
the fact that reclassifying it makes a value clear:**

> **`dump`** is the HARM case […] a data dump that names the term in a row and
> says nothing about it, against prose that discusses it. **The prose document
> is correct.** (b) collapses the dump's length; if it then wins, (b)
> over-promotes.
> — [`w144_graded.py`](../../../tools/quality-controls/w144_graded.py), written
> before any number existed

*Correct in both arms, and a treatment must not change that* is the definition of
a control. **`dump` was grouped with `content` and `main` because all three are
*table* families, and the rule inherited the grouping.**

⚠ **The reclassification would be correct if the sweep had never run.** That is
the test decision 10b implies and the reason this is legal.

## 2 · The decision rule — frozen

**Ship the FIRST value, in descending order `0.4 → 0.3 → 0.2 → 0.15`, that:**

1. **nets positive on `content` AND `main`**, each individually, neither
   negative; **and**
2. **every control holds** — `inverse`, `placebo`, **`verbose`** and **`dump`**;
   **and**
3. **the net clears [SR-RS](../../../records/0133_predictions.md) decision 19's
   floor** for the discordant count observed. **A net of 6 is the floor of all
   floors**, and nets of 1–5 cannot clear α at any count.

⚠ **Descending order is part of the rule, not a convenience.** `0.15` is a long
way from the literature's `0.75`, and a sweep reporting *the best value* would
pick the extreme whenever the curve is flat. **The first value that clears is the
smallest departure that works.**

🔴 **`dump` keeps its teeth.** W-155 showed option (b) drove it **30/30 → 0/30**;
catching exactly that is a control's job. **If a value clears `content` and
`main` while `dump` regresses, the run FAILS.** Moving it out of the benefit set
does not soften it — it stops asking a saturated family to improve.

**If no value clears with every control holding:** **stop and re-inbox**, with
the numbers. No second widening without a ruling.

## 3 · The families

| family | what it is | correct document | role |
|---|---|---|---|
| `main` | prose with a table appendix | the subject | **benefit** |
| `content` | a rate card whose subject IS its rows | the table-heavy one | **benefit** |
| `dump` | a data dump naming the term in rows and saying nothing about it | **the prose document, in both arms** | 🔴 **control** |
| `inverse` | `main` with the roles swapped | the prose-only one, in both arms | control |
| `placebo` | two prose-only documents, no table anywhere | the denser one | control |
| **`verbose`** | a concise brief (6 hits) against a report **3× as long with 7** | **the brief, in both arms** | control |

**30 probes per family, 180 total.**

## 4 · Headroom, declared before the numbers (decisions 22b, 22e, 22f)

Measured at the baseline `b = 0.75` by
[the control probe](../2026-09-16-b-sweep-2-control/report.md):

| family | hit@1 at baseline | regression headroom | improvement headroom |
|---|---|---:|---:|
| `main` | 0/30 | **0** | **30** |
| `content` | 0/30 | **0** | **30** |
| `dump` | 30/30 | **30** | **0** |
| `inverse` | 30/30 | **30** | **0** |
| `placebo` | 30/30 | **30** | **0** |
| **`verbose`** | 30/30 | **30** | **0** |

🔴 **Every family is saturated in one direction by construction, and that is the
design rather than a defect** (22e). A benefit family is built wrong at the
baseline or the lever has nothing to fix; a control is built right at it or it
cannot report. **22b's table is read per family.**

✅ **The control set now contains one family SHOWN to spend its headroom** —
`verbose` goes 30/30 → **0/30 at `b = 0`**, `p = 0.0000`. That is Arpit's
2026-09-15 condition, discharged before this was written, and it is what makes
the other controls' holding informative.

## 5 · Where it runs, and what each place may claim

| corpus | may it produce the verdict? |
|---|---|
| the **generated 180-probe corpus** in `fux-lab` | **yes** — it is the instrument the rule was written for |
| **fux's own docs tree** | **no** — reopen-trigger evidence only |

- **One lever moves.** `[bm25f] b`. `flen` is the **shipped** one in every arm —
  this sweep is not option (b) and does not exclude table tokens.
- **Per-probe rows** under `evidence/`, one per probe per arm (decision 22e).
- 🔴 **No answer key is read.** The corpus is generated; nothing from
  `work/golden/` enters it ([L11](../../../records/0012_LAW-11-sealed-answer-key.md)).

## 6 · Classification

**`informed`.** The corpus is generated by this project's own tool and the
reader of the results authored the `verbose` family. **An informed run is
reclassified, not banned** — filed, cited, and never compared with a blind run.

⚠ **This corpus is NOT the one the 2026-09-15 sweep ran on.** Adding 30 terms for
`verbose` moves every probe term's `df` (now 2–12), so `main`, `dump` and
`content` numbers here are a **replication**, not a continuation, and may not be
diffed against that run's.

## 7 · What this run does NOT do

- **It does not ship a default.** On a clear, step 4 of the item's order does —
  amend SR-TUNING and SR-RANKING in the same change, L3 check, two-reader byte
  equality, CHANGELOG. **The amendment is Arpit's.**
- **It does not test option (b).** Excluding table tokens from `flen` is a
  different mechanism and W-155 showed it destroys `dump`.
- **It does not widen the range.** `0.4 → 0.15`, and no value below it.
