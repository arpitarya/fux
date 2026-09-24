---
type: Report
run: 2026-09-24-golden-gen2-rung-01000
item: W-215
classification: informed
description: "The first capture of both generation-2 sets on the rebuilt 42-seed rung-01000: 205 questions, 410 calls, the rung's own engine 2dbe870f with no re-ingest, funnel gates on every row. Descriptive only. The two hand-offs are what Arpit scores."
filed: 2026-09-24
---

# REPORT — generation-2 baseline, `rung-01000` (42-seed ladder)

**A surface capture, not a paired run.** It files no verdict and computes no
correctness figure. The frozen bar is [PRE-REGISTRATION.md](PRE-REGISTRATION.md)
(`ca1accf9`, committed before any row existed). Every number here is
🔴 **`informed`**: author and runner are the same model family.

## 🔴 What Arpit does with it

```bash
just golden-score work/regression/2026-09-24-golden-gen2-rung-01000
```

- **Score these two files:** `evidence/handoff-set-2-u.jsonl` and `evidence/handoff-set-3-u.jsonl`.
- The rung comes from the pre-registration's `rung: rung-01000` line (W-218).
- **No agent runs it** ([L11](../../../records/0012_LAW-11-sealed-answer-key.md)).
- **What the score settles:**
  - [W-215](../../../archive/open/W-215-generation-2-corpus.md) item 1: does generation 2 hold questions today's engine fails?
  - every W-168 pool count on the ladder as it now is.

## 🔴 SCORED 2026-09-24 (Arpit's hand, `just golden-score`) — `informed`

Scores: `scores/single/rung-01000/set-2-u.json` · `set-3-u.json`. Both are
complete (`partial: false`), with no missing hand-off rows and no missing key
lines. Per set, never pooled:

| of the answerable questions | `set-2-u` (112 of 125) | `set-3-u` (72 of 80) |
|---|---:|---:|
| `hit@1` | 50 | 41 |
| `primary@1` | 36 | 18 |
| `hit@5` | 91 | 68 |
| `hit@10` | 101 | 70 |
| **miss rank 1, target in the top 10** (a reranker can reorder these) | **51** | **29** |
| miss rank 1, target not in the top 10 | 11 | 2 |
| miss `hit@5` | 21 | 4 |

⚠ **`hit@10` is the deepest rank known**, because the capture asked
`--top 10`, so the scorer's `hit@20` and `hit@50` equal it by construction.
**13 and 8 questions are unanswerable**, and fux answered every one of them.
Under W-214 that is by design (band `none` never fired), so abstention is not
measured here.

**Each W-168 step's own pool.** The tags are computed from question text and
`seed/` alone ([`evidence/step_pools.py`](evidence/step_pools.py) →
[`evidence/step-pools.txt`](evidence/step-pools.txt)). *Winnable* means a miss
that is in the top 10, or absent from it.

| step | `set-2-u` winnable at rank 1 · at rank 5 | `set-3-u` winnable at rank 1 · at rank 5 | vs the floor of 6 |
|---|---|---|---|
| 1 · anchor text | 5 · 2 | **14** · 2 | only set-3-u, at rank 1 |
| 2 · identifier (now W-205) | 0 · 0 | 1 · 0 | never |
| 4 · corpus-mined expansion | 0 · 0 | **10** · 0 | only set-3-u, at rank 1 |
| 9 · intent (draft I1 lexicon) | 2 · 0 | 1 · 0 | **never — stops before build** |

## The run

| | |
|---|---|
| rung | `rung-01000`, 1 000 documents, 42 of them seed — verified against `ladder/rung-01000.sha256`, 0 problems |
| engine | `fux 3.0.0-alpha.3` at `2dbe870f`, a pinned worktree — **equal to the rung's stamp, so no re-ingest** |
| repo HEAD at capture | `ca1accf9` (the pre-registration commit) |
| calls | `ask --json --band --why --top 10` + `answer --json` per question |
| `tune.toml` | the rung's committed file, unedited; `anchor = 0.0`, `rm3_weight` absent (`0.0`) |

## Counts, per set — never pooled

| | `set-2-u` | `set-3-u` |
|---|---:|---:|
| questions | 125 | 80 |
| rows carrying funnel gates | **125 / 125** | **80 / 80** |
| empty ranked lists | 0 | 0 |
| ranked lists shorter than 10 | 0 | 0 |
| answers declined (empty `answer_text`) | 0 | 0 |
| answers with no citation | 0 | 0 |
| `answerable: true` | 125 | 80 |
| band `grounded` | 41 | 22 |
| band `partial` | 56 | 48 |
| band `weak` | 28 | 10 |
| band `none` | 0 | 0 |
| rank-1 document under `seed/` | 116 | 80 |
| rank-1 document archived | 5 | 0 |

⚠ **The two rank-1 rows describe WHERE fux looked, not whether it was right.**
Every question is about the seed. A rank-1 `ext/` document is a hard negative
winning, or a question with no answer, and only the key says which.

⚠ **`answerable` is `band != none`** ([SR-CONFIDENCE](../../../records/0141_confidence.md)
decision 3a, W-214), so 205 of 205 `true` restates the band row above. It is not
a separate finding.

## Latency — descriptive, shared machine, not a benchmark figure

| | slowest `ask` (ms) | slowest `answer` (ms) |
|---|---|---|
| `set-2-u` | `s2u-001` 233 · `s2u-116` 194 · `s2u-011` 186 | `s2u-038` 163 · `s2u-039` 153 · `s2u-001` 150 |
| `set-3-u` | `s3u-075` 170 · `s3u-038` 159 · `s3u-021` 158 | `s3u-045` 149 · `s3u-075` 143 · `s3u-046` 133 |

## What looked wrong

Nothing structural: every row has ten results, a band and five gate integers.
**The `set-2-u` rows are NOT comparable** with
[`2026-09-22-golden-set-2u-rung-01000`](../2026-09-22-golden-set-2u-rung-01000/report.md).
That run used the 28-seed ladder and the alpha.2 engine, before W-214.

## May not claim

Whether any answer is right; any keyed metric; a pooled figure; the word *blind*.

## Reproduce

[PRE-REGISTRATION.md](PRE-REGISTRATION.md) §10.
