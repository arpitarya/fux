---
type: Report
run: 2026-09-27-ladder-gen3-rebuild
item: W-168
classification: surface capture
description: "The golden ladder rebuilt on generation 3's 68-document seed, with the seed's git history replayed (T11): all eight rungs were stale, all eight were rebuilt from scratch by the unmodified builder at engine 80495b44, and all eight froze with every coverage count equal to its declaration. The generation-2 rungs were moved aside, not deleted."
filed: 2026-09-27
---

# REPORT — the golden ladder, rebuilt for generation 3

**Not a paired run.** It has no arms, no judged queries and no threshold, and
no question was asked of a rung. It is [phase 4](../../golden/README.md) of the
golden process, run because generation 3 added seeds 37–62 and a git history.
**This is a surface capture. It files no verdict and has no per-query rows.**

## Authorship

🔴 **The honour declaration ([SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md) A23).**
One Claude Code session (Opus 5.5) did the whole rebuild. Its context has never
held a question of any set. Under `work/golden/` it read only these:
- `seed/` (with `seed/archive/`), `seed-dates.tsv`, `seed-history.tsv` and
  `seed-history/`, through the builder;
- `ladder/`;
- `README.md`.

It did not open, list, grep, hash or stat `questions/`. It did not touch either
spelling of the sealed-key directory ([L11](../../../records/0012_LAW-11-sealed-answer-key.md)).
One of its shell commands named that directory in a `grep -v` filter. The guard
hook refused the command before it ran, so nothing was opened.

⚠ **The ordering rule was not kept**, as on 2026-09-21 and 2026-09-23.
`questions/set-4-claude.jsonl` was committed (`363a8b8c`) before this build. The
honour rule is the whole of what protects this phase. The generator, its seed and
the builder are unmodified and committed, so anyone can re-derive the bytes.

| artifact | author | could reach |
|---|---|---|
| `seed/` 37–62, `seed-history*` | the designated generation-3 chat (prompt 11) | its own questions |
| `build_golden_rung.py`, `make_golden_ext.py` (unmodified) | earlier sessions, 2026-09-12 / 2026-09-25 | none |
| [`evidence/build_from_worktree.py`](evidence/build_from_worktree.py), [`evidence/new_seed_name_leaks.py`](evidence/new_seed_name_leaks.py) | this session | none |

## What the check found

`tests/test_golden_ladder_seed.py` failed **8 of 8**: every rung lacked seeds
37–62. The 42 older seeds were unchanged.

## What was done

- **From scratch, not in place.** The seed's history now interleaves commits by
  nine authors across 2025–2026. An in-place edit cannot put those commits under
  a rung's existing history. So each rung was rebuilt by the **unmodified**
  `build_golden_rung.py`, which replays the history through
  [`replay.py`](../../../tools/golden-history/replay.py).
- 🔴 **The generation-2 rungs were KEPT.** Corpora are never wiped (Arpit,
  2026-09-12). Before the builder's `rmtree` could reach them, all eight were
  moved to `fux-lab/corpora/golden-gen2/`. That is the ladder the 2026-09-24
  capture and the step-4 arms name.
- **From a clean worktree at `80495b44`.** The main tree held other sessions'
  staged, uncommitted W-225/W-226 changes. A rung stamped with a commit its
  engine did not match is the W-186 defect. The driver points the builder's four
  constants at the worktree and adds the `engine_commit:` line (W-186). It
  changes nothing else.

| rung | docs | seed | archived | superseded | mtime | build | index root |
|---|---:|---:|---:|---:|---:|---:|---|
| rung-seed | 68 | 68 | 6 | 6 | 68 | ~17 s | `1469d9630805…` |
| rung-00100 | 100 | 68 | 9 | 9 | 100 | 23 s | `4a42e13c6c12…` |
| rung-00200 | 200 | 68 | 19 | 19 | 200 | 41 s | `de571c2e3fcd…` |
| rung-00500 | 500 | 68 | 49 | 49 | 500 | 91 s | `424338439d70…` |
| rung-01000 | 1 000 | 68 | 99 | 99 | 1 000 | 163 s | `103430af5974…` |
| rung-02000 | 2 000 | 68 | 199 | 199 | 2 000 | 333 s | `6abba0432be9…` |
| rung-05000 | 5 000 | 68 | 499 | 499 | 5 000 | 621 s | `e1faadf68d67…` |
| rung-10000 | 10 000 | 68 | 999 | 999 | 10 000 | 766 s | `f9e4214f1115…` |

- Engine `fux 3.0.0-alpha.5` at commit `80495b44`. **Every declared count equals
  the indexed count on every rung.**
- **History (T11) on every rung:** 12 documents with history, 34 commits, 9
  authors, and at most 4 authors on one document. On `rung-01000`,
  `seed/40-procedure-dry-ice-handling.md` has 4 commits by 3 authors, dated
  2025-04-14 to 2025-11-20.
- **Validation:**
  - `tests/test_golden_ladder_seed.py`: 10 passed.
  - `tools/differential/ladder_check.py`: *8 rungs, manifests consistent and
    nesting verified*, exit 0.
  - `ref_edge_census.py`: **82 `ref` edges on every rung**, unchanged.
    Generation 3 adds history, not links.
- **Suites, in the worktree at `80495b44` + these records:**
  - e2e: 151 passed.
  - unit: 5 738 passed, 2 failed. Both are at `80495b44` itself: the
    `0159_constants.md` Components block and its owns-hash, left by W-225
    stage 1 and untouched here. The 8 ladder failures are gone.

The diagnosis, the leak search and what to watch are in [ANALYSIS.md](ANALYSIS.md).
