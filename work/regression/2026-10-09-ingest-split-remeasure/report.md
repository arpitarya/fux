---
type: Report
description: "W-267 - the unchanged delta ingest at fux-lab rung-10000 (gen 4, scratch copy) re-timed on the fixed engine, three interleaved repeats, identical root sha. N (delta non-extract) = 4.902 s median, 4.894-4.908 s on all three: under the frozen 5 s bar with no straddle. Full 9.44 s, full/delta 1.92x. redact is 0.96 s. The rule's first branch: B-002 may close, and that is Arpit's ruling."
run: 2026-10-09-ingest-split-remeasure
item: W-267
classification: informed
filed: 2026-10-09
---

# Report: the unchanged delta on the fixed engine

**Pre-registration:** [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md), frozen at
`d8113b7f`. **Instrument:** `tools/quality-controls/ingest_split.py`, unchanged,
run once (`run <copy> --repeats 3`). **No deviation.** A latency run: no ranking
claim and no per-query rows. The evidence rows are one per timed run, with `id`
and `arm`.

## Setup, as pre-registered ([`evidence/setup.txt`](evidence/setup.txt))

- Engine `0fec04d1` (3.0.0-alpha.11 + this session's commits). `src/fux/ingest/`,
  `src/fux/store/` and the instrument are **byte-equal to the freeze commit**
  (`git diff d8113b7f HEAD` on those paths is empty).
- Lab `ed46bfef`; rung-10000 (**generation 4**) HEAD `99fe0b4d`.
  `rungs.verify` → `[]` before the copy **and on the copy after its re-ingest**.
  `fux ingest --full` in the copy wrote **0 shards**, so this engine reproduces
  the rung's committed index byte for byte. The lab tree was untouched (`?? fux.toml`
  only, as before).
- Machine: macOS, 10 cores, Python 3.14.3. Load average **2.00–2.15**
  throughout, under half the core count (5), so no repeat was re-taken. No other
  agent session was running; this session ran nothing else while timing.

## The numbers (seconds; wall clock around `ingest.run`, fresh process each)

Validity: **identical root sha across the warm-up and all six timed runs**
(`3b557e62…`); every delta had `changed == 0`, `reused == 10000/10000`.

| run | total | extract | **non-extract (N)** | walk | parse | redact | before:write | write | tail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| delta-1 | 4.894 | 0.000 | **4.894** | 0.831 | 1.419 | 0.963 | 0.857 | 0.697 | 0.114 |
| delta-2 | 4.908 | 0.000 | **4.908** | 0.861 | 1.422 | 0.958 | 0.852 | 0.687 | 0.114 |
| delta-3 | 4.902 | 0.000 | **4.902** | 0.836 | 1.426 | 0.963 | 0.857 | 0.691 | 0.115 |
| full-1 | 9.436 | 3.828 | 5.608 | 0.828 | 1.386 | 0.966 | 1.481 | 0.760 | 0.174 |
| full-2 | 9.436 | 3.813 | 5.623 | 0.830 | 1.384 | 0.963 | 1.501 | 0.761 | 0.171 |
| full-3 | 9.419 | 3.809 | 5.610 | 0.832 | 1.382 | 0.967 | 1.486 | 0.759 | 0.172 |

(`edges` is 0.013 s on every run; `before:extract`/`before:edges` ≤ 0.001 s.)

- **N = 4.902 s** (median). **All three deltas are under 5 s** (4.894 / 4.908 /
  4.902): no straddle. ⚠ **The margin is 0.092 s, under 2 %.** On another machine,
  or under load, the same engine could land on the other side.
- walk + parse share of N: 0.460 / 0.465 / 0.461. Not dominant, and it does not
  matter, because that clause only applies at N ≥ 5 s.
- `redact` **0.96 s** (W-264's memoisation holds; the 2026-10-04 run measured
  5.85–6.01 s). ⚠ That comparison crosses corpus generations (gen 3 there, gen 4
  here) as well as engines; the addendum's same-corpus figure was 1.03–1.09 s.
- Full/delta on median totals: 9.436 / 4.902 = **1.92×**.

## Authorship ([SR-RS](../../../records/0133_predictions.md) decision 13)

| artifact | author | could reach |
|---|---|---|
| the rung (gen 4) | the gen-4 rebuild session, 2026-10-05, from `seed/` | the seed corpus; nothing of this run |
| the instrument | Claude Code, 2026-10-04 (W-256), unchanged | the engine and the copy; **none** of queries, judgments or prior scores. There are no queries: the endpoint is a clock |
| the pre-registration and the run | Claude Code, 2026-10-09 (W-267) | the 2026-10-04 run's numbers (the reason for the re-run), the code and the rungs; **not** `work/golden/` answers |

## Verdict, against the frozen rule

**N < 5 s → the first branch: B-002 closes, the dirty list stays advisory, and
option D is not needed at the design point.** [VERDICT](VERDICT.md). W-267 DoD 4
sends the closure to Arpit; the inbox row is filed in this change.
