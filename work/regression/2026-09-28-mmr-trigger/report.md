---
type: Regression Report
description: "W-168 step 7 (MMR) STOPS before build, key-free. On the shipped configuration's set-4-claude hand-off, the ruled swap's trigger (top 5 in one graph community) fires on 7 of 125 questions, and only 5 have another community's document in ranks 6–10. A net of 6 cannot be reached, so no bar is written, no build happens and nothing is scored."
run: 2026-09-28-mmr-trigger
item: W-168
classification: informed
---

# Report: can step 7's swap fire often enough to be measured?

**No. The ceiling is 5 swaps, below [SR-RS](../../../records/0133_predictions.md)
d19's floor of a net of 6. Step 7 STOPs before build.**

## What was run

| | |
|---|---|
| hand-off | `2026-09-28-intent-prior/evidence/ip-0.1/rung-01000/handoff-set-4-claude.jsonl` (sha256 `6207c88e…`), the arm whose `intent_weight = 0.1` shipped, stacked on `anchor 1.0` and `mined_weight 0.5` |
| index | that arm's own copy, `fux-lab/arms/runs/ip-0.1/rung-01000` (gen-3 `rung-01000` at `b73348d5`), read only |
| engine | `0e4e18ef` (this repo's HEAD), `fux.api` graph plane: label propagation over committed edges |
| script | [`evidence/trigger.py`](evidence/trigger.py) → [`evidence/trigger.txt`](evidence/trigger.txt), and one row per question in [`evidence/per-query.jsonl`](evidence/per-query.jsonl) |

```
questions=125 fires=7 ceiling@6-10=5
distinct communities in the top 5: {1: 7, 2: 8, 3: 14, 4: 15, 5: 81}
graph: 226 linked documents in 95 communities
```

**This is not a paired run**: one hand-off is counted, and no arm is compared
against another, so there is no headroom to report ([SR-RS](../../../records/0133_predictions.md) d22).

## The ruling it was run under

- **The design** (Arpit, 2026-09-28): top 5 all in one community → swap #5 for
  the best document of another community.
- **The candidate depth** (Arpit, 2026-09-28, this session): *ranks 6–10 → STOP*.
  The swap only reorders what the user already receives.
- The ruled early stop (a minimum multi-facet pool) needed the key. **This count
  is upstream of it, and needed nothing from the key**: a swap that cannot fire
  cannot win, so the facet column was never required.

## Authorship

Captured and counted by Claude Code (Opus). The questions are Claude-authored
(set-4-claude), so the run is `informed`. **No key was opened and `score.py` was
not run.**
