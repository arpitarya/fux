---
type: Report
run: 2026-09-27-golden-set-4-rung-01000
item: W-168
classification: informed
description: "The first capture of generation 3's set-4-claude on the rebuilt 68-seed rung-01000: 125 questions, 250 calls, the rung's own engine 80495b44 with no re-ingest, at the shipped anchor 1.0 + mined_weight 0.5, funnel gates on every row. Descriptive only. The hand-off is what Arpit scores."
filed: 2026-09-27
---

# REPORT — `set-4-claude` baseline, `rung-01000` (generation-3 ladder)

**A surface capture, not a paired run.** It files no verdict and computes no
correctness figure. The frozen bar is [PRE-REGISTRATION.md](PRE-REGISTRATION.md)
(`0ce0b845`, committed before any row existed). Every number here is
🔴 **`informed`**: author and runner are the same model family.

## 🔴 What Arpit does with it

```bash
just golden-score work/regression/2026-09-27-golden-set-4-rung-01000
```

- **Score this file:** `evidence/handoff-set-4-claude.jsonl` (flat layout). The
  rung comes from the pre-registration's `rung: rung-01000` line.
  `tools/golden-score/handoffs.py`, which reads no key, lists it as
  `single · rung-01000 · 4-claude`. The key it expects is `set-4-claude.jsonl`
  in the sealed directory.
- **No agent runs it** ([L11](../../../records/0012_LAW-11-sealed-answer-key.md)).
- **What the score settles:** each W-168 step's own pool on generation 3 —
  6 SDM, 7 MMR, 8 authority, 9 intent, 10 section units. **A pool below 6 stops
  that step.** Counting the pools needs the key's `relevant` / `primary` / facet
  fields joined against these rows, so it follows the score and is not done here.

## The run

| | |
|---|---|
| rung | `rung-01000`, 1 000 documents, 68 of them seed. `rungs.verify(documents_too=True)` → 0 problems; `ladder_check.py` → 8 rungs consistent |
| engine | `fux 3.0.0-alpha.5` at `80495b44`, a pinned worktree. **It equals the rung's stamp, so there was no re-ingest and no `doctor --fix`** |
| repo HEAD at capture | `0ce0b845` (the pre-registration commit) |
| calls | `ask --json --band --why --top 10` + `answer --json` per question, via `golden_run.py` |
| `tune.toml` | the rung's committed file, unedited: **`anchor = 1.0`, `mined_weight = 0.5`**, `b = 0.15`, `rerank_weight = 0.0` |
| wall clock | 2026-09-27, about 23:05–23:11 IST, on a shared machine; another session had uncommitted serve work in the main tree |

⚠ **Why the pin and not HEAD with `doctor --fix`.** W-168's next-step line
said to run `doctor --fix` on the rung. That was written for HEAD, whose W-225
stage 2 refuses the rung. Running it would have written keys into a frozen rung's
config. The pin predates stage 2, is the engine the rung was built with, and
already carries step 4. See PRE-REGISTRATION §3.

## Counts — [`evidence/describe.py`](evidence/describe.py) → [`describe.txt`](evidence/describe.txt)

| | `set-4-claude` |
|---|---:|
| questions | 125 |
| rows carrying funnel gates | **125 / 125** |
| empty ranked lists | 0 |
| ranked lists shorter than 10 | 0 |
| answers declined (empty `answer_text`) | 0 |
| answers with no citation | 0 |
| `answerable: true` | 125 |
| band `grounded` | 69 |
| band `partial` | 24 |
| band `weak` | 32 |
| band `none` | 0 |
| rank-1 document under `seed/` | 124 |
| rank-1 document archived | 2 |
| `source` | `refer` on all 125 |
| citation freshness | `current` on all 125 |

⚠ **The rank-1 rows describe WHERE fux looked, not whether it was right.** A
rank-1 `ext/` document may be a hard negative winning, or the answer to a
question with no answer in the seed. Only the key can say which.

⚠ **`answerable` is `band != none`** ([SR-CONFIDENCE](../../../records/0141_confidence.md)
decision 3a). So 125 of 125 `true` restates the band row, and band `none` never
fired. Abstention on this set's unanswerable questions is therefore not measured
by fux's flag. The key's own `answerable` field measures it.

⚠ **The band distribution is not comparable** with the generation-2 captures.
The ladder, the set and the ranking configuration are all different: `anchor`
and `mined_weight` were `0.0` on 2026-09-24.

## Latency — descriptive, shared machine, not a benchmark figure

| slowest `ask` (ms) | slowest `answer` (ms) |
|---|---|
| `s4u-001` 211 · `s4u-004` 199 · `s4u-022` 188 | `s4u-113` 164 · `s4u-010` 159 · `s4u-050` 155 |

## What looked wrong

Nothing structural. Every row has ten results, a band, five gate integers, a
`refer` answer and a `current` citation.

## May not claim

Whether any answer is right; any keyed metric; any step's pool; a comparison
with the generation-2 ladder or with another set; the word *blind*.

## Reproduce

[PRE-REGISTRATION.md](PRE-REGISTRATION.md) §10, then `evidence/describe.py`.
