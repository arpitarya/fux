---
type: Verdict
name: PRE-REG-NODE-GRAPH-SPEED
description: "W-259: FAIL on both frozen bars. (a) The graph.json read is consistently faster at rung-10000 (read faster in 12 of 12 cells for find and for ask) but saves a median 9.48 % (find) and 9.71 % (ask) against a frozen 10 % bar, so the frozen outcome is NULL, not loss. (b) One graph build per Node process gives a median 1.575x against a frozen 5.0x, so W-243 step 1 stays STOP."
verdict: FAIL
prediction: PRE-REG-NODE-GRAPH-SPEED
pre_registration: work/regression/2026-10-04-node-graph-speed/PRE-REGISTRATION.md
run: 2026-10-04-node-graph-speed
item: W-259
filed: 2026-10-05
classification: informed
---

# VERDICT: FAIL. Neither bar clears

**(a) Read against rebuild: NULL by the frozen rule at both rungs.** The verdict
is rung-10000's.

| rung × verb | S (median saving) | W (read faster) | frozen outcome |
|---|---:|---:|---|
| rung-01000 · find | +1.30 % | 9 / 12 | null |
| rung-01000 · ask | +1.76 % | 12 / 12 | null |
| **rung-10000 · find** | **+9.48 %** | **12 / 12** | **null** (bar: S ≥ 10 % and W ≥ 10) |
| **rung-10000 · ask** | **+9.71 %** | **12 / 12** | **null** |

The read is faster in every rung-10000 cell, by about 15–19 ms per query. It
misses the frozen 10 % by about half a percentage point on both verbs. **The bar
does not move** (SR-RS decision 10b). By the pre-registration's (c), a null
means: **the read stays**, it is recorded in the compare doc's Fork A row, it
goes to Arpit, and it is **not** a reopen-trigger. The "loss" rule did not fire
anywhere.

**(b) One graph build per Node process: 1.575× median against a frozen 5.0×.
W-243 step 1 STAYS STOP.**

| deciding corpus | n-proc / one-proc-once, trials 1–5 | median | n-proc / one-proc-rebuild, median |
|---|---|---:|---:|
| this repo, `git archive` of `d0a60b6e` + `fux build` | 1.562 · 1.575 · 1.588 · 1.540 · 1.606 | **1.575** | 1.366 |

Building the plane once per process adds about 0.21× on top of what one process
already buys. The rest of each comparison is the scan. Both identity gates
held:

- (a): every cell printed one stdout across all 20 of its processes, with
  return code 0, in 960 of 960.
- (b): 24 of 24 comparisons matched in every trial.

(a) in W-243's shape, for the record only: the median n-proc / one-proc with
the read is **1.309×**. It is ineligible in any case (the arm forbids the read).

`informed`: the session that built the read wrote the bars and measured them.
