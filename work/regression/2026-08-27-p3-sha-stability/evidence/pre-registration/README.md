# Why this mirror exists

**`VERDICT.md` is frozen and points at `work/open/W-87-what-good-means.md`.**
That file closed on **2026-09-20** — W-204 absorbed W-87 and its detail file
moved to `archive/open/` under queue rules 54–58 — so the path the verdict names
no longer resolves.

🔴 **The verdict was not edited.** `tests/test_regression_runs.py` states the
repair for exactly this case: mirror the pre-registration into the run rather
than touch the frozen ruling, because *"a verdict without its frozen threshold
is an opinion"*.

**Which version is mirrored, and why.** The verdict is stamped
`2026-08-27T17:26:30Z`, and W-87's file was still uncommitted then — the earliest
commit touching it is `70bca180` (2026-08-28). **That is the version here**, as
the nearest committed state to the ruling.

⚠ **The choice does not change the verdict.** §P3's threshold table — the frozen
`≥ 80 %` this ruling was made against — is **byte-identical** in `70bca180` and
in the last version before the file was archived. The file grew by 272 lines
elsewhere over three weeks; the threshold never moved, which is the property
[SR-RS](../../../../../records/0133_predictions.md) decision 10b exists to
protect.

**The live successor of W-87 itself is
[W-204](../../../../open/W-204-golden-outputs-scoring-and-version-benchmark.md)
phase D.** The archived file is history, never authority (queue rule 58).
