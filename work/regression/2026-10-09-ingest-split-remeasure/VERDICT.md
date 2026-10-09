---
type: Verdict
name: PRE-REG-INGEST-SPLIT-2
description: "W-267 - PASS for the close branch of W-256 section 8's frozen rule: delta non-extract N = 4.902 s median at rung-10000 (4.894-4.908 s, no straddle, identical root sha). B-002 may close; the closure is Arpit's ruling (W-267 DoD 4). Margin 0.092 s."
verdict: PASS
prediction: PRE-REG-INGEST-SPLIT-2
pre_registration: work/regression/2026-10-09-ingest-split-remeasure/PRE-REGISTRATION.md
run: 2026-10-09-ingest-split-remeasure
item: W-267
filed: 2026-10-09
classification: informed
---

# VERDICT — N < 5 s: the close branch

Frozen text, section 2:

> - **N < 5 s -> B-002 closes.** The dirty list stays advisory
>   (`maintain/dirty.py`'s docstring is true), SR-MAINTENANCE 1a-3 cites the run,
>   and option D is *not needed at the design point*.

Observed: N = **4.902 s** (4.894 / 4.908 / 4.902), all three under 5 s, so section
2 item 2's straddle does not apply. Valid under section 6: identical root sha on
all seven runs, and three true deltas.

`verdict: PASS` here means **the rule's first branch held**. The rule has no
"pass" outcome of its own. ⚠ **What it does not license:** B-002's row leaves
BACKLOG on Arpit's word, not the runner's (pre-registration section 2, *"What
this run adds to who decides"*). The margin is 0.092 s on one machine.
