---
type: Analysis
run: 2026-10-25-w300-merged-query
---

# ANALYSIS — W-300, the merged query

**No engine change is proposed.** Every gate is an identity: with no pin, or with
`scope = repo`, the merged path is the engine from before W-300, byte for byte.
So the feature can change a ranking only for a consumer who pins an index package.

**What the slice measures:** the 16 questions answerable only from the package.
The baseline (the repository alone) cannot win any of them. So C1's 16 / 0 shows
the package is reached and ranked, not that the shared statistics are well tuned.

**What it did not exercise:**
- **The large-package case `scope` exists for.** The package was smaller than the
  consumer (3 documents against 6), so "a large package fills the top-k" never
  arose.
- **Two identifier families**, where a package is built under other identifier
  rules. The unit tests in `tests/test_pkg_merged_query.py` cover that, not this
  run.

**A hazard found during the build, not by the run:** a package document and a
repository document can share an id (`file:docs/x.md`). The display, `fux_search`
and `answer` resolve by `package`. The steps after ranking that key on id alone
(the graph walk's window, `sections_out`) could mix the two up. This is recorded
in SR-PKG-INDEX d10 for a follow-up.
