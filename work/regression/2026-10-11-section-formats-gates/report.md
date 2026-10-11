---
type: Report
description: "W-273 phase 1's gates: the build b4d961cd (no section records for .csv/.json/.jsonl) re-run through W-269's G0, G1 and G3 on the gen-4 ladder — all PASS and each byte-identical to W-269's, because the ladder holds none of those formats — and this repository's own section plane by format: 1.756x the document plane, down from W-236's 8.0x."
run: 2026-10-11-section-formats-gates
item: W-273
classification: informed
filed: 2026-10-11
---

# Report: W-273 phase 1's gates (`b4d961cd`)

**Not a paired run: gates only, no score and no verdict.** No arm was scored and no threshold
is ruled here; W-270 is the measurement. This run checks that the phase-1
build does what [SR-SECTIONS](../../../records/0161_sections.md) decision 2 now
says, and pins the engine W-270 measures.

## 1 · What ran

| | |
|---|---|
| engine | a detached worktree at **`b4d961cd`** with its own venv (`fux 3.0.0-alpha.11`). Against W-269's `03fbf782`, `src/`, `node/` and `tools/` differ in three files only: `constants.toml`, `ingest/extract.py`, `templates/tune.toml.txt` |
| scripts | W-269's [`g0.py`](../2026-10-10-section-gain-only/evidence/g0.py) and [`g3.py`](../2026-10-10-section-gain-only/evidence/g3.py), W-236's [`g1.py`](../2026-10-10-section-records/evidence/g1.py), all unchanged; the drivers are [`evidence/gates.sh`](evidence/gates.sh) and [`evidence/g1own.sh`](evidence/g1own.sh) |
| the base | `fux-lab/arms/runs/w273-base/rung-01000`, a `cp -a` of W-269's `gain-base` (gen-4 `rung-01000`, `section_weight = 0.0` already written), then `fux ingest --full` with `b4d961cd` |
| arm copies | `fux-lab/arms/runs/w273-gates/sw-<λ>/rung-01000` for λ ∈ {0.0, 0.25, 0.5, 1.0, 2.0}, each a `cp -a` of the base with only the `section_weight` line changed |
| G1 copy | `fux-lab/arms/runs/w273-g1/rung-10000`, a `cp -a` of W-269's `gain-g1`, then `fux ingest --full` |
| own repository | a second detached worktree at `b4d961cd`, `fux ingest --full --no-fetch` |
| machine | shared: load average 10.1 at 03:51, other sessions' processes running. The base re-ingest took 588 s of wall time against 6 s of CPU (W-269 measured 4.2 s). No number here is a timing |

## 2 · The gates

| gate | bar | measured | |
|---|---|---|---|
| **index identity** | the base's `.fux/index/` after `ingest --full` equals W-269's `gain-base` | `diff -r` empty: **byte-identical**. Gen-4 `rung-01000` holds no `.csv`, `.json` or `.jsonl` document (`.md` 775, `.yaml` 134, `.html` 52, `.txt` 35, `.eml` 4, `.toml` 1), so option (b) moves nothing there | ✅ |
| **G0** byte identity at `0.0` | 90 hand-off and prediction rows of `set-5-claude` at `sw-0.0` equal W-269's `sw-0.0`, latencies and stamps aside | **0 of 90** and **0 of 90** ([`evidence/g0.json`](evidence/g0.json)) | ✅ PASS |
| **G1** size at `rung-10000` | W-236's bars | `g1.json` **byte-identical** to W-269's: ratio 0.9789, 51 398 926 B, largest 899 003 B (`REGISTER`), 0 totality misses, 0 `nsec` disagreements ([`evidence/g1.json`](evidence/g1.json)) | ✅ PASS |
| **G3** sectionless documents unmoved | W-269's three conditions at every λ | **0 failures**, 1 481 comparisons per arm, 40 sectionless documents, 90 questions; the JSON equals W-269's `g3.json` key for key ([`evidence/g3.json`](evidence/g3.json)) | ✅ PASS |

## 3 · This repository's own section plane, by format

[`evidence/own-repo-sizes.json`](evidence/own-repo-sizes.json), summed as W-236's
ANALYSIS §2 did:

| | W-236 (`f2a139fd`) | this build (`b4d961cd`) |
|---|---:|---:|
| document plane | 42 102 393 B | 44 851 336 B |
| section plane | 337 477 770 B | **78 772 996 B** |
| ratio | 8.0× | **1.756×** |
| largest section shard | 6 192 981 B | 4 297 059 B |
| `.jsonl` sections | 79 611 | **0** |
| `.json` sections | 4 522 | **0** |
| `.md` sections | 14 004 | 14 159 |

W-273 expected *near 1.9×*. The section plane is what W-236's prose sections
predicted (77.7 → 78.1 MB of `.md`); the ratio is lower because the document
plane grew 6.5 % since W-236's measurement.

## Authorship ([SR-RS](../../../records/0133_predictions.md) decision 13)

| artifact | author | could reach |
|---|---|---|
| the build and this capture | Claude Code (Opus 5.5), 2026-10-11 | the `set-5-claude` question text as it passes through `golden_run.py` and `g3.py`; W-269's score files (ids, booleans, pool counts); **no** key |
| the gate scripts | W-236's and W-269's sessions | as their reports say |

`informed`: `set-5-claude` is Claude-authored and has been read by two
mechanisms. Nothing here is a quality claim; every row is an identity check.
