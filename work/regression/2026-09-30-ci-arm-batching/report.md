---
type: Regression Run
name: ci-arm-batching
description: "W-243 step 1's spike: 24 differential-arm comparisons on this repo, as 24 `node` processes against one. One process was 1.11x-1.44x faster over four trials, against the ~5x the item set as the bar to build, so step 1 STOPS. The in-process calls still cost 140-700 ms each, which is the Node reader's own scan, W-242's to cut. Also filed: the Windows profile behind step 3 and the CI job timings the step-4 count rests on."
run: 2026-09-30-ci-arm-batching
item: W-243
classification: blind
status: complete
timestamp: 2026-09-30T00:00:00Z
---

# Does one Node process per arm pass pay? No, not yet.

**A timing measurement, not a ranking run.** It compares nothing about what
the two readers answer: there are no golden questions, keys or scores, so this run
has no per-query rows, and it is not a paired run. The bar came from
[W-243](../../open/W-243-ci-two-minutes.md) step 1: *"If one process is not at
least ~5x faster per comparison after W-242's landed tiers, stop and report."*

## Conditions

- **Engine:** `main` at `92445697`, plus uncommitted edits to `node/src/` from
  a concurrent session (W-242 T0 in progress). So this is the reader as it
  stood in this working tree that afternoon, **not** a landed tier.
- **Machine:** Arpit's Mac, Node v24.13.0. ⚠ **Loaded**: load average 5.9–8.9
  during the second batch, with another Claude session live on the same tree
  (SR-WORK-SESSION decision 12). Absolute times are inflated. The ratio is
  what this run is about, and every trial is far below the bar.
- **Jobs:** 6 queries × tops {1, 20} × {find, ask}, i.e. 24 comparisons,
  `--no-tune` (the transcription arm's flags).
- **One-process side:** `evidence/one-process.mjs` calls `runFind`/`runAsk`
  directly, with `.fux/output.toml` folded in the way `node/fux.mjs`'s `main`
  does. It skips argv parsing and the PII gate, so it is an **upper bound** on
  what a batching driver could save.

## Result

| trial | 24 processes | 1 process | ratio |
|---|---|---|---|
| 0 (first, before the bench was filed) | 8.24 s | 5.85 s | **1.41x** |
| 1 | 7.83 s | 7.07 s | **1.11x** |
| 2 | 12.89 s | 8.96 s | **1.44x** |
| 3 | 13.11 s | 10.18 s | **1.29x** |

Raw rows: [`evidence/bench.jsonl`](evidence/bench.jsonl) (trials 1–3; trial 0
is the session's first measurement, printed and not written to disk).

**In-process, each comparison still costs 110–700 ms**, and `ask` at `--top 1`
on a broad query ("ranking", "graph plane") costs 2–3x the others. Start-up
and module load, the only things one process saves, are ~100 ms of a
~350 ms call.

**Verdict against the item's bar: STOP.** One process is 1.1–1.4x faster, not
~5x.

## Reproduce

```bash
python work/regression/2026-09-30-ci-arm-batching/evidence/bench.py 3
```

## Also filed here: what steps 3 and 4 rest on

- [`evidence/ci-jobs-36666260696.tsv`](evidence/ci-jobs-36666260696.tsv) —
  every job of the last green `main` push run (`9989c7c5`, 2026-09-30):
  queue time, run time, and the steps over 10 s.
- [`evidence/unit-spawn-profile.txt`](evidence/unit-spawn-profile.txt) —
  which unit tests start a subprocess, measured locally.

## Authorship

| artifact | author | could reach |
|---|---|---|
| `bench.py`, `one-process.mjs`, this report, `ANALYSIS.md` | Claude (Opus, Claude Code), 2026-09-30 | none: no golden question, judgment or score is involved |
