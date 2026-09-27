---
type: Analysis
run: 2026-09-27-golden-set-4-rung-01000
item: W-168
classification: informed
description: "What the set-4-claude surface capture can and cannot support before Arpit scores it: nothing keyed, one caution about the band, and the order the step pools follow."
filed: 2026-09-27
---

# ANALYSIS — `set-4-claude` on the generation-3 `rung-01000`

**A surface capture, with no key in reach.** This analysis explains what the
counts in [report.md](report.md) can mean. It never says whether an answer is
right.

## What the capture supports

- **The instrument is whole.** Every one of the 125 rows has ten ranked paths,
  a band, the five funnel-gate integers, a `refer` answer and a `current`
  citation. A scorer can compute every field phase 6 needs without a re-run.
  The gates matter most: they cannot be recovered later (SR-WORK-QUALITY d13).
- **It is the first golden baseline at the shipped ranking.** `anchor = 1.0`
  (step 1) and `mined_weight = 0.5` (step 4) were both `0.0` in every earlier
  golden capture. A later step 6–10 arm is paired against these rows, not
  against the 2026-09-24 ones.

## What it does not support

- **The band cannot be read as quality.** `grounded` on 69 rows means only
  that the top result is separated from the runner-up by the provisional floor
  (R10, unmeasured). It does not mean 69 answers are right. Band `none` never
  fired, so fux's `answerable` flag says nothing about this set's unanswerable
  slice.
- **No comparison with generation 2.** The ladder, the set and two ranking keys
  all changed at once, so a band shift between the captures has three causes
  and no way to separate them.
- **No pool count.** Each step's pool is a miss the step's mechanism could win.
  Knowing a miss needs the key.

## The order after the score

1. Arpit scores (`just golden-score`, his shell).
2. A session counts each step's pool, 6 SDM · 7 MMR · 8 authority · 9 intent ·
   10 section units, from the score file's per-query rows and the tags.
   **Below 6 stops that step**, as before.
3. Step 10 pre-registers first, because its forks are already ruled
   (U0 · B2 · E1).
