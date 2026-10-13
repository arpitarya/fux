---
type: Verdict
name: W-278-SECTION-TERM-V3
description: "W-278, the section term's third form at section_weight = 1.0 on set-7-claude under law L13: INCONCLUSIVE by the frozen table, handed to Arpit. Every gate, C2, C3 and every guardrail hold; the slice (24) gained 5 with 0 losses, below SR-RS decision 19's floor at 5 flips (p = 0.0625). Whole set hit@1 117 -> 123, 6 wins, 0 losses. Decider run by Arpit 2026-10-13. section_weight stays 0.0 until he rules."
verdict: INCONCLUSIVE
verdict_by_table: "INCONCLUSIVE — C2, C3 and the guardrails hold; the slice net is positive (5) but below decision 19's floor"
ruled_by: "Arpit, 2026-10-13 — ran the frozen decide.py from his own shell; the ruling the table hands him is owed"
prediction: W-278-SECTION-TERM-V3
pre_registration: work/regression/2026-10-13-section-term-v3/PRE-REGISTRATION.md
run: 2026-10-13-section-term-v3
item: W-278
filed: 2026-10-13
classification: informed
---

# VERDICT — W-278: INCONCLUSIVE, to Arpit

Decider: [`evidence/decide.py`](evidence/decide.py), frozen at `2ac82d3b`, run
by Arpit; output [`evidence/decision.json`](evidence/decision.json),
[`evidence/per-query.jsonl`](evidence/per-query.jsonl).

| row (L13) | `sw-1.0` (decided) | holds |
|---|---|---|
| gates G0 · G1 · G3 · G4 | PASS · PASS · PASS · PASS | ✅ |
| slice size (`step10_section` misses at baseline) | **24** (floor 15) | ✅ |
| **C1** slice net vs SR-RS d19 | **5 wins, 0 losses** (b=5 c=0, p = 0.0625) | ❌ below the floor, not negative |
| C2 collateral outside the slice | −1 (one win, no loss; margin 4) | ✅ |
| C3 whole-set `hit@1` net | **+6** (117 → 123; 6 wins, 0 losses) | ✅ |
| `hit@5` · `evidence_quoted` · `grounded` | 148 → 148 · 142 → 144 · 86 → 89 | ✅ |
| latency at `rung-10000` | +49.5 ms | ✅ |

The slice split is exact here: the counts admit one value, `s = 5`.
**L13 decision 4's INCONCLUSIVE row, second clause:** *C2, C3 and the guardrails
hold and the slice net is positive but below decision 19's floor.* Also:
`primary@1` 7 wins, 0 losses.

`sw-0.5` (reported only): +3, slice 3 wins, 0 losses, INCONCLUSIVE.

**What it means.** No question got worse at either weight. The term fixed 5 of
the 24 long-document misses it was built for, and one more elsewhere. Five
flips cannot clear the floor of all floors (a net of 6), so the size of the
effect, not its direction, is what is unproven. `informed`, permanently.

**Owed: Arpit's ruling** (L13 decision 4). Until then `section_weight` stays
`0.0` and W-273 phase 2 does not run.
