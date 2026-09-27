---
type: Tool
description: "Plans a golden rung's git history from work/golden/seed-history.tsv, so the git authority prior (W-168 step 8) has commits and authors to read. Test-data item T11."
---

# `tools/golden-history/` — history for the golden ladder

**One module, [`replay.py`](replay.py), and one job:** turn
`work/golden/seed-history.tsv` into the ordered commits a rung is built from.

- **Why:** the git authority prior (W-168 step 8) reads authors × commits per
  document. The ladder committed each document **once, as `fux-lab`**, so it
  had nothing to read — test-data item **T11**
  ([SR-WORK-TESTDATA](../../records/0068_WORK-test-data.md)).
- **Who calls it:** `fux-lab/shared/generate/build_golden_rung.py`, step 4.
- **No history → no change.** With the file absent or empty, the plan is the
  old ladder's, commit for commit. `tests/test_golden_history.py` holds that.
- 🔴 **Reads `seed-dates.tsv`, `seed-history.tsv` and `seed-history/` only** —
  never a question file, never a key.

**The file's format and rules** are in `replay.py`'s docstring, which is the one
place they are stated.
