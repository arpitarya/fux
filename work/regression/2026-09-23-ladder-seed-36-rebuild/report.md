---
type: Report
run: 2026-09-23-ladder-seed-36-rebuild
item: W-215
classification: surface capture
description: "Prompt 4 run as a check after prompt 10 added 14 seed documents (23-36): all eight golden rungs reported STALE, and all eight were rebuilt in place, never wiped, and re-frozen on the 42-document seed. The headline sizes held, ref edges went from 61 to 82 on every rung, and an in-place versus from-scratch build agreed on every manifest and index root."
filed: 2026-09-23
---

# REPORT — the golden ladder, rebuilt on the 42-document seed

**Not a paired run.** No arms, no judged queries, no threshold, and no question
asked of a rung. It is [prompt 4](../../golden/prompts/4-claude-corpus.md) run as
the check it says it is. The check failed, and that failure is what authorises
the rebuild. **This is a surface capture and it files no verdict.**

🔴 **The honour declaration prompt 4 requires.** The rebuild ran in a fresh Opus
subagent whose context had never held a `set-3-u` question. Under `work/golden/`
it read only `seed/` (with `seed/archive/`), `seed-dates.tsv`, `ladder/`,
`README.md` and `prompts/4-claude-corpus.md`. It did not open, list, grep, hash
or stat `questions/` or either spelling of the sealed-key directory
([L11](../../../records/0012_LAW-11-sealed-answer-key.md)). The parent session
that launched it committed `questions/set-3-u.jsonl` (`53137262`) and never read
a value in it. ⚠ **Prompt 4's ordering rule was not kept**, for the same reason
as on 2026-09-21: the questions were on disk first. The honour rule is the whole
of what protects this phase.

## What the check found

| check | result |
|---|---|
| all eight rungs present in `fux-lab` | ✅ |
| `rungs.verify`: every document re-hashed | ✅ 0 problems on all eight |
| nesting | ✅ all seven steps |
| 🔴 **the manifest's `seed/` half against `work/golden/seed/`** | 🔴 **14 documents absent on all eight rungs** (`23-…` to `36-…`); the other 28 unchanged |

**The gate fired before a human did.** After the release push,
`tests/test_golden_ladder_seed.py` failed 8/8 in every CI matrix cell, and the
node-arm job "golden ladder manifests" failed too. Both turned `main` red.

## What was done

- **In place, not rebuilt from scratch.** `build_golden_rung.py` opens with
  `rmtree(rung)`, and the corpora are kept, never wiped. A new driver,
  [`evidence/rebuild_in_place.py`](evidence/rebuild_in_place.py), edits each
  rung's repo directly:
  1. commit the 14 seeds at their `seed-dates.tsv` dates;
  2. `git rm` the ext stream's last 14 documents;
  3. run `fux setup` and re-declare the four sources;
  4. check the skip list, then run `fux ingest --full` and commit;
  5. write `.sha256`, `.index` and `.coverage`.

  The builder and generator are unmodified.
- **The in-place build was cross-checked against a from-scratch one.** All eight
  rungs were also built from nothing with the unmodified builder in a scratch
  directory. The manifest, the coverage file and `index_root_sha256` were
  identical on all eight.
- **Every rung kept its headline size**, the rule since 2026-09-21. Each rung
  above the seed carries 14 fewer generated documents. `rung-10000` stays at the
  ceiling set by [SR-WORK-SCALE](../../../records/0057_WORK-scale.md).
  `rung-seed` is 42.

| rung | docs | archived | superseded | index root |
|---|---|---|---|---|
| rung-seed | 42 | 6 | 6 | `2175d52e92b4…` |
| rung-00100 | 100 | 12 | 12 | `99cbe7131b6b…` |
| rung-00200 | 200 | 22 | 22 | `15019c6564c7…` |
| rung-00500 | 500 | 52 | 52 | `f626be7a064e…` |
| rung-01000 | 1000 | 102 | 102 | `2dc88ccbe6a7…` |
| rung-02000 | 2000 | 202 | 202 | `2cc96c57ab50…` |
| rung-05000 | 5000 | 502 | 502 | `6516e0bc448a…` |
| rung-10000 | 10000 | 1002 | 1002 | `00adc3f059b0…` |

The engine was `3.0.0-alpha.3` at engine commit `2dbe870f`. On every rung, every
declared coverage count equals the indexed count. `ref_edge_census.py` exits 0
with **82 `ref` edges on every rung (was 61)**.

**Validation.** `tests/test_golden_ladder_seed.py` → 10 passed.
`tools/differential/ladder_check.py` → *8 rungs, manifests consistent and nesting
verified*, exit 0. The whole unit and e2e suites are green except this run's own
filing, which this report completes.

The diagnosis and what to watch are in [ANALYSIS.md](ANALYSIS.md).
