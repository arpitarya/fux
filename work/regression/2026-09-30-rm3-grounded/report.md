---
type: Report
description: "W-237, RM3 behind a `grounded`-only gate: five arms, `rm3_weight ∈ {0.0, 0.1, 0.2, 0.3, 0.5}`, captured on set-4-claude at a copy of the generation-3 `rung-01000` with the shipped template tune, engine `ee00d0cd` + the uncommitted W-237 build. Captured, not scored: hand-offs only, no score and no verdict exist."
run: 2026-09-30-rm3-grounded
item: W-237
classification: informed
filed: 2026-09-30
pre_registration: work/regression/2026-09-30-rm3-grounded/PRE-REGISTRATION.md
---

# Report: RM3, only when the first pass is `grounded` (`set-4-claude`, `rung-01000` copy)

🔴 **Captured, not scored.** No score file exists and this session produced
none. Below, *changed* means **the ranking moved**, never that it *improved*.

- **Who scores:** Arpit, with `just golden-score work/regression/2026-09-30-rm3-grounded`,
  in his own shell. No unlock is needed.
- **Who decides:** a session that did **not** capture these arms runs
  [`evidence/decide.py`](evidence/decide.py), sha256 `e0d7ba15…49ae`, written
  before the build ([PRE-REGISTRATION](PRE-REGISTRATION.md) §The decision rule).
  This session captured the arms, so it may not run it (item 5).

## 1 · What ran

| | |
|---|---|
| sequence | pre-registration (frozen, sha256 `33a9f3ab…3eca3`) → build → both suites green → capture, 2026-09-30 |
| engine | worktree at `ee00d0cd` **plus the uncommitted W-237 build**; its code diff is [`evidence/engine.diff`](evidence/engine.diff) (`src/` + `node/src/`, sha256 `82f0014c…fc52d2`), and the hand-offs carry `engine_commit = ee00d0cd+82f0014c`. ⚠ The build commit does not exist yet; whoever commits it records the sha here |
| source rung | `fux-lab/corpora/golden/rung-01000`. **Not written to** |
| the copy | `~/my_programs/fux-lab/arms/runs/rg-base/rung-01000`. **No re-ingest** |
| config repair | `[cli] progress_threshold = 200` added by hand to the copy's `output.toml` (the template's value): since W-239 `fux doctor` reads that key and **cannot start** to write it on a pre-W-239 rung. Then `fux doctor --fix` with the build's engine wrote every other missing key from the templates, `rm3_weight = 0.0` among them, and created `identifiers.toml` and `inspect.toml`. No `[doctype]` table. Diff: [`evidence/doctor-fix.diff`](evidence/doctor-fix.diff) |
| arm copies | `arms/runs/rg-<w>/rung-01000`, each `cp -a` of the base. `diff -r` (excluding `runtime/`) shows **only `tune.toml`**, and only its `rm3_weight` line |
| harness | `golden_run.py --sets 4-claude --arm rg-<w> --engine-commit ee00d0cd+82f0014c --fux <worktree>/.venv/bin/fux`, sequential, unchanged |
| questions | 125 per arm; funnel gates on all 125 in every arm |

## 2 · The build check — `rg-0.0` equals the capture the pool was counted on

[`evidence/same_ranking.py`](evidence/same_ranking.py) against the
[2026-09-27 capture](../2026-09-27-golden-set-4-rung-01000/report.md):

```
ranked lists equal: 125/125; bands equal: 125/125
```

So the build at `0.0` moved nothing, the frozen tag (69) stands, and **the pool
of 20** counted from Arpit's score of that capture holds. The pre-build precheck
at `ee00d0cd` gave the same result ([`evidence/precheck/`](evidence/precheck/)).

## 3 · What each arm did (descriptive, `k = 10`)

From [`evidence/describe.py`](evidence/describe.py) → `describe.json`:

