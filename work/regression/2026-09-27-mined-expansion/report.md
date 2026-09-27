---
type: Report
description: "W-168 step 4, corpus-mined expansion: five arms, `mined_weight ∈ {0.0, 0.1, 0.2, 0.3, 0.5}`, captured on `set-3-u` at a re-ingested copy of `rung-01000` (`9cdde333`), engine `f8b21bd5`. Hand-offs only: no score and no verdict exist yet."
run: 2026-09-27-mined-expansion
item: W-168
classification: informed
filed: 2026-09-27
pre_registration: work/regression/2026-09-27-mined-expansion/PRE-REGISTRATION.md
---

# Report: corpus-mined expansion (`set-3-u`, `rung-01000` copy)

✅ **Scored and decided on 2026-09-27: PASS by the table at `0.5`**, awaiting Arpit's ratification. See [`VERDICT.md`](VERDICT.md). The text below is as it was at capture.

🔴 **Captured, not scored, and not decided.** No answer key reached this session.
Below, *changed* means **the ranking moved**, never that it *improved*.

- **Who scores:** Arpit, with `just golden-score work/regression/2026-09-27-mined-expansion`, in his own shell (no unlock).
- **Who decides:** a session that did **not** capture these arms runs [`evidence/decide.py`](evidence/decide.py). It is the W-221 decider with only the arm names, the set and the tags changed, and it was written before any score existed.

## 1 · What ran

| | |
|---|---|
| sequence | pre-registration `02d6db94` → build `f8b21bd5` → capture, 2026-09-27 |
| source rung | `fux-lab/corpora/golden/rung-01000` at `9cdde333`, as the bar names. **Not written to.** |
| the copy | `~/my_programs/fux-lab/arms/runs/mx-base/rung-01000`, re-ingested `--full` at `f8b21bd5` → `fux.index.v5`. Two full ingests: one hash, `3b82fb39…` |
| what the re-ingest changed | **only `abbr`**, on 8 of 1 000 records; every other field of every record equals the rung's committed v4 record. The table holds **9 pairs**, the count the bar predicted |
| arm copies | `arms/runs/mx-<w>/rung-01000`, each `cp -a` of the copy. `.fux/index` is `diff -r` identical across all five; each `tune.toml` differs only in the added `mined_weight` line. The rung's own tune is kept (`anchor = 0.0`, graph tier on), as the bar holds it |
| harness | `golden_run.py --sets 3-u --arm mx-<w> --engine-commit f8b21bd5`, unchanged |
| questions | 80 per arm; the funnel gates captured on all 80 in every arm |

## 2 · What each arm did (descriptive, `k = 10`)

From [`evidence/describe.py`](evidence/describe.py) → `describe.json`:

| arm | rank 1 changed | of which tagged | order changed | membership changed | median `ask` ms | bands (grounded / partial / weak) |
|---|---:|---:|---:|---:|---:|---|
| `mx-0.0` | — | — | — | — | 150 | 22 / 48 / 10 |
| `mx-0.1` | 2 | 2 | 14 | 3 | 164 | 23 / 48 / 9 |
| `mx-0.2` | 5 | 5 | 19 | 5 | 157 | 21 / 48 / 11 |
| `mx-0.3` | 6 | 6 | 20 | 6 | 163 | 21 / 48 / 11 |
| `mx-0.5` | 7 | 7 | 20 | 11 | 159 | 22 / 48 / 10 |

- **At `0.0` the build does nothing.** The baseline arm's ranked lists and bands equal the 2026-09-24 capture the pool was counted on, on **80 of 80** questions. That is a check on the build, not an arm: the bar forbids stating a delta against that capture (§What this run may NOT do, item 9).
- **Every rank-1 change is on a tagged question**, at every weight. Untagged rank 1 did not move. Whether any change is a win is the score's to say.
- **Latency is flat.** The scan re-reads the shards for the table only when the weight is above 0, and the medians stay within 150–164 ms.

## 3 · Headroom (SR-RS d22)

Restated from **this run's baseline arm** once it is scored (d22f); `decide.py`
writes it into `decision.json`. The bar's precondition counted improvement
**10** and regression exposure **41** on the 2026-09-24 capture. Because the
baseline's rankings are identical to that capture, the numbers should match.
That is a prediction, not a figure this report claims.

## 4 · Reproduce

```bash
cp -a ~/my_programs/fux-lab/corpora/golden/rung-01000 ~/my_programs/fux-lab/arms/runs/mx-base/rung-01000
(cd ~/my_programs/fux-lab/arms/runs/mx-base/rung-01000 && fux ingest --full && fux build)   # at f8b21bd5
# each arm: cp -a the base, add `mined_weight = <w>` under [ranking] in .fux/tune.toml, then
python3 tools/quality-controls/golden_run.py --rung rung-01000 \
    --tree ~/my_programs/fux-lab/arms/runs/mx-<w>/rung-01000 \
    --evidence work/regression/2026-09-27-mined-expansion/evidence/mx-<w>/rung-01000 \
    --sets 3-u --arm mx-<w> --engine-commit f8b21bd5
python3 work/regression/2026-09-27-mined-expansion/evidence/describe.py
```

## Authorship

**`classification: informed`, permanently**, for the bar's reasons: set-3-u is
Claude-authored and has been scored before, and the endpoint was ruled after the
pools were seen. **This session also built the mechanism and captured the
arms**, so it may not decide them (§What this run may NOT do, item 5). It read
`work/golden/questions/set-3-u.jsonl` through the harness and no other path
under `work/golden/` except `seed/` and the ladder manifest, and it opened no
score and no key.
