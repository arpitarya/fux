---
type: OpenItem
id: W-213
title: "W-213 — the confidence band's operating point: it catches a fifth of what it is for and withholds a third of what it could answer"
description: "Measured by W-204 phase D on 2 992 questions: HEAD withholds on 818 and the key says 747 of those were answerable. Per set it catches 20.8-32.3% of the genuinely unanswerable and withholds 22.7-30.2% of the answerable — fourteen answerable questions sacrificed per unanswerable one caught on sets 2 and 3. Stable across a 357x corpus range, so it is where the threshold sits. The cost is now measured; the benefit still is not."
status: open
lane: agent
timestamp: 2026-09-22T00:00:00Z
filed: 2026-09-22
ball: agent
---

# W-213 — the band abstains far more than it should, and now there is a number

**Model: Opus** — it moves a ranking-adjacent threshold on `informed` data, which
is the exact shape [SR-RS](../../records/0133_predictions.md) decision 10b exists
to stop being done casually.

## The measurement

[W-204 phase D](../regression/2026-09-22-golden-final-score/FINAL-SCORE.md), HEAD
arm, 2 992 questions over eight rungs and three question sets. Each set carries
**12 unanswerable questions**, so 96 rows per set across the ladder.

| | set-1 | set-2 | set-3 |
|---|---:|---:|---:|
| **caught** — unanswerable it withheld on | 31/96 · **32.3 %** | 20/96 · **20.8 %** | 20/96 · **20.8 %** |
| **cost** — answerable it withheld on | 205/904 · **22.7 %** | 271/896 · **30.2 %** | 271/904 · **30.0 %** |
| **precision** — abstentions that were right | 31/236 · **13.1 %** | 20/291 · **6.9 %** | 20/291 · **6.9 %** |

🔴 **On sets 2 and 3, fourteen answerable questions are sacrificed for every
unanswerable one caught.** At this operating point the band is the largest single
source of lost answers in the engine.

⚠ **Not a corpus-size effect, which rules out the comfortable explanation.** On
set-1 it withholds 25–33 per rung and catches 3–5, from `rung-seed` to
`rung-10000` — a **357×** range. The rates barely move. **This is where the
threshold sits.**

## What this does NOT establish, and it is half the picture

🔴 **The run measures what abstention COSTS and says nothing about what it
SAVES.** No answer-text verdict was made, so *"the answers it withheld would have
been wrong"* is **unmeasured**, not disproved.
[SR-CONFIDENCE](../../records/0141_confidence.md)'s whole argument, and W-176's,
is that ten wrong links produce a confident wrong answer — and that benefit is
exactly what this run could not price.

⚠ **So the obvious move is the wrong one.** *"Lower `separation_floor` until
caught and withheld cross"* optimises a number whose counterpart is missing, on
data the optimiser has already seen. **It would be a threshold tuned on its own
test set**, which is the failure decision 10b names.

## Definition of done

1. **A frozen pre-registration first**, both directions, the d19 paired floor —
   before a line changes. It must name **what is being traded**, not just what is
   being improved: the endpoint cannot be `abstain_wrong` alone.
2. 🔴 **An answer-quality arm, or an explicit statement that the item ships
   without one.** The honest version needs to know whether the withheld answers
   would have been wrong. Options, none free: the judged series
   ([SR-WORK-QUALITY](../../records/0056_WORK-quality.md)) on a sample; or a
   proxy endpoint that is named as a proxy. **Choosing neither, silently, is how
   this item becomes a number-lowering exercise.**
3. **Measured on a RETIRED set, not a sealed one.** Once
   `just golden-retire` has run these questions are open regression data
   (L11 decision 14) and a sweep over them is legitimate tuning rather than a
   contaminated benchmark. ⚠ **And every number from it is still `informed`** —
   retiring changes what the data is for, not what it has seen.
4. Records: SR-CONFIDENCE for the operating point; SR-RS for the prediction id.

## Two things worth knowing before starting

- 🔴 **`v2`'s band exists and never fires** — `answerable: true` on 2 992 of
  2 992, with `weak` on 975 rows. So the two fields can be wired apart, and phase
  A's *"`band: weak` ⇔ `answerable: false`, 3 984 of 3 984"* is **a property of
  HEAD**, not of the band concept. Anything that reasons from that equivalence
  should check which engine it is reasoning about.
- ⚠ **`fux answer` returns text on every call**, including the 818 the band
  withheld on. The decline is the band's flag, never a null answer — so a
  consumer that ignores `answerable` sees no abstention at all.

## Out of scope

The funnel (that is **W-212**, closed 2026-09-22 — its outcome is in
[`IMPLEMENTATION.md`](../IMPLEMENTATION.md)), the
answer-text verdict as a general instrument, and anything that moves
`separation_floor` before a pre-registration exists.
