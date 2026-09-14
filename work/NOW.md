---
type: Pointer
description: "One line: the current state and the immediate next step. Overwritten every session."
---

✓ 2026-09-14 Claude Code: **`main` merged into `release/3.0.0-alpha.0`** — 22 conflicts, and the one that mattered was the **same fetcher fix in two shapes**. Resolved toward this branch: `UrlSource.config_for()` in `config.py` survives (one resolution point for `ingest/urlsrc.py` and `query/refer_answer.py` alike, with `[sources] urls_file`, `.env` overrides and the doctor row `main` never had); `main`'s `urlsrc.config_for()` and its three tests are **dropped**, covered by `tests/test_config.py`. ⚠ **[SR-FETCHER](../records/0117_fetcher.md) decision 8 was STALE on this branch** — it still said *"passed to `configure()` verbatim"* while [SR-CONFIG](../records/0113_config.md) 8a said otherwise; `main`'s rewrite is kept and re-pointed, so the two records no longer disagree. **Carried across whole:** the `.xlsx` decoder fix (phantom rows, truncation and column notices — [SR-TABULAR](../records/0150_tabular.md) decision 7), which exists nowhere else, and `2.0.1`'s version bump, changelog and release record. ⚠ **npm `2.0.1` is STILL STAGED** and waits for Arpit at npmjs.com. 🔴 `work/BLOCKED.json` open. Five 🔴 on Arpit: W-156, W-146, W-112, W-144, W-148 — plus W-170's two rulings and W-175.

→ **Next:** approve npm `2.0.1`; then W-169's successors on this branch.
