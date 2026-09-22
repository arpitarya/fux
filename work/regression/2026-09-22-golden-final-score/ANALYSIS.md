---
type: Analysis
run: 2026-09-22-golden-final-score
description: "What phase D's numbers actually oblige. One finding is a result to keep, one is a defect worth a work item, one is a gap in the instrument, and one is a claim nobody can make yet."
classification: informed
filed: 2026-09-22
---

# ANALYSIS — four things follow from this run

## 1 · 🔴 The abstention band is the engine's weakest layer, and it is a work item

**The numbers.** HEAD withholds on 818 of 2 992. The key says **747 of those 818
were answerable**. Per set, the two rates that decide whether an abstention layer
earns its place:

| | set-1 | set-2 | set-3 |
|---|---:|---:|---:|
| unanswerable it caught | **32.3 %** | **20.8 %** | **20.8 %** |
| answerable it withheld | **22.7 %** | **30.2 %** | **30.0 %** |

**On set-2 and set-3 it sacrifices fourteen answerable questions for every
unanswerable one it catches.** At this operating point the band is not a safety
feature; it is the largest single source of lost answers in the engine.

🔴 **It is not a corpus-size effect, and that is what makes it actionable.**
Across `rung-seed` → `rung-10000` on set-1 — a **357×** range — it withholds
25–33 per rung and catches 3–5. The rates barely move. **This is where the
threshold sits**, not something a bigger index fixes.

**What follows.** A work item against
[SR-CONFIDENCE](../../../records/0141_confidence.md) to re-derive the operating
point, with this run's rows as the input. ⚠ **It needs a pre-registration before
a threshold moves** — `separation_floor` is a ranking-adjacent tunable and
[SR-RS](../../../records/0133_predictions.md) decision 19 applies. The obvious
sweep — lower the floor until `caught` and `withheld` cross — **must be
pre-registered in both directions**, because a floor tuned on the run that
measured it is a floor tuned on its own test set.

⚠ **Do not read this as "remove the band".** W-176's whole argument is that ten
wrong links produce a confident wrong answer, and this run cannot price that: it
measures what abstention **costs** and says nothing about what it **saves**,
because the answer-text verdict was not made. **The cost is now measured and the
benefit is still not.**

## 2 · ✅ Resistance to distraction is what improved, and it is the first time it is measured

`hit@5` from `rung-00100` to `rung-10000`: v1 **−30**, v2 **−43**, HEAD **−10**.
The three engines are closest on the smallest corpus and furthest apart on the
largest.

**That is the index-and-refer thesis, measured.** The paper's claim is that
ranking from a small committed index and verifying at answer time holds up as a
corpus grows; **this is the first run in the project that puts a number on it**,
and it does so on three independently authored question sets with all nine
paired comparisons clearing the floor.

⚠ **What it does not license.** The design point is 10 000 documents
([SR-WORK-SCALE](../../../records/0057_WORK-scale.md)), `rung-10000` is the top
of the ladder, and **nothing here extrapolates past it.** The curve is flattening
between 5 000 and 10 000 for every arm — 225→226, 232→232, 286→286 — which is
consistent with a plateau and equally consistent with a ceiling in the question
set. **Neither reading is supported and the run does not choose one.**

## 3 · 🔴 The funnel could not be computed, and the instrument is why

W-204 phase D step 4 asks for SR-WORK-QUALITY's `reachable → in window → placed
→ answered`, cost-weighted at `c = 2`. **It is W-87's headline and it is not
here.** The hand-offs carry the ranked list and the answer; `reachable` and
`in window` live in `ask --json --why`'s `derivation.gates`, and **prompt 5 never
captured them**.

**What follows, and it is cheap:** prompt 5 gains `--why` and records
`derivation.gates` per question. Phases A and B then re-run — ~12 000 calls,
machine time — and the funnel computes from the same rows this pass already
joins. 🔴 **Until then, no document may state fux's funnel**, and W-87's `judged`
series stays unpinned.

⚠ **This is a measurement-design defect, not a scoring one.** The scoring pass
was complete on what it was given. **The instrument was specified without one of
the fields its own headline metric needs**, which is the same class as W-168 step
1 shipping against a corpus with zero `ref` edges — *the data does not contain
the input the metric acts on*.

## 4 · ⚠ v2's band exists and never fires — and it changes what the earlier runs mean

`v2` emits `band` on all 2 992 rows (`weak` 975, `partial` 924, `grounded`
1 093) and `answerable: true` on **all 2 992**. It never abstains.

**Two consequences:**

- **There is no cross-arm abstention comparison in this benchmark**, and no row
  may be read as *"HEAD abstains worse than v2"*. v1 has no band at all; v2 has
  one that reaches no decision. **An absence, not a regression.**
- 🔴 **The earlier runs' headline finding needs re-reading.** Phase A filed
  *"`band: weak` ⇔ `answerable: false`, 3 984 of 3 984"* and the set-3 re-run
  filed it again on 2 992. **That equivalence is a property of HEAD**, and v2
  shows the two fields can be wired apart — same `weak` band, `answerable` always
  true. The finding stands for the engine it was measured on; it is not a
  property of the band concept, and nothing should treat it as one.

## What this analysis deliberately does not propose

- **No threshold is moved here.** Every number above is `informed`, and a
  threshold moved on informed data is a threshold tuned on its own test set.
- **No difficulty band is frozen** — step 2 was not run, so SR-RS decision 10b
  has nothing to bite on.
- **No claim about answer quality.** `evidence_quoted` rises v1 → v2 → HEAD
  (1 019 → 1 494 → 1 696) and **that is a substring test**, not a verdict. It is
  reported and not interpreted.

## The next three things, in order

1. **`just golden-retire set-1 / set-2 / set-3`, then `just golden-lock`** —
   Arpit's hand. The generation is scored; retiring it turns these questions into
   reusable regression data and re-seals the next one.
2. **A work item on the confidence band's operating point** (finding 1), with a
   pre-registration before any threshold moves.
3. **Prompt 5 captures `derivation.gates`** (finding 3), so the next generation's
   phase D can compute the funnel this one could not.
