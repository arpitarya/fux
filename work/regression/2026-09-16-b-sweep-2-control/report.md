---
type: Regression Run
name: b-sweep-2-control
description: "Arpit's condition on ruling (b), discharged: a control family with regression headroom exists, and it is proven to lose. `verbose` holds 30/30 at every value in the ruled range and breaks to 0/30 at b = 0. It also finds that the ruled decision rule is unsatisfiable as written — `dump` is saturated at baseline and cannot net positive."
run: 2026-09-16-b-sweep-2-control
item: W-144
classification: informed
status: complete
timestamp: 2026-09-16T00:00:00Z
---

# The control that can lose — built, and proven to lose

**Arpit ruled option (b) on 2026-09-15 with one condition:**

> the run does not start until the arm set carries a control family with
> regression headroom. Both existing controls (`inverse`, `placebo`) are
> saturated 30/30 in every arm, so *"nothing regresses"* on the probe is
> consistent with safety and is not evidence of it.

**This discharges that condition and nothing else.** It is a **mechanism probe**
([SR-RS](../../../records/0133_predictions.md) decision 22c) outside any arm: it
asks whether the new control *can* fire, not what `b` should be. **No
pre-registration is frozen here and no value is recommended.**

**Reproduce:**

```bash
.venv/bin/python tools/quality-controls/w144_graded.py gen --dest /tmp/w144corpus
.venv/bin/python tools/quality-controls/w144_graded.py bsweep --corpus /tmp/w144corpus \
    --values 0.75 0.4 0.3 0.2 0.15 0.0
```

---

## The new family

**`verbose`** — two prose-only documents, no table anywhere:

| | prose | occurrences of the term | |
|---|---|---|---|
| **concise** (`-brief.md`) | `P` | **6** | **correct in both arms** |
| **verbose** (`-report.md`) | **3 × `P`** | **7** | the rival |

🔴 **The rival gets MORE occurrences, and that is the design rather than an
oversight.** With equal `tf` the two would merely **tie** as `b → 0`, and a tie
is not a regression anybody can read off a hit count. At 7 against 6 the verbose
document **wins outright** once length normalisation stops paying for its length
— so the control fires as a **flip**, and *which value it fires at* is a number.

**It is aimed at exactly what lowering `b` does.** `b` is the strength of length
normalisation; at `0.75` a document is penalised for saying the same thing at
greater length, at `0` it is not penalised at all.

## The result — it holds, then it breaks

| family | `b=0.75` | `0.4` | `0.3` | `0.2` | `0.15` | `0.0` |
|---|---|---|---|---|---|---|
| `main` | 0/30 | +0 | +0 | +0 | **+30** | **+30** |
| `content` | 0/30 | +0 | **+30** | **+30** | **+30** | **+30** |
| `dump` | **30/30** | +0 | +0 | +0 | +0 | +0 |
| `inverse` | **30/30** | +0 | +0 | +0 | +0 | +0 |
| `placebo` | **30/30** | +0 | +0 | +0 | +0 | +0 |
| **`verbose`** | **30/30** | +0 | +0 | +0 | +0 | 🔴 **−30** |

*(baseline column is hit@1; the rest are paired nets against `b = 0.75`.)*

✅ **The condition is discharged.** `verbose` is **not saturated in the way that
matters**: it holds at every value in the ruled range `{0.4, 0.3, 0.2, 0.15}` and
**goes to 0/30 at `b = 0`**, `p = 0.0000` on 30 discordant pairs. A control that
can lose, that did lose, and whose losing is legible.

### Headroom, both directions, per family (SR-RS decision 22b)

Measured at the baseline `b = 0.75`, which is the arm every other value is paired
against:

| family | hit@1 at baseline | **regression headroom** (right at baseline — something to break) | **improvement headroom** (wrong at baseline — somewhere to go) |
|---|---|---:|---:|
| `main` | 0/30 | **0** | **30** |
| `content` | 0/30 | **0** | **30** |
| `dump` | 30/30 | **30** | **0** |
| `inverse` | 30/30 | **30** | **0** |
| `placebo` | 30/30 | **30** | **0** |
| **`verbose`** | 30/30 | **30** | **0** |

🔴 **Every family is saturated in one direction, and that is by construction
rather than by accident.** A *benefit* family (`main`, `content`) is built to be
wrong at the baseline — otherwise there is nothing for the lever to fix — and a
*control* (`dump`, `inverse`, `placebo`, `verbose`) is built to be right at it,
or it cannot report a regression. **Reading either column as a defect would be
reading the design as a fault.**

⚠ **What the condition was about is the CONTROL column**, and `verbose` is the
first entry in it that has been shown to spend its headroom: 30 at risk, 30 lost
at `b = 0`. `inverse` and `placebo` carry 30 apiece and have never moved at any
value, which is precisely why *"nothing regresses"* on them was not evidence.

🔴 **And it earns its keep immediately.** Without it, `b = 0` looks exactly as
safe as `b = 0.15`: `main` and `content` both net **+30** at both values, and
`dump`, `inverse` and `placebo` hold at both. **The only instrument in the arm
set that distinguishes them is the family that did not exist yesterday.**

## The crossovers survived the corpus change

Arpit's ruling names them from the 2026-09-15 probe: `content` between 0.4 and
0.3, `main` between 0.2 and 0.15. **Both replicate exactly here** — and that is
not a given, because adding 30 terms moves every probe term's `df` (now 2–12),
so this is a **different corpus** from the one that sweep ran on. The generator
says so, and the ruling already required a separate run.

## 🔴 What this found that nobody was looking for

**The ruled decision rule cannot be satisfied as written.** Arpit's ruling and
[the frozen 2026-09-15 pre-registration](../2026-09-15-b-sweep/PRE-REGISTRATION.md)
both say:

> ship the FIRST value, descending, that **nets positive on all three families —
> `dump`, `content` and `main`, each individually, none negative**

**`dump` sits at 30/30 at the baseline.** It is structurally saturated: its
correct answer is the prose document, which already wins at `b = 0.75`. It
**cannot net positive at any value** — only hold or break.

So the rule's head clause is unsatisfiable, and its trailing clause
(*"none negative"*) describes what `dump` can actually do. **This is a
pre-registered rule and its meaning is not the runner's to choose**
([SR-RS](../../../records/0133_predictions.md) decision 10b; an ambiguous result
goes to Arpit). It is in the inbox as part of [W-144](../../open/W-144-structure-aware-extraction.md),
with this evidence, and **no pre-registration is frozen until it is ruled.**

## What this does NOT establish

- **It does not pick a value for `b`.** No threshold is frozen, and the
  descending rule is not applied.
- **It does not replace the run.** This is a synthetic corpus of 510 generated
  documents; the verdict run is the golden ladder's, and fux's own docs tree is
  reopen-trigger evidence only.
- **It says nothing about `b = 0`.** That value is outside the ruled range and
  appears here only because it is where `verbose` was expected to break, which
  is how a control is demonstrated rather than assumed.

## Authorship

| what | who |
|---|---|
| the corpus generator, the `verbose` family, this probe | **this session** |
| the ruled range and the condition | **Arpit**, 2026-09-15 |
| the crossovers | replicated from the 2026-09-15 probe |

**`informed`**, and the corpus is synthetic and authored by the reader of the
results — which is why **no number here may ship a default**. It exists to show
an instrument works.
