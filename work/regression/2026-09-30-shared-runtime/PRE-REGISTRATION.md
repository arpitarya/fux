---
type: Pre-registration
name: shared-runtime
description: "W-242 step 0 — frozen before any code: Node find/ask/answer wall time on fux, rung-01000 and rung-10000, before and after each of T0 (one read per shard), T1 (Node reads .fux/runtime/) and T2 (Node builds it). Endpoint wall time; stdout byte-identical on every cell; the plane byte-identical across builders."
run: 2026-09-30-shared-runtime
item: W-242
frozen: 2026-09-30
---

# W-242 — pre-registration

**Frozen 2026-09-30, before the first line of `node/` changed.** A latency and
equality run, not a ranking run: no golden question, key or score is read, so
the classification is `blind` and SR-RS decision 22's paired bar does not
apply — nothing is scored per query.

## The arms

| label | what runs | built from |
|---|---|---|
| `base` | Node, today | `git archive 5aaf3969 node src/fux/constants.toml` into a scratch dir |
| `t0` | Node after Tier 0 | the tree at the T0 commit |
| `t1-plane` | Node after Tier 1, with a fresh Python-built plane present | the tree at the T1 commit |
| `t1-scan` | the same, with `--scan` (or no plane), so the scan is timed on the same code | same |
| `t2-plane` | Node after Tier 2, reading a **Node-built** plane | the tree at the T2 commit |

## The cells — 3 verbs × 3 corpora

| corpus | query | where |
|---|---|---|
| `fux` | `rollback` | this repo |
| `rung-01000` | `incident` | `fux-lab/scratch/shared-runtime/rung-01000` — a copy of the kept rung, re-ingested to `fux.index.v6` because the kept one is v5. The kept rung is not touched (L9 — never the playground; never a kept corpus) |
| `rung-10000` | `incident` | same, `rung-10000` |

| verb | argv |
|---|---|
| find | `find Q --json --top 5` |
| ask | `ask Q --json --top 20 --band` |
| answer | `answer Q --json` |

Each corpus's own `tune.toml` is in force (no `--no-tune`): the graph tier and
`mined_weight` are what make Node read every shard three times, so turning the
tune off would time the one path this item does not change.

## The endpoint

**Wall time of one whole `node fux.mjs …` process**, `time.perf_counter()`
around `subprocess.run`, per cell:

- **warm** — the median of 7 runs, taken after the first.
- **cold** — the first run, one sample, reported beside the warm median.

⚠ **Deviation from the item, stated up front.** W-242 step 0 asks for
*"medians of 7, cold and warm"*. A truly cold page cache needs `sudo purge` on
macOS, which this session cannot run. So *cold* here is the first process in the
cell: one sample, not a median, and not a cold disk. It is reported. It decides
nothing.

The machine is shared with other Claude Code sessions. `uptime`'s load averages
are written beside every cell. **A cell timed at a 1-minute load above 6 is
re-run**, and both timings are kept.

## What decides — fixed before the first measurement

1. **Stdout is byte-identical** to `base` on every cell, for every arm, with
   return code 0. **One byte different fails the tier.** This is the whole
   correctness claim for T0, and half of it for T1 and T2.
2. **T0 — at most one read of each shard per query**, asserted by a test that
   spies on the reader (item step 3). Not a timing.
3. **T1 — the differential arm at 0 discordant**: `tools/differential/node_arm.py`
   on this repo, with a fresh plane present, then after `adversarial_corpus.py`
   and `fux build`. Plus Node-plane = Node-scan = Python-plane on candidates,
   `(n, total_wlen, df)` and order, on this repo and rung-10000.
4. **T1 — speed** is the compare doc's reopen-trigger (2), and nothing looser:
   if `t1-plane`'s warm median for `find` or `ask` is **not below** `t1-scan`'s
   on rung-01000 **or** rung-10000, the trigger has fired. The tier still
   ships, because its outputs are identical. The finding goes to Arpit and is
   not re-interpreted by whoever ran it.
5. **T2 — byte-identity.** A Node-built and a Python-built `.fux/runtime/`,
   `diff -r`, are identical on every file the build writes except
   `stamp.json`: every `DETERMINISTIC_FILES` member, every `postings/*.jsonl`
   and `*.idx`, every `anchors/*.json`. On this repo, rung-10000 and the
   adversarial index. **One byte different fails the tier** — the compare
   doc's reopen-trigger (1).
6. **T2 — the cross-read**: Python `--fast` answers from a Node-built plane,
   and Node from a Python-built one, at 0 discordant.

No threshold above moves after the first measurement (SR-RS decision 10b). A
result this document did not anticipate goes to Arpit.

## The instrument

[`evidence/bench.py`](evidence/bench.py), committed with this file and not
edited after the `base` run. Its rows go to `evidence/bench-<label>.jsonl`,
each carrying the cell, both timings, the load averages, the return code and
the stdout's sha256 — so the equality check reads the files, not a memory of
them.
