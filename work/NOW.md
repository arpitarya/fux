---
type: Pointer
description: "One line: the current state and the immediate next step. Overwritten every session."
---

✓ 2026-09-15 Claude Code: **W-168 step 1 is BUILT** — the anchor field, *what other documents call this one*, in both readers behind `[bm25f] anchor` **default `0.0`**. The words ride the **source's** edge (`at`/`al`); the per-target view folds at read time from `.fux/runtime/anchors/`, so no committed byte crosses a document boundary. `fux.index.v3` + `fux.runtime.v6`, repo re-ingested `--full`, vendored Node bundle rebuilt (mandatory — the old one pins v2 and refuses the new index). **5 536 byte-identical scan-vs-accelerator comparisons at the default and 5 536 at `anchor = 2.0`, 0 mismatches.** 13 records amended, [pre-registration](regression/2026-09-15-anchor-text/PRE-REGISTRATION.md) frozen.

→ **Next:** 🟢 **W-179 · W-180 · W-181 · W-182 · W-184** — all agent work, no blockers,
inbox still empty. **W-168 is 🟣 until 2026-09-30**: obligations 8 and 10 need documents
findable only through a linker's wording, and those are Codex's
([SR-RS](../records/0133_predictions.md) d23 +
[L11](../records/0012_LAW-11-sealed-answer-key.md)). ⚠ **New: W-184** —
`tools/differential/run.py` dies on a PNG in a source dir, so **the real-corpus
differential arm has been dead while the synthetic one covered for it**; this session's
evidence came through an ad-hoc copy and says so. ⚠ **Two things for Arpit, neither
blocking:** the edge carries **hashed terms, not the anchor string** (L2 — a readable
string for `fux explain` is a second field and a second decision), and a document ranked
#1 on its linkers' wording reports `coverage 0` with the query's word in
`confidence.missing` — honest, deliberate, unmeasured. 🔴 **`tests/test_sr_ownership.py`
is RED and was red before this session**: `SR-LAW-11` needs a `describes` row or a pin
entry. That is the L11 change, **still staged and uncommitted**.
