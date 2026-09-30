---
type: Report
description: "W-242, the shared runtime plane — Tier 0 (a Node query reads each committed shard once): stdout byte-identical to base on all 9 cells in every one of 5 timed runs (45 cells), and the shard-read spy test green. Both of Tier 0's pre-registered clauses pass. Wall time is not a Tier 0 clause, and on this shared machine it could not separate the arms. Tiers 1 and 2 are not built."
run: 2026-09-30-shared-runtime
item: W-242
classification: blind
filed: 2026-09-30
pre_registration: work/regression/2026-09-30-shared-runtime/PRE-REGISTRATION.md
---

# Report: the shared runtime plane — Tier 0

Judged against [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md) §"What decides". No
threshold moved. **Only Tier 0 is built.** Tiers 1 and 2 have their own arms in
the same bar and have not run.

## Tier 0 — the two clauses

| clause | result |
|---|---|
| **1 — stdout byte-identical** to `base`, rc 0, every cell | ✅ **9/9 cells**, in all five runs below: 45 of 45 sha256 equal, every run `stable` (the eight processes in a cell printed one output) |
| **2 — at most one read per shard per query**, a spy test | ✅ `node/test/shard-reads.test.mjs`. It spies on `fs.readFileSync`, so a path that bypasses the reader's `Shards` object is counted too. It fails above one read per shard on `find`, `ask`, `answer` and `ask -q`, and it failed at 3 on the pre-Tier-0 reader. It also asserts that two calls read twice, which is the cross-call cache the item forbids |

**Tier 0 passes.**

## Wall time — reported, decides nothing

Warm medians of 7 (s), [`evidence/bench.py`](evidence/bench.py), unchanged since the
`base` run. The rows are `evidence/bench-<label>.jsonl`.

| cell | `base` | `base-rerun` | `base-rerun2` | `t0` | `t0-rerun` |
|---|---:|---:|---:|---:|---:|
| fux · find | 0.168 | 0.150 | 0.241 | 0.245 | 0.140 |
| fux · ask | 0.176 | 0.171 | 0.208 | 0.245 | 0.161 |
| fux · answer | 0.168 | 0.310 | 0.219 | 0.200 | 0.240 |
| rung-01000 · find | 0.065 | 0.100 | 0.097 | 0.077 | 0.081 |
| rung-01000 · ask | 0.066 | 0.100 | 0.101 | 0.073 | 0.075 |
| rung-01000 · answer | 0.072 | 0.089 | 0.114 | 0.075 | 0.081 |
| rung-10000 · find | 0.144 | 0.172 | 0.234 | 0.166 | 0.165 |
| rung-10000 · ask | 0.144 | 0.257 | 0.239 | 0.205 | 0.177 |
| rung-10000 · answer | 0.147 | 0.227 | 0.225 | 0.220 | 0.236 |

- ⚠ **The same arm moves by up to 1.8× between runs** (base, fux · answer:
  0.168 → 0.310). That is wider than any difference between the arms, so **no
  speed claim is made for Tier 0.** The profile that motivated it (769 shard
  opens for 257 shards, `rawRecordLines` 207 of 383 ms) came from the Cowork
  VM's mount, where an open costs far more than on this SSD.
- **Load.** One-minute load was 4.1–5.5 on every timed cell, below the bar's re-run
  threshold of 6. The machine was shared with other Claude Code sessions
  throughout (SR-WORK-SESSION d12). `t0-rerun` and `base-rerun2` ran in the
  reverse order of `base-rerun` and `t0`, so drift in the load cannot favour one
  arm.
- **Who ran what.** `base` was taken by the building agent before any code
  changed. The four later runs were taken by the parent session: base from the
  bundle committed at `6744cb78`, Tier 0 from the Tier 0 bundle, on
  `fux-lab/scratch/shared-runtime/rung-{01000,10000}-v6` (the v6 re-ingested
  copies the bar describes; the un-suffixed folders there are still v5). The
  original `base` rows' sha256s equal the later ones cell for cell, so they read
  the same corpora.

## Headroom

**This is not a paired run** in [SR-RS](../../../records/0133_predictions.md)
d22's sense. It scores no relevance and no question set. Its correctness claim
is byte equality of whole stdout per cell, and its timing decides nothing. There
is no query that "could have changed" in either direction to count.

## Authorship

| artifact | author | could reach |
|---|---|---|
| `PRE-REGISTRATION.md`, `evidence/bench.py` | the W-242 step 0 session, before any code | none: no question set, judgment or score is involved |
| the Tier 0 code, `node/test/shard-reads.test.mjs`, `bench-base.jsonl` | a background build agent of the 2026-09-30 session, which stalled twice before committing | none |
| `bench-base-rerun*.jsonl`, `bench-t0*.jsonl`, this report | the parent session, which also decided W-168 step 8 and W-237 that day | none relevant: the corpora are unscored rungs, and the endpoint is stdout bytes |

## Suites at the Tier 0 commit

Node **209/209**. e2e **158 passed, 1 skipped**. Unit: green except
`test_work_queue_rules_have_one_home`, which reads other sessions' worktrees under
`.claude/worktrees/` as if they were live documents. Two failures inherited from
`6744cb78` (the 0063 Components block and the 0110/0131 content hashes) were
restamped in the same commit.
