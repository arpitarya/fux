---
type: Analysis
description: "What W-278's capture leaves: every gate and the latency guardrail pass, and the arms move rank 1 on few questions — 7 of 165 at the decided arm. Whether that clears the slice floor and C1 is the score's to say."
run: 2026-10-13-section-term-v3
item: W-278
---

# ANALYSIS — W-278's capture

## 1 · The latency fix held on generation 6

**Finding.** +49.5 ms at gen-6 `rung-10000`, against +328 ms for W-270's form.
**Cause:** the scan reads sections from the derived plane when the runtime is
fresh (SR-SECTIONS decision 7, W-278 DoD 2). **Change:** none here. Repro:
`python3 evidence/latency.py --fux <08ef6293 fux> --arms ~/my_programs/fux-lab/arms/runs/s7-lat --questions work/golden/questions/set-7-claude.jsonl`.

## 2 · The decided arm moves rank 1 on 7 questions

**Finding.** Rank 1 changed on 7 of 165 at `sw-1.0` (4 at `sw-0.5`), against
21 and 33 for W-270's form at `sw-2.0`/`sw-4.0`. Every move brings in a long
sectioned document. **Unresolved, and not this session's to resolve:** the
slice floor is 15 baseline misses and C1 needs SR-RS decision 19's floor at
the observed flips. **Seven rank-1 changes bound the slice's wins at 7**, so
if the slice is ≥ 15, C1 clears only if few of those 7 are wrong — the score
decides. A FAIL: no gain is a possible outcome and would be a finding about
the max form at `b = 0.15`, not a defect.

## 3 · The capture was 15 minutes, not 45

The estimate given to Arpit was high; the run took 15 min. Speed work is
[W-281](../../open/W-281-capture-harness-speed.md).
