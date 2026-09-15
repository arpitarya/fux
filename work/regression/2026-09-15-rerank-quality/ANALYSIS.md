---
type: Analysis
run: 2026-09-15-rerank-quality
description: "The endpoint's defect, why two screens missed it, the exact fix, and what a screen can and cannot be asked to do."
filed: 2026-09-15
---

# ANALYSIS — a screen that passed twice while the defect was present

## 1 · The diagnosis, in one sentence

**The query's own source document is in the candidate set, and a proximity
reranker is built to find the document that contains a phrase contiguously.**

Everything follows: 39 of 52 broken contests are the source winning, the `ask`
arm reads −50, and none of it is about whether proximity reranking helps anyone.

## 2 · Why BOTH screens missed it, and this is the transferable part

The screen asks: *is the true passage/document also the one the reranker's
objective would pick?* It scores the **candidates it is handed**.

| screen | candidates it compared | `agreement` |
|---|---|---|
| passage-level | the target document's own passages | 0.4141 |
| document-level | the **other cited documents** from the same source file | 0.5273 |

🔴 **Neither ever contained the citing document**, because neither was asked to.
The screen answers *is the truth the objective's own pick among these rivals*; it
cannot answer *is there something else in the corpus that beats them all*, and
nothing in its construction suggests it could.

**So the screen's design is sound and its scope was narrower than it was used
for.** That distinction matters: the fix is not a better screen, it is
**screening the candidate set the arm actually ranks over**.

## 3 · The fix, exactly

**Per contest, exclude the `source` document from the candidate set.** It is
recorded on every contest already (`cited_decision.py` emits `source`), so this
is a filter on the ranked list rather than a corpus change — which keeps the
index and both readers untouched.

⚠ **It must be frozen in a NEW pre-registration before the next number.** The
bar is unchanged; what changes is the instrument, and writing the change in
after seeing these numbers and calling it the same run would be the
moving-threshold failure wearing a repair's clothes.

**Two smaller corrections owed in the same pass:**

1. **Regression headroom means *right in the BASELINE arm*,** not *right in both*.
   The pre-registered definition reports what survived rather than what was at
   risk — 5 instead of 57 — and is post-hoc whenever an arm breaks things.
2. **The `answer` path needs a usable hit criterion.** 4 of 538 in the baseline
   is no signal. Overlapping the *top* cited passage with the decision's line
   range is too strict; *any* cited passage, or a rank-aware criterion, is the
   obvious next shape — and it is a design decision, not a loosening, so it goes
   in the pre-registration too.

## 4 · What I would not do

🔴 **Re-run with the exclusion and file it as this run.** The numbers above were
seen first. A corrected instrument gets a new pre-registration and a new run
directory, or the correction is indistinguishable from choosing a result.

⚠ **Conclude anything about `rerank_weight`.** It ships at `0.0`, the price is
measured (+15–19 ms), and the benefit is **exactly as unmeasured as it was this
morning**. W-154 does not close on this.

## 5 · The specific changes

| # | change | repro |
|---|---|---|
| 1 | `tools/quality-controls/rerank_partb.py` — the two-arm, two-path runner | `rerank_partb.py --tree <scratch> --contests <file>` |
| 2 | the document-level screen, which the pre-registration required first and which **passed** | `evidence/document-screen.json` |
| 3 | **the run filed `VOID`**, with the contamination measured at 75 % | `VERDICT.md` |
| 4 | **W-154 stays open**, with the fix named | `work/OPEN-WORK.md` |

## 6 · Unresolved

- **W-154's actual question.** Untouched.
- **The corrected endpoint**, and whether excluding the source leaves enough
  discordant pairs to clear the floor — 13 contests moved for reasons other than
  the source, and **13 is above 6 but not by much**.
- ⚠ **Whether a citing sentence is a fair query at all.** Excluding the source
  fixes the scoring; it does not make *"a sentence somebody wrote about a
  document"* the same thing as *"a question somebody would ask"*. That is the
  dogfood caveat the pre-registration already carries, and it is larger than it
  looked this morning.
