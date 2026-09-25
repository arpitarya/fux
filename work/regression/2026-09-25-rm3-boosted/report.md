---
type: Report
description: "W-221's re-run of W-168 step 5 (RM3), with RM3 learning from the graph-boosted top 10 that `ask` shows. Five arms, `rm3_weight ∈ {0.0, 0.1, 0.2, 0.3, 0.5}`, captured on `set-2-u` at the frozen `rung-01000` index, engine `0ff3078c`. Hand-offs only: no score and no verdict exist yet."
run: 2026-09-25-rm3-boosted
item: W-221
classification: informed
filed: 2026-09-25
pre_registration: work/regression/2026-09-25-rm3-boosted/PRE-REGISTRATION.md
---

# Report: RM3 re-run on the boosted first pass (`set-2-u`, `rung-01000`)

🔴 **Captured, not scored, and not decided.** No answer key reached this session.
Below, *changed* means **the ranking moved**, never that it *improved*.

- **Who scores:** Arpit, with `just golden-score work/regression/2026-09-25-rm3-boosted`.
- **Who decides:** a session that did **not** capture these arms runs [`evidence/decide.py`](evidence/decide.py). It is the 2026-09-23 decider with only the arm names and paths changed, and it is committed before any score exists.

## 1 · What ran

| | |
|---|---|
| sequence | re-registration `d1eeaae3` → build `0ff3078c` → capture, 2026-09-25 10:17–10:20 |
| index | 🔴 **the frozen `17fe414e…` index, copied from the 2026-09-23 arm copies** (see §2) |
| arm copies | `~/my_programs/fux-lab/arms/runs/rm3b-<w>/rung-01000`. Each `.fux/index` is `diff -r` identical to the source, and each `tune.toml` differs from the committed one only in the `rm3_weight` line (`anchor = 0.0`, `ask_boost = true`) |
| engine re-ingest check | a throwaway copy re-ingested at `0ff3078c` wrote **0 shards**, and its index is byte-identical |
| harness | `golden_run.py --sets 2-u --engine-commit 0ff3078c`, unchanged from 2026-09-23 |
| questions | 125 per arm; the funnel gates were captured on all 125 in every arm |

## 2 · ⚠ `rung-01000` moved since 2026-09-23, and this run did not follow it

`fux-lab/corpora/golden/rung-01000` was **rebuilt at 12:05 UTC on 2026-09-23**
("index rung-01000 (42 seed documents)", the ladder-seed-36 rebuild), after the
first RM3 arms were copied. Its index is no longer the `17fe414e…` index the
pre-registration freezes.

- The five 2026-09-23 arm copies still hold that frozen index, and they agree with each other byte for byte. **This run was copied from them.**
- ⚠ **A first attempt was copied from the rebuilt rung by mistake.** The copy script did not stop at the failed index `diff`. Those copies were deleted before any capture ran.

## 3 · What each arm did (descriptive, `k = 10`)

From [`evidence/describe.py`](evidence/describe.py) → `describe.json`:

| arm | rank 1 changed | of which tagged | order changed | membership changed | median `ask` ms | bands (grounded / partial / weak) |
|---|---:|---:|---:|---:|---:|---|
| `rm3b-0.0` | — | — | — | — | 139 | 42 / 59 / 24 |
| `rm3b-0.1` | 18 | 12 | 122 | 105 | 181 | 45 / 59 / 21 |
| `rm3b-0.2` | 29 | 20 | 125 | 117 | 182 | 42 / 59 / 24 |
| `rm3b-0.3` | 38 | 26 | 125 | 120 | 182 | 38 / 59 / 28 |
| `rm3b-0.5` | 53 | 38 | 125 | 123 | 183 | 33 / 59 / 33 |

- **At `0.0` the build does nothing.** The baseline arm's ranked lists equal the 2026-09-23 baseline arm's on **125 of 125** questions.
- **The change made a difference.** Compared with the 2026-09-23 arm at the same weight, the ranked list differs on **50 / 58 / 60 / 60** questions, and rank 1 on **3 / 3 / 3 / 11**. This compares rankings only, and it gates nothing (re-registration, extra item 1).
- **The band still leans toward `weak` at the high weights** (24 → 33 at `0.5`), for the reason the 2026-09-23 ANALYSIS §3 gives.

## 3a · Headroom (SR-RS d22)

Headroom is restated from **this run's baseline arm** once it is scored (d22f), and `decide.py` writes it into
`decision.json`. It will not be quoted from the 2026-09-23 run, whose baseline ran at a different engine.
Its ranked lists are identical to this run's, so the numbers should match. That
is a prediction, not a figure this report claims.

- **Improvement headroom** (d22b): the baseline's tagged rank-1 misses that sit in the returned 10. This is the pool clause 1 can win from.
- **Regression headroom** (d22f): the baseline arm's `hit@1` count across the whole set. Each of those is exposed to the drift bound, clause 2.

## 4 · Reproduce

```bash
# each arm: cp -a ~/my_programs/fux-lab/arms/runs/rm3-0.0/rung-01000, set rm3_weight = <w>, then
python3 tools/quality-controls/golden_run.py --rung rung-01000 \
    --tree ~/my_programs/fux-lab/arms/runs/rm3b-<w>/rung-01000 \
    --evidence work/regression/2026-09-25-rm3-boosted/evidence/rm3b-<w>/rung-01000 \
    --sets 2-u --arm rm3b-<w> --engine-commit 0ff3078c
python3 work/regression/2026-09-25-rm3-boosted/evidence/describe.py
```

## Authorship

**`classification: informed`, permanently.** The authorship is the 2026-09-23
report's table, with one addition. **This session also ran W-221's ranking
comparison**, so it may not rule on this run.
