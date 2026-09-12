---
type: Pointer
description: "One line: the current state and the immediate next step. Overwritten every session."
---

NOW: W-142 RETIRED · W-115 MEASURED · W-144 answered (compare doc = Arpit's call) · W-136 phase 2 COMPLETE (8 rungs to 10 000) · W-140 row 22 fixed, row 21 not reproduced in 11 tries and deliberately unchanged. All committed, aff3c82 → caa5383.
🔴 W-139 IS ANOTHER SESSION'S (fux-99) — I collided with it on the same run id, truncated its docs-10000 rows twice, and contaminated two hours of its timings by indexing golden rungs on the same machine. I killed my run, deleted my rows, did NOT re-run. `docs-10000` is UNMEASURED. `pgrep -f bench.py` before timing anything; MACHINE.md §Two sessions on one machine.
⚠ Arpit, 2026-09-12: the built corpora in fux-lab and fux-benchmark are KEPT and reused — never wiped. SETUP-LAB and SETUP-BENCHMARK carry it.
⚠ One unit test is red and it is NOT this session's: `test_working_tree_is_not_mid_violation` fires on ADR-RERANK and ADR-RS from a prior session's uncommitted `src/` edits. It was 7 red on arrival.
