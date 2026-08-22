---
type: Verdict
name: R6-MERGE-RERUN
title: "R6 re-run — the merge driver, judged with a tier 1 that can be informative"
description: "PASS. All three judged tiers match their expected column and both machine tiers are informative against the control arm. Supersedes nothing: R6-MERGE (2026-08-20, INCONCLUSIVE) stands as filed."
status: final
verdict: PASS
prediction: R6
pre_registration: tools/maintenance-bench/PRE-REGISTRATION-R6-v2.md
timestamp: 2026-08-22T00:00:00Z
---

# R6-MERGE-RERUN — **PASS**

- **Prediction:** **R6** — *machine planes conflict-free, human conflicts
  preserved.* Same prediction, second measurement.
- **Pre-registration:**
  [`tools/maintenance-bench/PRE-REGISTRATION-R6-v2.md`](../../../tools/maintenance-bench/PRE-REGISTRATION-R6-v2.md),
  written before this run.
- **Item:** [W-67](../../open/W-67-r6-instrument-repair.md)
- **Engine:** `9bb870e+dirty` · Python 3.14.2 · Darwin 25.3.0 arm64
- **Evidence:** [`evidence/report.json`](evidence/report.json) ·
  [`evidence/run.out`](evidence/run.out)

## The verdict

**PASS**, read from the `PASS` row of §3.2 of the pre-registration, which was
written before the run.

| tier | treatment | control | informative | outcome |
|---|---|---|---|---|
| **1 · disjoint adds, one shard** | no conflict | **conflicts** | **yes** | PASS |
| **2 · one shard, two lines** | no conflict | **conflicts** | **yes** | PASS |
| **3 · same document, both sides** | conflict preserved, both sides kept | conflicts | n/a by design | PASS |
| *1-disjoint · disjoint adds, two shards* | *no conflict* | *no conflict* | *no* | **unjudged** |

All three judged tiers match their expected column, and both machine tiers are
informative against the control arm — the driver is demonstrably doing the
work, rather than git's textual merge succeeding by luck.

## What this changes, and what it does not

**It closes the debt ADR-MERGE-DRIVER was accepted with.** That record went
`accepted` on 2026-08-22 on Arpit's *reading* of a contradictory instrument, not
on a clean pass. Its veto condition 2 is now satisfied by a measurement whose
verdict table had a row for every possible outcome before the run started.

**It does not supersede [R6-MERGE](../2026-08-20-r6-merge-driver/VERDICT.md).**
That verdict read INCONCLUSIVE, it was measured, and it stands exactly as filed
— nothing supersedes a measurement except a better measurement, and a better
measurement is a *new* verdict beside it, which is this file. The 2026-08-20
pre-registration was not edited either; neither its §3.1 nor its §3.2 has
changed a character.

**The instrument was repaired, not the threshold.** The threshold is copied
verbatim into the new pre-registration's §2. What changed is (a) tier 1 is
selected by hashing so that it can be informative, and (b) the verdict table
gained a `PARTIAL` row for the case that fell through in August — a row that
routes to Arpit rather than resolving anything, so nothing was gained by
writing it.

## The finding worth keeping

**Most concurrent adds need no merge driver, and that is now a reported
result rather than an accident.** The original tier 1 — two people adding
different documents, landing in different shard files — merges cleanly *with
the driver removed*. It was kept as an unjudged arm precisely so this stays
visible: the driver earns its place on the one-shard cases, not on the everyday
one. Deleting the arm that showed it would have deleted a true finding while
tidying up an inconvenient one.

## Weaknesses, declared

Both were declared in the pre-registration before the run, not discovered after:

1. **The evidence chain is weaker than the 2026-08-20 run's.** That run could
   point at `git log` to prove the instrument predated the numbers. This one
   cannot: it was produced in a working tree with a large uncommitted change set
   that a concurrent session also held, so the pre-registration could not be
   committed alone. The engine sha is recorded as `+dirty` accordingly. What
   partially substitutes: tier 1's definition was **promoted verbatim** from the
   `tier1b` function already in git history, so *what* was measured does not
   rest on this session's word.
2. **The prior was strong.** `tier1b` had already indicated post-hoc what a
   hash-selected tier 1 would do. This run converts that indication into a
   pre-registered result; it did not discover it. The pre-registration says so
   in its §0 and predicted `PASS` or `FAIL` — not `PARTIAL` — in advance.

## Reproduce

```bash
.venv/bin/python tools/maintenance-bench/run.py --only r6 \
  --out work/regression/2026-08-22-r6-rerun/evidence
```

Run twice on 2026-08-22; identical tier outcomes both times. The second run
differed only in a display fix (an unjudged arm was printing `FAIL`), which
touches no measurement.
