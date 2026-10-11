---
type: Verdict
name: W-270-SECTION-RETEST-SET-6
description: "W-270, the gain-only section term at section_weight = 2.0 on set-6-claude under law L13: STOP by the frozen table — the baseline's step10_section slice is 11, below the floor of 15, a data defect and never a verdict on the term. Gates G0, G1, G3 PASS; the latency guardrail had already failed (+328 ms). section_weight stays 0.0; nothing reached main. Decider run by Arpit 2026-10-11."
verdict: INCONCLUSIVE
verdict_by_table: "STOP — the slice is 11, below 15"
ruled_by: "Arpit, 2026-10-11 — ran the frozen decide.py from his own shell"
prediction: W-270-SECTION-RETEST-SET-6
pre_registration: work/regression/2026-10-11-section-retest-set-6/PRE-REGISTRATION.md
run: 2026-10-11-section-retest-set-6
item: W-270
filed: 2026-10-11
classification: informed
---

# VERDICT: STOP — the slice is 11, below 15

**Who adjudicated.** Arpit ran [`evidence/decide.py`](evidence/decide.py) from
his own shell on 2026-10-11. Its sha256 is
`7dd5a04c5bd8ad54ba16918852f6dc30df12643968f621a267c092d85916de35`, the hash
frozen at `9ab19fc6` before the generation-5 ladder existed, unchanged. The
session that captured the arms only files his output here (the bar's item 4).
No threshold moved.

**Evidence:** the four score files under `scores/` (Arpit's `just golden-score`)
and [`evidence/decision.json`](evidence/decision.json), written by that run.

⚠ **Filed as `INCONCLUSIVE` in [SR-RS](../../../records/0133_predictions.md)'s
five-way vocabulary**, which has no STOP: SR-RS's INCONCLUSIVE is *the
instrument could not decide*, and a slice too small to measure is exactly
that. It is **not** L13's INCONCLUSIVE row (C2 missing by 1–2, or a positive
slice net below the floor); the table's own word is STOP, kept in
`verdict_by_table`. Not VOID: the bar was complete and applied.

## The table's output

```
STOP — the slice is 11, below 15
```

| | |
|---|---|
| gates | G0 PASS · G1 PASS · G3 PASS ([report](report.md) §2) |
| slice (`step10_section` `miss@1` at `sw-0.0`) | **11** (`reorderable@1` 11); floor **15** (L13 decision 3) |
| latency guardrail | FAIL, +328 ms against 100 ([report](report.md) §3) — not read by a STOP, recorded |

## What it means

- **A STOP is a data defect, never a verdict** (L13 decision 4). It says
  nothing about whether the term helps: the set could not measure it.
  `section_weight` stays `0.0`, and nothing merges.
- **Why the slice is small.** Prompt 14 asked for ≥ 60 `step10_section`
  questions on new long documents, and the key tags 60. The baseline engine
  already places **49 of them at rank 1**, so only 11 were left to win. The
  premise the set was built on — long documents losing at rank 1 — mostly does
  not hold on these six documents at `b = 0.15`.
- **The guardrail failure stands on its own.** Even with a big enough slice,
  `sw-2.0` as built could not PASS: L13's PASS needs every guardrail.
- **What happens next is Arpit's.** L13 decision 3: *a run that needs a smaller
  slice says so and asks Arpit.* The options and the recommendation are in
  [W-270](../../open/W-270-section-retest-set-6.md).
