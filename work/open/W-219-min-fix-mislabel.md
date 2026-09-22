---
type: OpenItem
id: W-219
title: "W-219 — `ranking_headroom.py`'s `min_fix` is the net needed if the WHOLE pool flips, not the fewest wins that clear, and three documents read it as the latter"
description: "Found 2026-09-23 while pre-registering W-168 step 5. ranking_headroom.py documents min_fix as 'the smallest number of wins that clears, assuming zero regressions' but computes smallest_detectable(pool), i.e. the net SR-RS d19 needs when the discordant count equals the whole pool. With zero losses, w wins give discordant = net = w, and w = 6 clears for every pool >= 6. The '58–78 % of every remaining failure' claim (SR-RS d24e, the 2026-09-22 step-inputs report, W-215) and the '8 reorderable < min_fix ≈ 9' rationale (W-215, W-168) read the mislabel as a minimum."
status: open
lane: build
timestamp: 2026-09-23T00:00:00Z
filed: 2026-09-23
ball: agent
---

# W-219 — `min_fix` is mislabelled, and the mislabel reached a ruling's rationale

**Model: Sonnet.** A docstring, one column, and prose in documents that cite it.
**No filed verdict changes:** `verdict_possible` was always computed correctly
as `needed ≤ pool`.

## The defect

[`ranking_headroom.py`](../../tools/quality-controls/ranking_headroom.py) sets
`min_fix = smallest_detectable(pool)` and calls it *"the smallest number of wins
that clears, assuming zero regressions"*. **It is the net
[SR-RS](../../records/0133_predictions.md) d19 needs if every question in the
pool flips.** With zero losses, `w` wins give a discordant count of `w` and a
net of `w`. `smallest_detectable(6) = 6`, so **6 wins with zero losses clear
(p = 0.031) at any pool ≥ 6.**

| pool | `min_fix` as printed | the fewest wins that actually clear, zero losses |
|---:|---:|---:|
| 8 | 8 | 6 |
| 18 | 10 | 6 |
| 23 | 11 | 6 |

## Where the mislabel was read as a minimum

- [SR-RS](../../records/0133_predictions.md) d24e: *"One ranking step must fix
  **58–78 % of every remaining failure** with zero regressions"*.
- [`2026-09-22-w168-step-inputs`](../regression/2026-09-22-w168-step-inputs/report.md)
  and its row in `work/regression/README.md`, which say the same.
- [W-215](W-215-generation-2-corpus.md) and the
  [W-168](W-168-search-improvements.md) 2026-09-23 ruling block: *"only 8 are
  winnable by reordering — below `min_fix` ≈ 9"*. That compares the reorderable
  8 with the bar for all 18. **8 wins with zero losses clear.**

⚠ **The 2026-09-23 rank-1 ruling is not reopened by this.** It still stands on
the 51 reorderable misses at rank 1 against 8 at `hit@5`. What changes is one
sentence of its *why*, which said a `hit@5` verdict was impossible when it was
only very unlikely.

## Definition of done

1. `ranking_headroom.py`: rename the column to what it is (for example
   `net_if_all_flip`), add `min_wins = 6 if pool >= 6 else None`, and fix the
   docstring. A unit test pins the pool-8 and pool-18 rows above.
2. SR-RS d24e amended in the record first, then the step-inputs report gets a
   dated correction note (never an edit to its numbers), and W-215 and W-168 get
   the corrected sentence.
3. Both suites, whole.
