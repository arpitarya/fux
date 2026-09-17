---
type: Analysis
name: b-sweep-2-analysis
description: "Why 0.15 and not 0.3, what the reclassification did and did not change, and the one thing that would make this number shippable beyond a synthetic corpus."
---

# Why `0.15`, and what it is worth

## `content` crosses at 0.3 and `main` at 0.15 — the rule needs both

The two benefit families cross at **different values**, and that is the whole
reason the answer is `0.15`:

| family | what it is | crosses between |
|---|---|---|
| `content` | a rate card whose subject **is** its rows | **0.4 and 0.3** |
| `main` | prose with a table **appendix** | **0.2 and 0.15** |

**The rule requires both, each individually, neither negative.** So `0.3` and
`0.2` fix the rate card and leave the appendix case exactly where `0.75` does,
and only `0.15` moves both.

🔴 **A rule that had asked for *either* would have shipped `0.3`**, and half the
mechanism would have gone unmeasured with a passing verdict on the file.

## What the reclassification changed, precisely

**It stopped asking a saturated family to improve. It did not lower the bar.**

| | before (2026-09-15) | after (2026-09-16) |
|---|---|---|
| must net positive | `dump`, `content`, `main` | `content`, `main` |
| must hold | `inverse`, `placebo`, `verbose` | `inverse`, `placebo`, `verbose`, **`dump`** |
| decision 19 floor | same | same |
| range, order, first-that-clears | same | same |

**`dump` is required to hold and it held.** Had it regressed at `0.15`, the run
would have FAILED under the new rule exactly as under the old one — the
difference is only that the old rule *also* demanded an improvement `dump` was
structurally incapable of producing.

⚠ **The old rule was unsatisfiable, so it could only ever produce `FAIL`.** A
rule that cannot pass is not a strict rule; it is a broken one, and it would have
recorded a false negative against a lever that demonstrably works on two of three
families.

## What would make this shippable beyond the corpus that produced it

**Nothing here does**, and the gap is worth naming precisely rather than
gesturing at:

1. **The corpus is generated.** 510 documents from this project's own tool, with
   a fixed seed. It is built so the mechanism *can* move — which is what makes
   it a valid instrument and what stops it being evidence about real documents.
2. **The probe terms are nonsense tokens** with `df` 2–12. Real house vocabulary
   has a different distribution.
3. **`informed`.** The `verbose` family's author reads the results.

**The reopen-trigger evidence W-144 asks for** — fux's own docs tree — is the
next measurement, and it may produce the verdict for nothing: the item is
explicit that only the generated corpus may. ⚠ **A default shipped on this alone
is a default shipped on one synthetic corpus**, which is why step 4 pairs it with
an SR amendment somebody has to read rather than a silent value change.

## The one number that decides whether the controls said anything

**`verbose` at `b = 0`: 0/30.**

Every control reads `+0` at every value in the ruled range. That is either *the
treatment is safe* or *these families cannot report*, and the two are
indistinguishable from the range alone. **One family has now been driven to zero
outside the range**, so its silence inside it is a measurement.

🔴 **And the probe that produced it found the blind spot was one value wide** —
`b = 0` and `b = 0.15` agree on `main`, `content`, `dump`, `inverse` and
`placebo`, and differ only on `verbose`. Arpit's condition was not procedural
caution.
