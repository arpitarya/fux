---
type: Pre-Registration
description: "A BASELINE CAPTURE of generation 3's one set — `set-4-claude` (125) — on the rebuilt 68-seed `rung-01000`, one arm, the rung's own engine at the shipped ranking (`anchor = 1.0`, `mined_weight = 0.5`). Not a paired comparison, no verdict, no correctness column: no key reaches this session."
run: 2026-09-27-golden-set-4-rung-01000
item: W-168
rung: rung-01000
status: frozen
filed: 2026-09-27
classification: informed
---

# PRE-REGISTRATION — `set-4-claude`, `rung-01000` (generation-3 ladder)

🔴 **FROZEN, and committed before any number exists**
([SR-RS](../../../records/0133_predictions.md) decision 10b).

## 1 · What this run IS and is NOT

- **IS** [phase 5](../../golden/README.md) for generation 3: the first capture
  of `set-4-claude` on the ladder rebuilt on 2026-09-27
  ([`2026-09-27-ladder-gen3-rebuild`](../2026-09-27-ladder-gen3-rebuild/report.md)).
  W-168 steps 6–10 each count their own pool from the score of these hand-offs;
  a pool below 6 stops that step.
- 🔴 **Is NOT a paired comparison.** One arm, no endpoint, no direction, no
  delta, no verdict. No `VERDICT.md` will exist here.
- 🔴 **No correctness column, and there cannot be one.** No key reaches this
  session by any route, a paste included
  ([L11](../../../records/0012_LAW-11-sealed-answer-key.md)). `just golden-state`
  → `locked`, checked before this file was written. Scoring is
  [`tools/golden-score/score.py`](../../../tools/golden-score/score.py), **started
  by Arpit from his own shell** (`just golden-score <this run>`, set `4-claude`);
  this session does not invoke it.

## 2 · The set

| set | file | author | rows | ids |
|---|---|---|---:|---|
| `set-4-claude` | `work/golden/questions/set-4-claude.jsonl` | Claude (prompt 11, 2026-09-27) | 125 | unique |

Checked before this file was written, **keys only**: every row carries exactly
`{"id", "question"}`, 125 ids, all unique. One file in, one pair of files out.

## 3 · The engine — the rung's own, so no re-ingest and no `doctor --fix`

| | `ladder/rung-01000.index` | this run |
|---|---|---|
| engine | `fux 3.0.0-alpha.5` | **`fux 3.0.0-alpha.5`** |
| engine_commit | `80495b449f063ba69c42a7a82f3a9f0880043892` | **`80495b449f063ba69c42a7a82f3a9f0880043892`** |
| rung_head_commit | `b73348d56edf5c0e16aa6f344ad629ba1dd00c37` | `b73348d5…` (checked) |

Pinned as a detached `git worktree` at that sha with its own venv, outside the
repository. **Both match, so phase 5's rule is: use the rung's index, do not
re-ingest.**

⚠ **Why not HEAD with `fux doctor --fix`, as W-168's next-step line said.** HEAD
(`f50eb83a`) carries W-225 stages 2–3b, which refuse this rung until `doctor
--fix` writes the missing `tune.toml` keys — and that would **edit a frozen
rung's committed config** to run it. The pin predates stage 2, ranks what the
rung was built with, and already includes step 4 (`8d401423` is its ancestor).
`git log 80495b44..HEAD -- src/fux` is W-225 stages 2/3a/3b (config
requirement), W-226 (schemas moved) and `serve` — no ranking path. The rows are
stamped with the pin regardless.

Checked at freezing: `rungs.verify('rung-01000', …, documents_too=True)` → **0
problems**; `ladder_check.py` → *8 rungs, manifests consistent and nesting
verified*. The rung's worktree carries one untracked `fux.toml`, written by the
builder at build time on every rung; nothing is edited.

## 4 · Ranking configuration — the rung's committed `.fux/tune.toml`, unedited

`[bm25f] b = 0.15`, **`anchor = 1.0`** (step 1, shipped) · `[ranking]
rerank_weight = 0.0`, `expand_weight = 0.2` (a no-op without `--expand`),
**`mined_weight = 0.5`** (step 4, shipped) · `[graph] ask_boost = true`,
`ask_related = true` · `[confidence] separation_floor = 0.1`,
`doc_coverage_floor = 0.0`.

⚠ **This is the first golden capture at the shipped combination** `anchor = 1.0`
+ `mined_weight = 0.5`; step 4's verdict names that combination unmeasured.
This run does not measure it either — it has no second arm — but it is the
baseline any later step compares against.

## 5 · The calls

```
fux ask    "<question>" --json --band --why --top 10
fux answer "<question>" --json
```

125 questions × 2 verbs = 250 calls, via
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
omitted. The structural ceiling for a later paired run is **125**. The usable
pool, and each step's own pool (6 SDM · 7 MMR · 8 authority · 9 intent · 10
section units), lives in the key and is the first thing a score of these
hand-offs can state.

## 8 · Classification — `informed`, permanently

Author and runner are the same model family, and every golden number is
`informed` from the first unlock (2026-09-22). **This session reads the question
text of `set-4-claude` as it passes through `golden_run.py`** and so may not build
a rung afterwards (SR-WORK-TESTDATA A23); it builds none. It is not the W-227
session.

## 9 · May NOT claim

Whether an answer is right · any `hit@k`, `recall@k` or keyed metric · a
comparison with any number filed on the generation-2 ladder · a comparison with
another set · the word *blind*.

## 10 · Reproduce

```bash
git worktree add <tmp>/engine-pin 80495b449f063ba69c42a7a82f3a9f0880043892 --detach
cd <tmp>/engine-pin && uv venv .venv && uv pip install --python .venv/bin/python -e .
cd ~/my_programs/fux
.venv/bin/python tools/quality-controls/golden_run.py --rung rung-01000 --sets 4-claude \
    --fux <tmp>/engine-pin/.venv/bin/fux \
    --engine-commit 80495b449f063ba69c42a7a82f3a9f0880043892 \
    --dest work/regression/2026-09-27-golden-set-4-rung-01000
```
