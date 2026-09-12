---
type: Pointer
description: "One line: the current state and the immediate next step. Overwritten every session."
---

✓ **THE TREE IS COMMITTED — all of it, including the four files `6f518c6` held back.** `src/fux/config.py`, the deletion of `config.schema.json`, `src/fux/setup.py`, `src/fux/store/fuxdir.py`.
🔴 **The holdback's premise was wrong, and that is the finding.** It said the five owning records were untouched; they were **already written and already committed** (`24c0a3d`, `6f518c6`) — ADR-CONFIG decisions 13/14/15, ADR-DOTFUX's `.agents/skills` and Node-vendoring text, the `keep`/`ttl`/`enrich` key rows. **The code was what was missing**, so for two commits five accepted records described behaviour the engine did not have — a reader checking `dirs_fil` against decision 14 was told it errors, and it did not.
⚠ **A record AHEAD of its code reads as authority exactly as one behind it does, and `tests/test_adr_freshness.py` sees neither** — it checks an owning record was *touched*, never what it says. Recorded in [ADR-CONFIG](../docs/adr/0113_config.md) after decision 15. **W-83 with the halves swapped; first occurrence, not gated.**
⚠ Both suites run whole after the change: `tests` and `tests_e2e` green, `node --test` green. `test_working_tree_is_not_mid_violation` is **no longer red** — the working tree is clean.
🔴 **Nothing agent-side is unblocked by this.** Ten 🔴 rows, all filed 2026-09-12: W-143 (four priors answered NO) and the `weak`/`answerable` ruling unblock the most.
⚠ Arpit, 2026-09-12: the built corpora in fux-lab and fux-benchmark are KEPT and reused — never wiped.
