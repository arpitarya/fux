---
type: Analysis
name: ci-arm-batching-analysis
description: "Why W-243 step 1 stops, what would reopen it, and what the Windows and job-count evidence changed in steps 2-4."
run: 2026-09-30-ci-arm-batching
item: W-243
timestamp: 2026-09-30T00:00:00Z
---

# Analysis — W-243's evidence, step by step

## Step 1: batching the arm does not pay while each call reads the index

**Diagnosis.** A Node comparison costs ~350 ms as its own process and
110–700 ms inside a shared one. The shared process saves only start-up and
module load (~100 ms). Everything else is the reader's own work per call, and
`node/src/` caches nothing across calls: each call reads the committed index
again. That is the cost W-242 exists to cut (T0 reads each shard once, T1
reads `.fux/runtime/`).

**Change: none.** The item's own rule stops the step below ~5x, and 1.1–1.4x
is well below it. The FAST `arm` stays at 10 shards and FULL `node-arm` at 3
per cell. `tools/differential/node_arm.py` is not touched.

⚠ **One sentence in that file is now stale, and it is recorded here rather
than edited** (the file's owner, SR-T1-ACCELERATOR, carried another session's
uncommitted edits that day). The sharding comment says batching *"would save
well under a tenth"*. That was measured when a call cost ~1.2 s. After W-235 a
call costs ~0.35 s, and the saving is 10–30 %. The conclusion still stands
(sharding, not batching), but the fraction does not. Correct it in the next
change that touches `node_arm.py`.

**What reopens it.** Re-run `evidence/bench.py` once W-242 T0 **and** T1 have
landed. If a call then costs well under 100 ms, start-up becomes most of the
cost and the ratio could clear 5x. The driver design is already settled by the
item. The verb seam is the constraint to design against: the one-process side
here calls `runFind`/`runAsk` directly, and so skips `main`'s argv parsing,
which is exactly where W-107's defect lived.

## Step 2: 17 of 40, not 22 of 40

Measured by `python scripts/ci-key.py skips 40` on 2026-09-30. The five
commits the ruling's estimate counted as documentation-only re-ingest the
committed `.fux/index/`. That index is the arm's own corpus, so by the
exclude-list rule it is code. **No exclusion was widened to recover them.** A
re-ingested index can change an arm verdict, and an index change that skipped
FULL would be exactly the silent pass the key must never produce.

## Step 3: one test, not the platform in general

`evidence/unit-spawn-profile.txt`: 554 of 6 462 unit tests start a
subprocess, they are 50 % of call time, and **54 % of every spawn comes from
`tests/test_sr_freshness.py`** (~1 540 `git` processes). On Windows that one
test took 72 s against 10 s on Linux.

**Change:** its blobs now come through one `git cat-file --batch`, and each
commit's patch is read once and split by file. Before landing, the answers
were checked identical against the old code on 166 commits and 1 165
(commit, file) pairs. Locally that test went from 23.7 s to 5.9 s.

**Also changed, not yet measured:** `TMP`/`TEMP` point at `$RUNNER_TEMP` on
Windows (`setup-fux`), and FULL's Python cells print `--durations=30`, so the
next `main` run is the profile the next cut comes from.

**Not done, and why:** running CLI tests in-process (item 3.3) and a second
Windows shard (3.4). The 30-slowest profile does not exist yet. A second shard
adds two jobs to a run that is already 18 over the cap.

## Step 4: `needs:` stays

The run is **38 jobs** against the plan's 20 (13 FAST + 24 FULL + `verdict`,
after `ladder` folded into `build`), and **8 macOS against 5**. The condition
for dropping `needs:` was *"every job fits under the cap"*. It does not hold,
and it cannot hold until step 1's collapse of the arm matrix is possible. In
the last green push run, FULL's worst queue was 214 s even with `needs:` in
place ([`evidence/ci-jobs-36666260696.tsv`](evidence/ci-jobs-36666260696.tsv)).
Without it, FAST would queue too.

## Unresolved

- Whether the Windows temp move helps here at all. It needs a `main` run.
- What the other ~46 % of Windows' extra time is. It needs the
  `--durations=30` output from that same run.
