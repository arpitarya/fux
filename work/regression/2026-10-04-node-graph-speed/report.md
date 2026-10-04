---
type: Report
description: "W-259 DoD 3-4, run as frozen in PRE-REGISTRATION.md. (a) The graph.json read against the forced rebuild: NULL. At rung-10000 the read is faster in 12 of 12 cells for find and for ask, but saves a median 9.48 % and 9.71 % against a frozen 10 %; rung-01000 saves under 2 %. (b) One graph build per Node process: a median 1.575x against W-243 step 1's 5.0x, so step 1 stays STOP. Both identity gates held. informed."
run: 2026-10-04-node-graph-speed
item: W-259
classification: informed
filed: 2026-10-05
---

# Report: the read helps a little, and batching still does not pay

[Pre-registration](PRE-REGISTRATION.md) (frozen at `d0a60b6e`) ·
[verdict](VERDICT.md): **FAIL on both bars** · [analysis](ANALYSIS.md).

## Conditions

- **Engine:** `d0a60b6e`, the W-259 build `caa30980` plus the frozen
  pre-registration. Node v24.13.0, darwin, 10 cores.
- **Load:** another session was active on the machine (SR-WORK-SESSION
  decision 12). The 1-minute load average was **2.97–4.86 for the whole run**
  (`uptime` before each block and arm; `load1` on every row). **No (a) block and
  no (b) trial ran above 6, so nothing was re-run.**
- **(a) corpora:** fresh copies of fux-lab
  `scratch/shared-runtime/rung-{01000,10000}-v7`, re-made by
  `2026-10-04-node-graph-read/evidence/migrate.sh` in a new scratch directory.
  `accel.is_fresh` was true before and after all four blocks.
- **(b) deciding corpus:** `git archive d0a60b6e` of this repo, excluding
  `work/golden` (see Deviations), plus `fux build`: 2 103 docs, fresh. The two
  rung copies were run the same way and decide nothing.

## (a) The read against the rebuild

Twelve frozen queries per rung. One discarded warm-up per cell per arm, then 9
ABBA repeats, timing the wall time of each whole `node node/fux.mjs` process.
That is **960 timed processes; return code 0 on all of them, and each cell
printed exactly one stdout across its 20 processes** (identity gate held).

| rung × verb | S | W | outcome | read / rebuild, ms per cell (range of medians) |
|---|---:|---:|---|---|
| rung-01000 · find | +1.30 % | 9/12 | null | 53.8–73.5 / 53.6–73.7 |
| rung-01000 · ask | +1.76 % | 12/12 | null | 52.8–75.1 / 54.2–78.0 |
| rung-10000 · find | **+9.48 %** | **12/12** | **null** | 83.3–271.7 / 102.3–291.7 |
| rung-10000 · ask | **+9.71 %** | **12/12** | **null** | 82.4–266.7 / 101.2–283.5 |

**Headroom (SR-RS decision 22):** a wall-time endpoint has no ceiling. Each of
the 12 cells in each block could move either way, so improvement headroom and
regression headroom are both 12 of 12 per block. **This null is not a
saturated endpoint.** At rung-10000 every cell moved in the read's favour, by
about 15–19 ms, and the effect is smaller than the frozen bar.

## (b) One graph build per Node process

These are W-243's 24 spike comparisons, with `FUX_GRAPH_REBUILD=1` on every arm
and 5 trials, the arms rotated.

| corpus | n-proc / one-proc-once (trials) | median | n-proc / one-proc-rebuild median | identity |
|---|---|---:|---:|---|
| **this repo (deciding)** | 1.562 · 1.575 · 1.588 · 1.540 · 1.606 | **1.575** | 1.366 | 24/24 × 5 |
| rung-01000-v7 (reported) | 4.406 · 3.978 · 4.310 · 4.476 · 4.380 | 4.380 | 4.300 | 24/24 × 5 |
| rung-10000-v7 (reported) | 2.026 · 2.013 · 2.092 · 1.996 · 2.021 | 2.021 | 1.908 | 24/24 × 5 |

The prototype's memo reported **1 build and 23 hits** per process on this repo.
On the rungs it reported 1 build and 7 hits: 16 of W-243's 24 repo-specific
query cells return nothing there, so those cells are mostly process start-up,
which is why the rung ratios run high. **They decide nothing.**

(a) in W-243's shape, the switch unset (`b-read-fux.jsonl`): n-proc /
one-proc = 1.309 · 1.179 · 1.385 · 1.493 · 1.281, median **1.309**. This is for
the record only, because the arm may not read.

## Outcome against the frozen rules

- **(a) is NULL at rung-10000, the deciding rung.** The read stays. The result
  goes to Arpit and to the compare doc's Fork A row. It is not a reopen-trigger.
- **(b) is 1.575 against 5.0, so W-243 step 1 stays STOP.** (a) is ineligible
  for CI, and its W-243-shaped ratio of 1.309 would not have cleared the bar
  either.

## Deviations (stated; no threshold moved, and the pre-registration is untouched)

1. **The instruments were not committed before their first run.** The
   pre-registration required that, but this session may not commit.
   `bench_a.py`, `bench_b.py`, `once-hook.mjs`, `once-process.mjs` and
   `analyze.py` were written to the frozen spec immediately before running and
   were not edited afterwards. Each is filed here as it ran.
2. **The (b) prototype is harness-only.** `once-hook.mjs` is a
   `module.registerHooks` load hook. It wraps the shipped `planeFor` in memory
   with a memo keyed like `Resident`: the stamp digest plus every shard's name,
   size and mtime, recomputed on every call, and that cost is inside the timing.
   **No engine file changed**, and the identity gate shows the bytes match.
3. **`work/golden` was excluded from the `git archive` snapshot** for L11
   hygiene. `.fux/sources/dirs` already excludes it from the index, so the
   committed index the queries read is unchanged.
4. **The trial count for (a) in W-243's shape was not frozen.** It used 5
   trials alternating order, the same count as (b).

## Authorship

| artifact | author | could reach |
|---|---|---|
| the pre-registration, every script in `evidence/`, this report, ANALYSIS, VERDICT | the W-259 builder session (Claude Code, Opus) | none: no question set, judgment or score is involved. The queries are the frozen identity-run list and W-243's spike list |

`informed`: the builder of the read set the bars and measured them.

## Reproduce

```text
S=<scratch> work/regression/2026-10-04-node-graph-read/evidence/migrate.sh
git archive HEAD -- . ':(exclude)work/golden' | tar -x -C $S/fux-snap && (cd $S/fux-snap && fux build)
E=work/regression/2026-10-04-node-graph-speed/evidence
for r in rung-01000 rung-10000; do for v in find ask; do python $E/bench_a.py $S/$r $r $v a.jsonl; done; done
python $E/bench_b.py $S/fux-snap fux-snapshot b-fux.jsonl          # deciding
python $E/bench_b.py $S/fux-snap fux-snapshot b-read-fux.jsonl --read
python $E/analyze.py a.jsonl b-fux.jsonl b-read-fux.jsonl
```