| arm | rank 1 changed | order changed | membership changed | `answer` citations changed | **untagged moved** | bands (grounded / partial / weak) |
|---|---:|---:|---:|---:|---:|---|
| `rg-0.0` | — | — | — | — | — | 69 / 24 / 32 |
| `rg-0.1` | 0 | 65 | 41 | 20 | **0** | 63 / 24 / 38 |
| `rg-0.2` | 2 | 67 | 48 | 26 | **0** | 57 / 24 / 44 |
| `rg-0.3` | 6 | 68 | 57 | 33 | **0** | 51 / 24 / 50 |
| `rg-0.5` | 13 | 68 | 63 | 42 | **0** | 45 / 24 / 56 |

- ✅ **The gate held structurally.** No question whose baseline band is not
  `grounded` moved in any arm; every change is on one of the 69 tagged.
- **The gate fires on nearly every `grounded` question**: the order moved on
  65–68 of 69. Rank 1 moved on 0 / 2 / 6 / 13. That is a count of moves, not of
  wins, and **every one of the 40 `grounded` rank-1 hits is exposed**. Only the
  score can say which way each move went.
- **The published band moves toward `weak`**, 69 → 45 `grounded` at `0.5`. The
  band describes the second pass, the list shown, and ten added terms narrow
  the top-2 separation. That is the mechanism being visible, not a finding.
- **Latency**: median `ask` 184–287 ms per arm on a shared machine, with no
  consistent tagged-versus-untagged gap. The two-pass cost is below this run's
  noise and is not claimed.

## 4 · Headroom ([SR-RS](../../../records/0133_predictions.md) d22)

Restated from this run's baseline arm once it is scored (d22f); `decide.py`
writes it. Because `rg-0.0` equals the 2026-09-27 capture, the pre-registration's
improvement **20** and regression exposure **66** should repeat. That is a
prediction, not a figure this report claims.

## 5 · Hand-offs

| arm | `handoff-set-4-claude.jsonl` sha256 |
|---|---|
| `rg-0.0` | `5c7ca3cc661de17405cab172429f6ff31bab51ac9b1a2ad31e92eb705d87512f` |
| `rg-0.1` | `6be48e26f608d3729320e4f17ba0759f065c119fca116ed3b8d7f25bfc148e09` |
| `rg-0.2` | `75fc25eca0a30941c5af74877e263777459b80bc1132af704380d33df5a86168` |
| `rg-0.3` | `afa82981589bc82936f8071a8a3fab5d267fa3425b7d1211259be362634a96e1` |
| `rg-0.5` | `322d29ed00807ada832125a87c0f0d315d0b0bc4f6469a4c2a3e1e20608b031a` |

## 6 · Reproduce

```bash
cp -a ~/my_programs/fux-lab/corpora/golden/rung-01000 ~/my_programs/fux-lab/arms/runs/rg-base/rung-01000
# add `progress_threshold = 200` under [cli] in its .fux/output.toml, then:
(cd ~/my_programs/fux-lab/arms/runs/rg-base/rung-01000 && <eng>/.venv/bin/fux doctor --fix)
# each arm: cp -a the base to rg-<w>, set `rm3_weight = <w>`, then:
python tools/quality-controls/golden_run.py --rung rung-01000 \
    --tree ~/my_programs/fux-lab/arms/runs/rg-<w>/rung-01000 \
    --evidence work/regression/2026-09-30-rm3-grounded/evidence/rg-<w>/rung-01000 \
    --sets 4-claude --arm rg-<w> --engine-commit <build> --fux <eng>/.venv/bin/fux
python3 work/regression/2026-09-30-rm3-grounded/evidence/same_ranking.py \
    work/regression/2026-09-30-rm3-grounded/evidence/rg-0.0/rung-01000/handoff-set-4-claude.jsonl
python3 work/regression/2026-09-30-rm3-grounded/evidence/describe.py
```

## Authorship

**`classification: informed`, permanently.** `set-4-claude` is Claude-authored
and was scored before; the gate was chosen after `set-2-u`'s rows were seen.
**This session wrote the bar, built the mechanism and captured the arms**, so it
may not decide them. It read the released question ids through the harness,
Arpit's earlier score output (ids, ranks, booleans) for the pool count, and no
key.
