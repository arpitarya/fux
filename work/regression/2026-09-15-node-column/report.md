---
type: Report
run: 2026-09-15-node-column
item: W-179
classification: surface capture
description: "Node's query latency, measured for the first time, as a COLUMN beside Python's. The Node reader is FLAT in corpus size — 26.3 ms at 100 documents and 26.4 ms at 1 000 — and every bit of its growth is W-161's in-memory graph rebuild, which takes a Node ask to 269.5 ms at 1 000 and about 2.4 s at 10 000."
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

## docs-10000 — the tier where it stops being a cost and becomes a wall

**One timed call, `node fux.mjs ask` in the prepared work dir: `real 2.40 s`.**

⚠ **That is one call, under load from the sweep then running** — it is a
magnitude, not a p50, and it is labelled as one.

🔴 **Against N4's retired fence — `p95 ≤ 150 ms` — the split decides the
answer**: `B-node-nograph` clears it by 5× at every tier measured;
`B-node` misses it by 1.8× at 1 000 documents and by more than an order of
magnitude at 10 000.

## What this run does NOT establish

- **N4 is not ruled.** A benchmark rules no threshold (decision 6). What N4 gets
  from this run is **a number where it had none**.
- **Nothing about quality.** Ranked lists were captured; no judgement was made.
- ⚠ **`B` is an editable install pointing at the working tree**, so it reports
  `2.0.1` and is not the published `2.0.1`. **Two runs of "arm B" are not
  necessarily the same engine**, which is worth knowing about every filed
  benchmark number, not just this one.

## Machine and contention — stated, not buried

⚠ **The `docs-00100` tier was measured while this session ran the unit suite on
the same machine.** Interleaving protects the *difference* between arms and
never the absolute number
([SR-WORK-SESSION](../../../records/0060_WORK-session.md) decision 12, and the
2026-09-12 correction that established the distinction). **The comparisons stand;
the absolute milliseconds at that tier do not.**

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
