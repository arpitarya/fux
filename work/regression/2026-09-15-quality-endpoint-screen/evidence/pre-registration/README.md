# Why this mirror exists

**`VERDICT.md` is frozen and points at `work/proposals/quality-endpoint-for-reranking.md`.**
That proposal archived on **2026-09-20** — its trigger had fired on 2026-09-15
and W-154, the item it graduated into, closed **FAIL** on 2026-09-16
([W-206](../../../open/W-206-compare-and-proposals-sweep.md) B2) — so the path
the verdict names no longer resolves.

🔴 **The verdict was not edited.** `tests/test_regression_runs.py` states the
repair for exactly this case: mirror the pre-registration into the run rather
than touch the frozen ruling, because *"a verdict without its frozen threshold
is an opinion"*.

**Which version is mirrored, and why.** The one committed at **`bed465f3`
(2026-09-15)** — the last state before the screen ran. The next commit to touch
the file is 2026-09-16, after the verdict.

⚠ **This is the second time an archive move broke a frozen verdict's pointer**
(the first was W-87 on 2026-09-20, mirrored into
`2026-08-27-p3-sha-stability/`). **Closing an item or archiving a document can
invalidate a frozen artifact three directories away, and only the whole suite
sees it** — `tests/test_doc_links.py` cannot, because `work/regression/**` is
frozen-by-law and exempt from it.

**The live successors** of the proposal itself are named in
[`archive/README.md`](../../../../archive/README.md) §*Archived 2026-09-20*:
this screen's verdict, and
[W-154's FAIL](../../../regression/2026-09-16-rerank-quality-b2/VERDICT.md).
The archived file is history, never evidence.
