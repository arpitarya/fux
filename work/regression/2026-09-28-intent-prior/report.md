---
type: Report
description: "W-168 step 9, the intent → doc-type prior: five arms, `intent_weight ∈ {0.0, 0.1, 0.2, 0.3, 0.5}`, captured on set-4-claude at a copy of the generation-3 `rung-01000` (`b73348d5`), engine `a113b727`, `[doctype]` = the bar's three globs. Hand-offs only: no score and no verdict exist yet."
run: 2026-09-28-intent-prior
item: W-168
classification: informed
filed: 2026-09-28
pre_registration: work/regression/2026-09-28-intent-prior/PRE-REGISTRATION.md
---

# Report: the intent → doc-type prior (`set-4-claude`, `rung-01000` copy)

✅ **Decided on 2026-09-28: PASS by the table at `0.1`, ratified by Arpit the same day.** See [`VERDICT.md`](VERDICT.md). The text below is as it was at scoring.

✅ **Scored 2026-09-28 (Arpit's hand); not decided.** No answer key reached this session.
Below, *changed* means **the ranking moved**, never that it *improved*.

- **Who scores:** Arpit, with `just golden-score work/regression/2026-09-28-intent-prior`, in his own shell. No unlock is needed.
- **Who decides:** a session that did **not** capture these arms runs
  [`evidence/decide.py`](evidence/decide.py), sha256 `8529846567a3…61652da5`. It
  is step 4's decider with the arm names, the set and the tag reading changed,
  plus `primary@1` per intent. It was written before any score existed.

## 🔴 Scored — 2026-09-28, Arpit's hand · `informed`

`just golden-score` → `scores/ip-<w>/rung-01000/set-4-claude.json`, five
complete joins (n = 125, none partial).

| arm | hit@1 | hit@5 | hit@10 | primary@1 | answered unanswerable | evidence quoted |
|---|---:|---:|---:|---:|---:|---:|
| `ip-0.0` | 66 | 104 | 110 | 62 | 11 | 95 |
| `ip-0.1` | 72 | 104 | 110 | 68 | 11 | 96 |
| `ip-0.2` | 74 | 105 | 110 | 70 | 11 | 96 |
| `ip-0.3` | 77 | 105 | 110 | 73 | 11 | 96 |
| `ip-0.5` | 80 | 105 | 110 | 76 | 11 | 97 |

🔴 **These totals are NOT the rule, and this session files no verdict.** The
frozen bar decides on tagged per-query flips against the SR-RS d19 floor
(clause 1) and on **zero** baseline rank-1 losses anywhere (clause 2). A net
total can hide a loss, and only `decide.py` reads the flips. This session
captured the arms, so it may not run it (§What this run may NOT do, item 5).

## 1 · What ran

| | |
|---|---|
| sequence | pre-registration `21b5143e` → build `b3898441` → capture at `a113b727` (build + docs), 2026-09-28 |
| engine | a detached worktree at `a113b727` with its own venv, passed to the harness as `--fux`. **Not the main tree**, which carried another session's uncommitted engine edits |
| source rung | `fux-lab/corpora/golden/rung-01000` at `b73348d5`, as the bar names. **Not written to** |
| the copy | `~/my_programs/fux-lab/arms/runs/ip-base/rung-01000`. **No re-ingest**: the engine reads the rung's index as it stands |
| `doctor --fix` on the copy | wrote the `tune.toml` keys W-225 made required: `rerank_depth`, `rerank_coverage_power`, `rerank_base`, `rerank_span`, `rerank_adjacency`, `intent_weight`, `path_limit`, `citation_overhead`, `table_rows_per_passage`, `[enrich] self_retrieval_k`. It also filled `formats.toml`, `output.toml` and `refusals.toml`, and created `inspect.toml`. Every value is the template's. Full diff: [`evidence/doctor-fix.diff`](evidence/doctor-fix.diff) |
| `[doctype]` | then appended, exactly the bar's three lines: `"*-procedure-*"`, `"*-decision-*"`, `"*-reference-*"` |
| arm copies | `arms/runs/ip-<w>/rung-01000`, each `cp -a` of the base. `diff -r` shows **only `tune.toml`** differing, and only on the `intent_weight` line |
| harness | `golden_run.py --sets 4-claude --arm ip-<w> --engine-commit a113b727 --fux <pinned>`, unchanged |
| questions | 125 per arm; funnel gates on all 125 in every arm |

## 2 · The build check — `ip-0.0` equals the capture the pool was counted on

**125 of 125 ranked lists and 125 of 125 bands** equal the
[2026-09-27 capture](../2026-09-27-golden-set-4-rung-01000/report.md), whose
score gave the pool of 14. Neither the build at `0.0` nor the keys `doctor
--fix` wrote moved anything. That is a check on the build, not an arm: the bar
supplies the precondition from that capture and **forbids stating a delta
against it**.

## 3 · What each arm did (descriptive, `k = 10`)

From [`evidence/describe.py`](evidence/describe.py) → `describe.json`:

| arm | rank 1 changed | of which tagged | order changed | membership changed | median `ask` ms | bands (grounded / partial / weak) |
|---|---:|---:|---:|---:|---:|---|
| `ip-0.0` | — | — | — | — | 169 | 69 / 24 / 32 |
| `ip-0.1` | 6 | 6 | 11 | 1 | 164 | 67 / 24 / 34 |
| `ip-0.2` | 8 | 8 | 13 | 3 | 163 | 73 / 24 / 28 |
| `ip-0.3` | 11 | 11 | 18 | 8 | 163 | 74 / 24 / 27 |
| `ip-0.5` | 14 | 14 | 19 | 12 | 168 | 78 / 24 / 23 |

- **Every rank-1 change is on a tagged question**, at every weight. A question
  with no cue gets no prior, so untagged rank 1 cannot move, and it did not.
  Order and membership changes past rank 1 are on tagged questions too, by the
  same construction.
- ⚠ **At `0.5`, rank 1 moved on 14 questions, the pool's exact size.** That is
  a count of moves, not of wins. A move can put the wrong same-type document
  first, and only the score can tell which it did.
- **The band moves toward `grounded`.** A multiplied rank-1 score widens the
  separation the band reads ([SR-CONFIDENCE](../../../records/0141_confidence.md),
  noted with the build). That is the prior being visible, not evidence that it
  is right.
- **Latency is flat**, 163–169 ms median across arms, on a shared machine.

## 4 · Headroom ([SR-RS](../../../records/0133_predictions.md) d22)

Restated from **this run's baseline arm** once it is scored (d22f).
`decide.py` writes it into `decision.json`. Because `ip-0.0` equals the
2026-09-27 capture, the bar's improvement **14** and regression exposure **66**
should repeat. That is a prediction, not a figure this report claims.

## 5 · Reproduce

```bash
git worktree add --detach <eng> a113b727 && (cd <eng> && uv sync --extra dev)
cp -a ~/my_programs/fux-lab/corpora/golden/rung-01000 ~/my_programs/fux-lab/arms/runs/ip-base/rung-01000
(cd ~/my_programs/fux-lab/arms/runs/ip-base/rung-01000 && <eng>/.venv/bin/fux doctor --fix)
printf '\n[doctype]\n"*-procedure-*" = "procedure"\n"*-decision-*" = "decision"\n"*-reference-*" = "reference"\n' \
    >> ~/my_programs/fux-lab/arms/runs/ip-base/rung-01000/.fux/tune.toml
# each arm: cp -a the base, set `intent_weight = <w>`, then, from <eng>:
python tools/quality-controls/golden_run.py --rung rung-01000 \
    --tree ~/my_programs/fux-lab/arms/runs/ip-<w>/rung-01000 \
    --evidence work/regression/2026-09-28-intent-prior/evidence/ip-<w>/rung-01000 \
    --sets 4-claude --arm ip-<w> --engine-commit a113b727 --fux <eng>/.venv/bin/fux
python3 work/regression/2026-09-28-intent-prior/evidence/describe.py
```

## Authorship

**`classification: informed`, permanently**, for the bar's reasons: set-4-claude
is Claude-authored and was scored before, and the pools were seen before the
bar was written. **This session wrote the bar, built the mechanism and captured
the arms**, so it may not decide them (§What this run may NOT do, item 5). It
read `work/golden/questions/set-4-claude.jsonl` directly and through the
harness, and read `seed/` and the ladder manifest. It read no other path under
`work/golden/`, and it opened no key. It did read Arpit's filed set-4 score
file (ids, ranks, flags, pools) to count the precondition.
