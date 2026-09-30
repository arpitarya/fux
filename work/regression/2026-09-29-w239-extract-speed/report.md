---
type: Regression Run
name: w239-extract-speed
description: "W-239 — the ingest extract phase, before and after three per-document fixes (a gated identifier-family scan, a cached decoder registry, a cached formats.toml [meta] read). rung-10000 extract 45.6 s -> 6.5 s and total 73.5 s -> 12.8 s back to back; rung-01000 extract 8.45 s -> 3.07 s; the committed index is byte-identical on both rungs."
run: 2026-09-29-w239-extract-speed
item: W-239
classification: blind
status: complete
timestamp: 2026-09-29T00:00:00Z
---

# The ingest `extract` phase, before and after W-239

**A latency run, not a ranking run.** No golden question, key or score is
involved. The change is required to leave every committed byte unchanged, and
the equality check is a sha-256 over `.fux/index/` after a full ingest. It is
**not a paired run** in SR-RS decision 22's sense (nothing is scored), and it
files **no per-query rows** (there are no queries).

- **Machine:** macOS, 10 cores, Python 3.14.3 (`fux`'s own `.venv`). The
  machine was shared with at least one other session: load average was 5.9–7.7
  during the first "before" runs and 2.2–2.6 afterwards. **That is why the
  10 000 pair was re-run back to back**, and only that pair is quoted as the
  speed-up.
- **Before:** `HEAD` = `0980e962`'s `src/`, extracted with `git archive` and run
  with `PYTHONPATH`. **After:** the same tree plus the W-239 change.
- **Corpora:** scratch copies of `fux-lab/corpora/golden-gen2/rung-01000` and
  `rung-10000` under `fux-lab/scratch/w239/`, each given **this repo's
  `.fux/identifiers.toml` (103 families)**, as the item requires. `fux doctor
  --fix` was run on the copies, because the rungs' `fux.toml` predates keys the
  current engine requires. The kept rungs were not touched.
- **Harness:** `evidence/phase_times.py` calls `ingest.run(full=True)` in
  process and times each progress phase with `perf_counter`. It is measurement
  tooling, so it may read a clock. `--full` re-extracts every document, which
  is the path being measured.

## Phase times, seconds

| rung | arm | extract | redact | write | total | index sha-256 |
|---|---|---|---|---|---|---|
| 01000 | before | 8.45 | 0.12 | 0.30 | 14.04 | `678cf6eb…a69a` |
| 01000 | after | **3.07** | 0.12 | 0.23 | **4.63** | `678cf6eb…a69a` |
| 10000 | before (back to back) | 45.59 | 0.99 | 0.82 | 73.46 | `9f415b2e…66ba` |
| 10000 | after (back to back) | **6.50** | 0.97 | 0.81 | **12.84** | `9f415b2e…66ba` |

At 10 000 documents `extract` is **7.0× faster** and the whole ingest is
**5.7× faster**. The 10 000 numbers from the first, loaded pair (45.22 → 6.54)
agree with these. Every row is in `evidence/timings.txt`.

## Where the 1 000-document ingest went (cProfile, cumulative)

| s before | s after | what |
|---|---|---|
| 4.94 | 0.27 | `decode.registry()`, 3 410 calls; 57 970 `exec_module` before, 17 after |
| 2.87 | 0.23 | `IdentifierRules.matches()`, 4 214 calls |
| 1.87 | ~0 | `decode.meta_bindings()` → `typesfile.read`, 1 000 parses before |
| 2.17 | 2.17 | `stem()`, unchanged and now the largest cost |

Full listings: `evidence/profile-1k-before.txt`, `evidence/profile-1k-after.txt`.

## The matcher, on its own

`evidence/matcher_sweep.py` runs the old combined `finditer` and the new gated
scan over **every tracked Markdown file in this repo** (1 213 files, `work/golden/`
excluded), using the repo's 103 families:

```
1213 files, 0 mismatches, 103 families; old 90.08s new 2.51s (35.9x)
```

## Reproduce

```bash
L=~/my_programs/fux-lab/scratch/w239      # the scratch rung copies
E=work/regression/2026-09-29-w239-extract-speed/evidence
S=$(mktemp -d); git archive 0980e962 src | tar -x -C $S
PYTHONPATH=$S/src .venv/bin/python $E/phase_times.py $L/rung-10000   # before
.venv/bin/python $E/phase_times.py $L/rung-10000                     # after
.venv/bin/python $E/matcher_sweep.py                                 # from the repo root
```

## Authorship

Claude Code (Opus 5.5), 2026-09-29, the session that built W-239. It is `blind`
because no artefact the run depends on was authored against a score: the rungs
are generated, the families are the repo's committed `[detected]` table, and the
only outcome measured is time and byte equality.
