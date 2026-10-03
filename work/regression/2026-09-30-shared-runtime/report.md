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

---

# Tier 1 — Node reads the plane (2026-10-03, Claude Code, Opus)

## ⚠ Deviation, stated before the numbers: the byte-identity base moved

The frozen `base` arm is Node at `5aaf3969`, and the frozen corpora are the
`fux.index.v6` copies. **Between Tier 0 and Tier 1 the index format moved to
`fux.index.v7`** (W-168 step 8's removal, Arpit's option (c)). `base` cannot read
v7, and this engine refuses v6. So, for Tier 1 only:

- **corpora**: `rung-01000-v7` and `rung-10000-v7`, new copies of the scratch
  copies, re-ingested at v7 beside them. The v6 copies are untouched. `fux` is
  this repo at its committed v7 index.
- **base**: `t1-base`, Node at `a62409ed`. That is Tier 0 plus the step-8
  removal, which was itself shown byte-identical, 120/120, before and after on a
  copy of rung-01000 with git history.

`bench.py` is unchanged. It takes the entry point and the corpora as arguments.
No threshold moved.

## Decision 1 — stdout byte-identical: ✅ 9/9 cells, all three arms

| corpus | verb | `t1-base` | `t1-plane` (`--fast`) | `t1-scan` (`--scan`) |
|---|---|---|---|---|
| fux | find | `a4d88dac9cdc` | same | same |
| fux | ask | `6542cb63c8fc` | same | same |
| fux | answer | `e3a17bf668da` | same | same |
| rung-01000 | find | `446c55c2b034` | same | same |
| rung-01000 | ask | `fc3ee40552f6` | same | same |
| rung-01000 | answer | `bff630406c2d` | same | same |
| rung-10000 | find | `d079a959b4d7` | same | same |
| rung-10000 | ask | `f93ac8249751` | same | same |
| rung-10000 | answer | `829258979d2e` | same | same |

Rows: `evidence/bench-t1-base.jsonl`, `bench-t1-plane.jsonl`,
`bench-t1-scan.jsonl`. Every cell had rc 0 and was stable over 8 runs.

## Decision 3 — the arm: ✅ 0 discordant everywhere

`evidence/t1_arm.py` checks three things on every query:

- Node scan, Node plane and Python plane have the same **candidates**, `n`,
  `total_wlen` and `df`, at `skipping=False`, so the plane's set is complete.
- Node plane at `skipping=True` gives the same **ranking** as Node scan at tops
  1, 5 and 20.
- Node `--fast` gives the same **stdout** as the scan for `find`, `ask` and
  `answer`.

| corpus | queries | candidate checks | ranking checks | stdout checks | discordant |
|---|---|---|---|---|---|
| fux (record titles; no source walk, W-244) | 98 | 196 | 294 | 120 | **0** |
| rung-10000-v7 (`queryset.generate`) | 134 | 260 | 390 | 90 | **0** |
| adversarial (this index + `adversarial_corpus.py`, `fux build`) | 98 | 196 | 294 | 60 | **0** |

`tools/differential/node_arm.py` on `rung-01000-v7` gave **0 of 225**, with
`ranked_by` now compared rather than excluded.

## Decision 4 — speed: the trigger did NOT fire

Warm medians in seconds, 1-minute load 2.5–2.8:

| corpus | verb | plane | scan | base |
|---|---|---|---|---|
| rung-01000 | find | 0.052 | 0.056 | 0.055 |
| rung-01000 | ask | 0.055 | 0.057 | 0.057 |
| rung-10000 | find | **0.090** | 0.129 | 0.127 |
| rung-10000 | ask | **0.090** | 0.133 | 0.126 |
| fux | find | **0.107** | 0.161 | 0.149 |

The plane is below the scan on both rungs. **On rung-01000 the margin is 2–4 ms
on a shared machine, which is real by the bar's wording and nothing more.** At
1 000 documents the remaining cost is the graph-plane rebuild, which Fork A
(Arpit's, open) would remove.

## Suites at the Tier 1 commit

See the commit message. The new tests are `tests/derive/test_node_accel.py`
(10), `tests/derive/test_idx_fixture.py` (2) and `node/test/accel.test.mjs` (4).
