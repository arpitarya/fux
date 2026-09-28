---
type: Verdict
name: W-233-IDENTIFIER-FAMILIES
description: "W-233, identifier families: PASS by the frozen table. E1 nets +25 / +88 / +105 with 0 broken, E2 0 broken on a full guard, E3 0 of 60 moved, and G1–G3 all hold. Every clause clears by a wide margin, so this is not an ambiguous result for Arpit to rule (SR-RS decision 6)."
verdict: PASS
verdict_by_table: PASS
prediction: W-233-IDENTIFIER-FAMILIES
pre_registration: work/regression/2026-09-28-identifier-families/PRE-REGISTRATION.md
run: 2026-09-28-identifier-families
item: W-233
filed: 2026-09-28
classification: informed
---

# VERDICT: PASS — the mechanism ships

Judged against [PRE-REGISTRATION.md](PRE-REGISTRATION.md) §5, frozen at
`cca32152`. **No threshold moved, no query row was added, removed or
retargeted, and no after-arm file was edited.**

| clause | needed | measured | holds |
|---|---|---|---|
| E1 net ≥ +6 on at least one rung | +6 | **+25 · +88 · +105** | ✅ all three |
| no rung with E1 or E2 net ≤ −6 | > −6 | E1 broke **0**; E2 net **0** (0 broken of 28 · 119 · 113) | ✅ |
| E3 fewer than 6 of 60 rank-1 changes | < 6 | **0** | ✅ |
| G1 parity | 0 divergent | **0 of 999** | ✅ |
| G2 determinism | byte-identical | **all three rungs** | ✅ |
| G3 inertness | byte-identical | **rung-01000** | ✅ |

**Not ambiguous** ([SR-RS](../../../records/0133_predictions.md) decision 6):
the smallest margin is E1 at rung-00100, +25 against a floor of 6, and every
guard is at zero against a tolerance of 6. The runner records the table's
verdict and chooses no reading.

**Therefore, per §5:** the verb, the file, both readers, the doctor rows and
the Identifiers tab ship.
[SR-IDENTIFIERS](../../../records/0160_identifiers.md) is accepted in the same
change.

**Evidence:** [report.md](report.md) ·
[evidence/decision.json](evidence/decision.json), written by the frozen
`evidence/decide.py` · [per-query rows](evidence/per-query-rows.jsonl).
