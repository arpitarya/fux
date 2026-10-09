---
type: Report
description: "W-236 Part B, section records: built on branch w236-sections (f2a139fd); G0 byte identity at 0.0 PASS (90/90 rows), G1 size bar at rung-10000 PASS (ratio 0.979, 51.4 MB, largest file 899 KB); five arms captured on set-5-claude at a re-ingested copy of gen-4 rung-01000. Hand-offs only: no score and no verdict exist yet."
run: 2026-10-10-section-records
item: W-236
classification: informed
filed: 2026-10-10
pre_registration: work/regression/2026-10-10-section-records/PRE-REGISTRATION.md
---

# Report: section records (`set-5-claude`, `rung-01000` copy)

⏳ **Captured 2026-10-10; not scored, not decided.** No answer key reached this
session (`just golden-state` read `locked` throughout). Below, *changed* means
**the ranking moved**, never that it *improved*.

- **Who scores:** Arpit, with `just golden-score work/regression/2026-10-10-section-records`, in his own shell. No unlock is needed.
- **Who decides:** a session that did **not** capture these arms runs
  [`evidence/decide.py`](evidence/decide.py) (sha256 `71769bb0…ee7034e`, frozen
  at `4ac1d334` before any build code existed). An INCONCLUSIVE goes to Arpit.

## 1 · What ran

| | |
|---|---|
| sequence | pre-registration `4ac1d334` → build `f2a139fd` on branch `w236-sections` → gates and capture, 2026-10-10 |
| engines | detached worktrees with their own venvs: **pre-section** `4ac1d334` (G0 only) and **build** `f2a139fd` (every arm). Neither is the main tree, which carried another session's uncommitted edits |
| source rung | `fux-lab/corpora/golden/rung-01000` at `e776146f`. **Not written to** |
| the base | `fux-lab/arms/runs/sw-base/rung-01000`, a `cp -a`. `doctor --fix` wrote **one key**, `section_weight = 0.0` ([`evidence/doctor-fix.diff`](evidence/doctor-fix.diff)); then `fux ingest --full` (1 000 documents, 4.9 s) |
| arm copies | `arms/runs/sw-<λ>/rung-01000`, each `cp -a` of the base; `diff -r` shows **only** the `section_weight` line |
| harness | `golden_run.py --sets 5-claude --arm sw-<λ> --engine-commit f2a139fd --fux <pinned build>`, unchanged; 90 questions per arm |

## 2 · The gates

| gate | bar | measured | |
|---|---|---|---|
| **G0** byte identity at `0.0` | all 90 hand-off rows equal, latencies and stamps aside | **0 of 90** hand-off rows and **0 of 90** prediction rows differ between the pre-section engine on the plain copy and the build at `sw-0.0` on the re-ingested base ([`evidence/g0/`](evidence/g0/g0.json)) | ✅ PASS |
| **G1** size at `rung-10000` (`99fe0b4`, copy, `--full`) | section ÷ document plane ≤ 2.0 · total ≤ 55 000 000 B · largest file ≤ 1 MiB · 0 totality misses and 0 `nsec` disagreements | **0.979** (24 980 580 ÷ 25 519 343 B) · **51 398 926 B** · **899 003 B** (`REGISTER`) · **0 · 0**. 9 660 of 10 000 documents split into 39 466 sections ([`evidence/g1.json`](evidence/g1.json), from [`g1.py`](evidence/g1.py)) | ✅ PASS |
| **G2** the pool ≥ 6 on the baseline arm | `pools.step10_section.reorderable@1` | needs Arpit's score of `sw-0.0`; `decide.py` reads it first | ⏳ |

G0 compares against the engine at the freeze commit, so the bar's
*"pre-section engine"* is literal. The sw-0.0 bands (44 · 26 · 20) are also the
2026-10-09 capture's, but no delta is stated against that capture.

## 3 · What each arm did (descriptive, `k = 10`)

From [`evidence/describe.py`](evidence/describe.py) → `describe.json`, against `sw-0.0`:

| arm | rank 1 changed | order changed | membership changed | answer text changed | bands (grounded / partial / weak) |
|---|---:|---:|---:|---:|---|
| `sw-0.0` | — | — | — | — | 44 / 26 / 20 |
| `sw-0.1` | 9 | 56 | 19 | 3 | 44 / 26 / 20 |
| `sw-0.25` | 11 | 81 | 47 | 15 | 42 / 26 / 22 |
| `sw-0.5` | 16 | 85 | 55 | 25 | 45 / 26 / 19 |
| `sw-1.0` | 17 | 89 | 68 | 31 | 45 / 26 / 19 |

- **The term reaches every question, not only the pool.** Every candidate gets
  `λ ·` its best section, so order moves on up to 89 of 90 questions. That is
  the *hurts* direction the bar named, and it is what clause 2 (no new rank-1
  miss anywhere) is there for.
- ⚠ **Latency, not a benchmark figure.** Median `ask` was 188 ms at `sw-0.0`
  and 484–527 ms in the treatment arms, captured later on a shared machine.
  Run on its own, the same `ask --json --band --why --top 10` takes **0.26 s
  at `sw-1.0` against 0.20 s at the base**, three runs each, on the scan path.
  The ~60 ms is the section plane read. The rest of the capture's gap is
  machine load. Nothing here gates.

## 4 · Not in the bar, and owed to Arpit with the verdict

**This repository's own index.** Re-ingested by the build, its section plane
measured **337 477 770 B against a 42 102 393 B document plane (8.0×)**, with
a largest section shard of 6.19 MB. `.jsonl` sources make up 75.6 % of that:
one section per record, each repeating the shared vocabulary
([`evidence/own-repo-sizes.json`](evidence/own-repo-sizes.json)). SR-SECTIONS'
Consequences named this format class as unmeasured, because the ladder holds
none of it. G1 passes on the ladder, and no frozen commit limit fails here.
But the branch does **not** carry this repository's re-ingested index, so the
merge owes it, and its size is a cost nobody has accepted.
[`ANALYSIS.md`](ANALYSIS.md) §2.

## Authorship ([SR-RS](../../../records/0133_predictions.md) decision 13)

| artifact | author | could reach |
|---|---|---|
| the questions (`set-5-claude`) | Claude, prompt 12, run by Arpit 2026-10-03 | `seed/` only |
| the rung (gen 4) | the rebuild session, 2026-10-05 | the seed corpus; never `questions/` |
| the bar, the build and this capture | Claude Code (Opus 5.5), 2026-10-10 (W-236) | the question text as it passes through `golden_run.py`, and the pool **counts** of the 2026-10-09 score; **no** key, no per-row tag, no judgment |

`informed`, permanently: the questions' author and the builder are the same
model family.

## Headroom ([SR-RS](../../../records/0133_predictions.md) decision 22)

From the baseline arm, once scored (d22f). On the 2026-10-09 capture: improvement
23 on the pool, regression 45.
