---
type: Report
run: 2026-09-15-node-column
item: W-179
classification: surface capture
description: "Node's query latency, measured for the first time, as a COLUMN beside Python's, at three tiers. The Node reader grows 26.3 -> 26.4 -> 42.7 ms across a 100x corpus; W-161's in-memory graph rebuild grows 37 -> 243 -> 3157 ms and is the whole of the difference. The tier-off arm clears N4's retired p95 fence at every tier; the shipped arm misses it by 36x at 10 000."
filed: 2026-09-15
---

# REPORT — the Node latency column

**Not a paired run** in SR-RS decision 22's sense: no judged queries, no quality
endpoint, no threshold. [SR-WORK-BENCHMARK](../../../records/0053_WORK-benchmark.md)
decision 6 — *a benchmark rules no threshold* — applies, so this is a **surface
capture** and files no verdict.

## What decision 12 asked for, and what this is

> **The ruling (Arpit, 2026-09-14):** add the Node measurement to
> `fux-benchmark` in the same shape as Python's — same rungs, same `p95`, **one
> more column**. Not a second harness and not a second report.

**Four arms, interleaved inside every repeat**, so all four see the same machine:

| arm | what it is |
|---|---|
| `A` | Python, fux 1.0.0 |
| `B` | Python, the working tree (reports `2.0.1`; it is an editable install) |
| `B-node` | the **vendored** Node reader in `B`'s own work dir, as shipped |
| `B-node-nograph` | the same reader with `[graph] ask_boost` and `ask_related` **off** |

🔴 **The fourth arm is decision 12's second paragraph, and without it this run
produces a confidently wrong number.** W-161 makes a Node `ask` rebuild the
graph plane **in memory, parsing every committed record** — work the Python
reader does not do, because it reads one derived file
([SR-NODE-SEARCH](../../../records/0153_node-search.md) decision 17a).

## The result

| arm | docs-00100 p50 / p95 | docs-01000 p50 / p95 |
|---|---|---|
| `A` — Python 1.0.0 | 51.9 / 52.8 ms | 208.0 / 212.8 ms |
| `B` — Python HEAD | 77.7 / 78.8 ms | 231.2 / 238.2 ms |
| `B-node` — as shipped | 63.2 / 63.8 ms | **269.5 / 276.7 ms** |
| `B-node-nograph` | **26.3 / 26.7 ms** | **26.4 / 26.8 ms** |

60 queries per tier, median of each query's repeats, then p50 and p95 of those
medians. Never a mean.

### 🔴 The finding: the Node READER is flat, and the TIER is everything

**26.3 ms → 26.4 ms across a 10× corpus.** The Node reader's own cost does not
move with the corpus at all, and it is roughly **a third of Python's** at 100
documents and **a ninth** at 1 000.

**Every bit of the growth is the graph rebuild:**

| tier | `B-node` − `B-node-nograph` = the tier's price |
|---|---|
| docs-00100 | **36.9 ms** |
| docs-01000 | **243.1 ms** |

⚠ **Read the naive column and you get the opposite answer.** `B-node` 269.5 ms
against `B` 231.2 ms at 1 000 documents says *the Node reader is slower than
Python*. It is not: it is **8.7× faster**, and a tier that
[W-161](../../open/W-161-graph-composed-ask.md) ships **on and unmeasured** costs
ten times the reader. That is exactly the misattribution decision 12 named in
advance.

## docs-10000 — measured, and the split becomes a chasm

Run separately at **1 warm-up + 3 repeats** (the other tiers use 2 + 5) — a
deliberate reduction, because a Node `ask` there costs seconds and a benchmark
rules no threshold. Stated rather than quietly applied.

| arm | p50 | p95 |
|---|---|---|
| `A` — Python 1.0.0 | 2009.3 ms | 3999.4 ms |
| `B` — Python HEAD | 1952.2 ms | 4458.6 ms |
| `B-node` — as shipped | 3200.3 ms | 5488.6 ms |
| `B-node-nograph` | **42.7 ms** | **83.7 ms** |

🔴 **The graph tier costs 3 157 ms at 10 000 documents** — 75× the reader it is
bolted to.

⚠ **The reader is not perfectly flat after all**, and that is worth saying
plainly: 26.3 → 26.4 → **42.7 ms** across 100 → 1 000 → 10 000. It grows
**sub-linearly and by 16 ms across a 100× corpus**, against Python's 52 → 208 →
1 952 ms. *Flat* is the shape; it is not literally constant.

### 🔴 N4's retired fence, and the arm decides it

| arm | `p95` at 10 000 | against `≤ 150 ms` |
|---|---|---|
| `B-node-nograph` | **83.7 ms** | ✅ **clears it**, at every tier measured |
| `B-node` | 5 488.6 ms | ❌ misses by **36×** |

**N4 is not ruled** — decision 6 — but it now has a number, and *which* number
depends entirely on whether the graph tier is counted as the reader's cost.

## What this run does NOT establish

- **N4 is not ruled.** A benchmark rules no threshold (decision 6). What N4 gets
  from this run is **a number where it had none**.
- **Nothing about quality.** Ranked lists were captured; no judgement was made.
- ⚠ **`B` is an editable install pointing at the working tree**, so it reports
  `2.0.1` and is not the published `2.0.1`. **Two runs of "arm B" are not
  necessarily the same engine**, which is worth knowing about every filed
  benchmark number, not just this one.

## Machine and contention — stated, not buried

🔴 **Every absolute number in this run is contended, and the 10 000 tier worst
of all.** Three separate things were on this machine during it: the unit suite
(during `docs-00100`), W-154 Part B's ~2 000 subprocesses (during `docs-10000`),
and **a concurrent Cowork session**, which the queue's in-flight marker surfaced
only afterwards.

**Interleaving protects the DIFFERENCE between arms and never the absolute
number** ([SR-WORK-SESSION](../../../records/0060_WORK-session.md) decision 12,
and the 2026-09-12 correction that established the distinction). So:

| claim | status |
|---|---|
| `B-node-nograph` is far cheaper than every other arm, at every tier | ✅ stands — the arms are interleaved |
| the graph tier is the whole of Node's growth | ✅ stands — same reason |
| Python at 10 000 costs ~2 s | ❌ **do not quote it.** The filed 2026-09-12 benchmark puts it near 400 ms; this run says the machine was busy, not that the engine got slower |

⚠ **Two sessions shared this machine and neither told the other in advance.**
Decision 12 asks for the disclosure; it got it late, from a queue marker.

## Headroom

**Not a paired run.** No arms over judged queries, so decision 22's disclosure
does not apply.

## Reproduce

```console
$ python3 bin/bench.py prepare --run <id> --corpus docs-01000 --arms AB
$ python3 bin/bench.py latency --run <id> --corpus docs-01000 --arms AB \
      --node-arms B-node,B-node-nograph --path scan
```

⚠ **`fux-benchmark` is scratch and its harness is uncommitted**
(SR-WORK-BENCHMARK decision 13). The `NODE_ARMS` column added for this run lives
on one machine, and nothing in fux would notice it going.
