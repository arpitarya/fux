---
type: Report
description: "W-257 DoD 3, capture: the seven pre-registered arms of the full enriched rung on gen-4 rung-01000, one engine (a07f9329), set-5-claude (90) through golden_run.py. G0, G1, G3 and the archived gate pass; none reproduces the 2026-10-09 capture 90/90. No correctness column: Arpit scores, then a session that did not capture runs decide.py (B-108, B-109) and tilt.py (B-110)."
run: 2026-10-10-enriched-rung
item: W-257
rung: rung-01000
classification: informed
filed: 2026-10-10
---

# Report: the enriched rung, seven arms captured. Arpit scores.

**Bar:** [PRE-REGISTRATION.md](PRE-REGISTRATION.md) (`a07f9329`), amended
once by Arpit's ruling ([AMENDMENT.md](AMENDMENT.md), `79bc22ea`, committed
before any arm past the gates was built). The gates before the arms:
[GATES.md](GATES.md). 🔴 **This report never says whether an answer is
right.** No key reached this session, and it ran no scorer.

⚠ **Every verdict on this run carries amendment 1's sentence:** *doc2query as
written by a blind author without the fux-enrich skill: one question per chunk,
template-filled on `ext`.*

## What ran

- **Engine:** `a07f9329`, `fux 3.0.0-alpha.11`, a detached worktree with its
  own venv. Every arm was ingested `--full` by it, and every harness call used it.
- **Arms:** `~/my_programs/fux-lab/arms/runs/w257/<arm>/`, each a `cp -a` of
  `rung-01000` at `e776146f`. `diff -rq` against `declared` (excluding `.git`,
  `__pycache__`, `index` and `runtime`) shows only `.fux/enrich/`. `none`
  differs from `declared` only in `.fux/sources/dirs`.
  [`evidence/build_arms.py`](evidence/build_arms.py) built `filtered`,
  `placebo`, `cov-25` and `cov-50`.
- **Harness:** `golden_run.py --rung rung-01000 --tree <arm> --fux <pinned>
  --arm <arm> --engine-commit a07f9329 --sets 5-claude --evidence
  evidence/<arm>/rung-01000`. 90 questions × 2 calls per arm, 32–93 s each, on
  a shared machine.

| arm | `.fux/enrich/` | index (sha256 of shards, 16) |
|---|---|---|
| `none` | — | `49ddce516fc976cb` |
| `declared` | — | `49ddce516fc976cb` (= `none`: **G0**) |
| `unfiltered` | the author's 1,000 files, 5,620 questions | `3a8fa23268555906` |
| `filtered` | the same minus the 837 first-pass refusals (4,783 left, 357 files touched) | `8574a46451b21999` |
| `placebo` | `placebo.py --per-line`: 1,000 files, 0 line-count mismatches, −1.1 % words | `79277e9b65479de6` |
| `cov-25` | `unfiltered`'s files for `S_25` (250 documents) | `766d61e7857870f9` |
| `cov-50` | `unfiltered`'s files for `S_50` (500 documents) | `4076e0a567ce008c` |

## The capture: descriptive only ([`evidence/describe.json`](evidence/describe.json))

| arm | rows · gates | empty · uncited | grounded · partial · weak | rank-1 = `none` | top-10 = `none` |
|---|---|---|---|---:|---:|
| `none` | 90 · 90 | 0 · 0 | 44 · 26 · 20 | — | — |
| `declared` | 90 · 90 | 0 · 0 | 44 · 26 · 20 | 90 | 90 |
| `unfiltered` | 90 · 90 | 0 · 0 | 39 · 26 · 25 | 78 | 1 |
| `filtered` | 90 · 90 | 0 · 0 | 41 · 26 · 23 | 78 | 1 |
| `placebo` | 90 · 90 | 0 · 0 | 41 · 26 · 23 | 81 | 7 |
| `cov-25` | 90 · 90 | 0 · 0 | 44 · 26 · 20 | 82 | 15 |
| `cov-50` | 90 · 90 | 0 · 0 | 46 · 26 · 18 | 81 | 3 |

- **`none` reproduces the 2026-10-09 capture of the same set at the same rung:
  top-10 lists identical on 90/90**, so G2's pre-registered headroom
  (improvement 36, regression 45) is this arm's. `decide.py` re-reads it from
  the score.
- A changed rank-1 document is **not** a win or a loss. Whether it is right
  is the key's, and only Arpit's scorer reads the key.

## The gates

| gate | result |
|---|---|
| `archived` refusal | pass ([GATES](GATES.md)) |
| G0 | pass: `declared` = `none` byte for byte, and in all 90 rankings |
| G1 | pass: no malformed file, no sha mismatch, no PII hit |
| G2 | read by `decide.py` from `none`'s score |
| G3 | pass: 837 / 5,620 = 14.9 % |
| placebo line count | pass after amendment 1 |

## What happens next

1. 🔴 **Arpit:** `just golden-score work/regression/2026-10-10-enriched-rung`,
   which scores the seven hand-offs into `scores/<arm>/rung-01000/`.
2. **A session that did not capture these arms** runs
   [`evidence/decide.py`](evidence/decide.py) (sha256 `49dfc3bb…`) and
   [`evidence/tilt.py`](evidence/tilt.py) (sha256 `be3e69d0…`), both committed
   in `79bc22ea` before any arm was scored. It writes `VERDICT.md`. Every
   INCONCLUSIVE goes to Arpit.
3. Then W-257 DoD 3's rewrite (SR-ENRICH d15, d16, main d6 → `sr-hash.py
   --write`) and DoD 4 (`BACKLOG.md`).

## Authorship

| artifact | author | could reach |
|---|---|---|
| the 5,620 questions | the blind full-rung author (11 subagents + a coordinator, `claude-opus-5-5`), launched by Arpit in `fux-lab`, 2026-10-10 00:30–00:46 | the rung copy's documents, by its prompt. **none** of queries, judgments or scores, by its own report and by nothing the environment can prove |
| the bar and amendment 1 | Claude Code sessions, 2026-10-10 | the queries (`set-5-claude` is released text) and prior scores (counts). No key |
| `placebo.py --per-line`, `build_arms.py`, `decide.py`, `tilt.py`, this capture | this session (Claude Code, Opus 5.5) | the queries, through the harness. No key, no score |

`informed`, permanently: `set-5-claude` is Claude-authored (L11 d7). **Not a
generalisation estimate** (SR-RS d13).

## Repro

```bash
F=<worktree at a07f9329>/.venv/bin/fux; A=~/my_programs/fux-lab/arms/runs/w257
python3 -I work/regression/2026-10-10-enriched-rung/evidence/build_arms.py   # after none/declared/unfiltered (GATES.md)
for a in none declared unfiltered filtered placebo cov-25 cov-50; do
  (cd $A/$a && $F ingest --full)
  python3 -I tools/quality-controls/golden_run.py --rung rung-01000 --tree $A/$a --fux $F --arm $a \
    --engine-commit a07f9329 --sets 5-claude --evidence work/regression/2026-10-10-enriched-rung/evidence/$a/rung-01000
done
python3 -I work/regression/2026-10-10-enriched-rung/evidence/describe.py
```
