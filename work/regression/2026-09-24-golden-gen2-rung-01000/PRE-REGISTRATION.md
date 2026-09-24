---
type: Pre-Registration
description: "A BASELINE CAPTURE of generation 2's two sets — `set-2-u` (125) and `set-3-u` (80) — on the rebuilt 42-seed `rung-01000`, one arm, the rung's own engine. Not a paired comparison, no verdict, no correctness column: no key reaches this session."
run: 2026-09-24-golden-gen2-rung-01000
item: W-215
rung: rung-01000
status: frozen
filed: 2026-09-24
classification: informed
---

# PRE-REGISTRATION — generation-2 baseline, `rung-01000` (42-seed ladder)

🔴 **FROZEN, and committed before any number exists**
([SR-RS](../../../records/0133_predictions.md) decision 10b).

## 1 · What this run IS and is NOT

- **IS** the first capture of both generation-2 sets on the ladder rebuilt on
  2026-09-23 ([`2026-09-23-ladder-seed-36-rebuild`](../2026-09-23-ladder-seed-36-rebuild/report.md)).
  Every golden number filed before that rebuild names a ladder that no longer
  exists — including [`2026-09-22-golden-set-2u-rung-01000`](../2026-09-22-golden-set-2u-rung-01000/report.md)
  and the RM3 arms — so W-215 item 1 (*does generation 2 hold questions today's
  engine fails?*) and every W-168 pool count need this one.
- 🔴 **Is NOT a paired comparison.** One arm, no endpoint, no direction, no
  delta, no verdict. No `VERDICT.md` will exist here.
- 🔴 **No correctness column, and there cannot be one.** No key reaches this
  session by any route, a paste included
  ([L11](../../../records/0012_LAW-11-sealed-answer-key.md)). `just golden-state`
  → `locked`, checked before this file was written. Scoring is
  [`tools/golden-score/score.py`](../../../tools/golden-score/score.py), **started
  by Arpit from his own shell**; this session does not invoke it.

## 2 · The sets — kept apart at every step

| set | file | author | rows | ids |
|---|---|---|---:|---|
| `set-2-u` | `work/golden/questions/set-2-u.jsonl` | Claude | 125 | `s2u-…` |
| `set-3-u` | `work/golden/questions/set-3-u.jsonl` | Claude (prompt 10) | 80 | `s3u-…` |

Checked before this file was written, **keys only**: every row carries exactly
`{"id", "question"}`, ids unique within each set. One file per set in, one pair of
files per set out, never pooled.

## 3 · The engine — the rung's own, so no re-ingest

| | `ladder/rung-01000.index` | this run |
|---|---|---|
| engine | `fux 3.0.0-alpha.3` | **`fux 3.0.0-alpha.3`** |
| engine_commit | `2dbe870f66a87ec65a6483078fc64899ee10b72c` | **`2dbe870f66a87ec65a6483078fc64899ee10b72c`** |

Pinned as a detached `git worktree` at that sha with its own venv, outside the
repository. **Both match, so prompt 5's rule says use the rung's index and do not
re-ingest.** ⚠ HEAD (`ed8e0bee`, alpha.4) differs from the pin only in
`__init__.py`'s version string, `serve/__init__.py` and `node/src/verbs/mcp.mjs`
— no retrieval path — which is why the rung's engine and HEAD rank alike; the
rows are stamped with the pin regardless.

Checked at freezing: `rungs.verify('rung-01000', …, documents_too=True)` → **0
problems**; `ladder_check.py` → *8 rungs, manifests consistent and nesting
verified*.

## 4 · Ranking configuration — the rung's committed `.fux/tune.toml`, unedited

`[bm25f] b = 0.15`, `anchor = 0.0` · `[ranking] rerank_weight = 0.0`,
`expand_weight = 0.2` (a no-op without `--expand`), **`rm3_weight` absent → its
`0.0` default** (step 5 filed FAIL) · `[graph] ask_boost = true`,
`ask_related = true` · `[confidence] separation_floor = 0.1`.

## 5 · The calls

```
fux ask    "<question>" --json --band --why --top 10
fux answer "<question>" --json
```

205 questions × 2 verbs = 410 calls, via
[`golden_run.py`](../../../tools/quality-controls/golden_run.py).
`--why` is required ([SR-WORK-QUALITY](../../../records/0056_WORK-quality.md)
decision 13); the hand-off keeps its five gate integers and nothing else.

## 6 · The metrics — descriptive only, `k = 10`

| # | claim | computed from |
|---|---|---|
| S1 | decline rate | `answer` payload empty |
| S2 | band distribution | `confidence.band` |
| S3 | empty ranked lists | `len(ranked) == 0` |
| S4 | funnel-gate capture rate | `gates` present on the row |
| S5 | latency tail | wall clock — ⚠ shared machine, **not a benchmark figure** |

## 7 · Headroom ([SR-RS](../../../records/0133_predictions.md) decision 22)

**Undefined in both directions**, because the run is unpaired — disclosed, not
omitted. The structural ceiling for a later paired run is **125** (`set-2-u`) and
**80** (`set-3-u`). The usable pool lives in the key and is the first thing a
score of these hand-offs can state.

## 8 · Classification — `informed`, permanently

Author and runner are the same model family, and every golden number is
`informed` from the first unlock (2026-09-22). **This session read the question
text of both sets as it passed through `golden_run.py`** and so may not build a
rung afterwards (prompt 4); it builds none.

## 9 · May NOT claim

Whether an answer is right · any `hit@k`, `recall@k` or keyed metric · a
comparison with any number filed before 2026-09-23's rebuild · a pooled figure
across the two sets · the word *blind*.

## 10 · Reproduce

```bash
git worktree add <tmp>/engine-pin 2dbe870f66a87ec65a6483078fc64899ee10b72c --detach
cd <tmp>/engine-pin && uv venv .venv && uv pip install --python .venv/bin/python -e .
cd ~/my_programs/fux
.venv/bin/python tools/quality-controls/golden_run.py --rung rung-01000 --sets 2-u,3-u \
    --fux <tmp>/engine-pin/.venv/bin/fux \
    --engine-commit 2dbe870f66a87ec65a6483078fc64899ee10b72c \
    --dest work/regression/2026-09-24-golden-gen2-rung-01000
```
