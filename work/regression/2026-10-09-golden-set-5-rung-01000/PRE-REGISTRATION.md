---
type: Pre-Registration
description: "A BASELINE CAPTURE of generation 4's set — `set-5-claude` (90) — on the gen-4 `rung-01000`, one arm, the rung's own engine `ba1c0e44` at the rung's committed ranking. Not a paired comparison, no verdict, no correctness column: no key reaches this session. Its score, run by Arpit, counts the `step10_section` pool W-240 and W-236 wait on."
run: 2026-10-09-golden-set-5-rung-01000
item: W-240
rung: rung-01000
status: frozen
filed: 2026-10-09
classification: informed
---

# PRE-REGISTRATION — `set-5-claude`, `rung-01000` (generation-4 ladder)

🔴 **FROZEN, and committed before any number exists**
([SR-RS](../../../records/0133_predictions.md) decision 10b).

## 1 · What this run IS and is NOT

- **IS** [phase 5](../../golden/README.md) for generation 4: the first capture
  of `set-5-claude` on the ladder rebuilt on 2026-10-05
  ([`2026-10-05-ladder-gen4-rebuild`](../2026-10-05-ladder-gen4-rebuild/report.md)).
  W-240's done-condition is a **`step10_section` pool ≥ 6**, counted from the
  score of these hand-offs; W-236 Part B waits on it.
- 🔴 **Is NOT a paired comparison.** One arm, no endpoint, no direction, no
  delta, no verdict. No `VERDICT.md` will exist here.
- 🔴 **No correctness column, and there cannot be one.** No key reaches this
  session by any route, a paste included
  ([L11](../../../records/0013_LAW-11-sealed-answer-key.md)). `just golden-state`
  → `locked`, checked before this file was written. Scoring is
  [`tools/golden-score/score.py`](../../../tools/golden-score/score.py), **started
  by Arpit from his own shell** (`just golden-score <this run>`, set `5-claude`);
  this session does not invoke it.
- **Not the rebuild session.** The gen-4 rebuild (2026-10-05) was held to
  `seed/` and never opened `questions/`; this session is a different one, as
  W-240 requires.

## 2 · The set

| set | file | author | rows | ids |
|---|---|---|---:|---|
| `set-5-claude` | `work/golden/questions/set-5-claude.jsonl` | Claude (prompt 12, run by Arpit 2026-10-03) | 90 | unique |

Checked before this file was written, **keys only**: every row carries exactly
`{"id", "question"}`, 90 ids, all unique.

## 3 · The engine — the rung's own, so no re-ingest and no `doctor --fix`

| | `ladder/rung-01000.index` | this run |
|---|---|---|
| engine | `fux 3.0.0-alpha.11` | **`fux 3.0.0-alpha.11`** |
| engine_commit | `ba1c0e445fb5562e566ad93d7f23632efdfb556e` | **`ba1c0e44…`** — a detached `git worktree` with its own venv, outside the repository |
| rung_head_commit | `e776146fc4c51c5801c47144a058cf0eb8644145` | `e776146f…` (checked) |

**Both match, so phase 5's rule is: use the rung's index, do not re-ingest.**
HEAD has moved 31 files under `src/fux/` since the freeze (18 commits), which is
why the pin, not HEAD, ranks.

Checked at freezing: `rungs.verify('rung-01000', …, documents_too=True)` → **0
problems** (`[]`). The rung's tree carries one untracked `fux.toml`, written by
the builder on every rung; nothing is edited.

## 4 · Ranking configuration — the rung's committed `.fux/tune.toml`, unedited

`[bm25f] b = 0.15`, `anchor = 1.0` · `[ranking] rerank_weight = 0.0`,
`expand_weight = 0.2` (a no-op without `--expand`), `mined_weight = 0.5`,
`intent_weight = 0.1` · `[graph] ask_boost = true`, `ask_related = true` ·
`[confidence] separation_floor = 0.1`, `doc_coverage_floor = 0.0`. No section
weight exists in this engine — SR-SECTIONS is proposed and unbuilt — so this is
the **document-level baseline** W-236 Part B will be compared against.

## 5 · The calls

```
fux ask    "<question>" --json --band --why --top 10
fux answer "<question>" --json
```

90 questions × 2 verbs = 180 calls, via
[`golden_run.py`](../../../tools/quality-controls/golden_run.py). `--why` is
required ([SR-WORK-QUALITY](../../../records/0056_WORK-quality.md) decision 13);
the hand-off keeps its five gate integers and nothing else.

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
omitted. The structural ceiling for a later paired run is **90**. The
`step10_section` pool, and every other step's pool, lives in the key and is the
first thing Arpit's score of these hand-offs can state. **W-240 is done when that
count is ≥ 6**; under 6, W-240 ruling 1 applies (lengthen seed `64`–`66` with
off-question sections), not this session's judgement.

## 8 · Classification — `informed`, permanently

Author and runner are the same model family. **This session reads the question
text of `set-5-claude` as it passes through `golden_run.py`**, and so may not
build a rung afterwards ([SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md)
A23); it builds none.

## 9 · May NOT claim

Whether an answer is right · any `hit@k`, `recall@k` or keyed metric · a
comparison with any number filed on the generation-3 ladder · a comparison with
another set · the word *blind*.

## 10 · Reproduce

```bash
git worktree add <tmp>/engine-pin ba1c0e445fb5562e566ad93d7f23632efdfb556e --detach
cd <tmp>/engine-pin && uv venv .venv && uv pip install --python .venv/bin/python -e .
cd ~/my_programs/fux
.venv/bin/python tools/quality-controls/golden_run.py --rung rung-01000 --sets 5-claude \
    --fux <tmp>/engine-pin/.venv/bin/fux \
    --engine-commit ba1c0e445fb5562e566ad93d7f23632efdfb556e \
    --dest work/regression/2026-10-09-golden-set-5-rung-01000
```
