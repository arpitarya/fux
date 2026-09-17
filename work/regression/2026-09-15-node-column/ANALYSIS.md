---
type: Analysis
run: 2026-09-15-node-column
description: "Why the Node reader is flat where Python is not, what the graph tier actually costs, and the two things this run changes for W-161 rather than for W-179."
filed: 2026-09-15
---

# ANALYSIS — the reader is flat; the tier is the cost

## 1 · Why the two readers scale differently

**Python's `ask` grows with the corpus and Node's does not**, and the reason is
structural rather than a quality of either implementation:

| | Python | Node |
|---|---|---|
| candidate generation | the **accelerator** — mmap'd runtime segments, built by `fux build` | a **scan** of the committed shards |
| graph plane | reads **one derived file** (SR-NODE-SEARCH decision 17a) | **rebuilds it in memory**, parsing every committed record |

At 100 and 1 000 documents the scan is simply cheap, and Node's constant
26.3 / 26.4 ms is dominated by process start. **The accelerator earns its keep at
a size neither of these tiers reaches** — which is a statement about the tiers,
not about the accelerator.

🔴 **So the interesting comparison is not Node against Python.** It is
`B-node` against `B-node-nograph`: **36.9 ms at 100 documents and 243.1 ms at
1 000**, from a tier that ships **on**.

## 2 · What this changes, and it is mostly W-161's problem rather than W-179's

W-179 asked *what does the Node reader cost*. The answer is **26 ms, flat**.

But the run's load-bearing number belongs to
[W-161](../../open/W-161-graph-composed-ask.md), whose own queue row says both
tiers *"ship on and unmeasured"*:

- **The tier's price is now measured on one reader**, and it grows roughly
  linearly with the corpus: ~37 ms per 100 documents at the small tier, ~243 ms
  at 1 000, ~2.4 s at 10 000 from a single timed call.
- ⚠ **This says nothing about the tier's price on Python**, which reads a
  derived file instead of rebuilding. A Python-side measurement is a different
  run and is not owed here.
- ⚠ **And it says nothing about the tier's VALUE.** W-161's two arms need
  link-dependent questions that are Codex's and gated on 2026-09-30. **A cost
  without a benefit is half an argument**, and this run supplies only the half
  that was cheap.

## 2a · The 10 000 tier, measured — and one claim of §1 needs narrowing

The two-tier draft of this analysis said the Node reader is **flat**. With the
third tier in, the honest statement is **sub-linear, not constant**:

| corpus | reader (tier off) | the tier's price |
|---|---|---|
| 100 | 26.3 ms | 36.9 ms |
| 1 000 | 26.4 ms | 243.1 ms |
| **10 000** | **42.7 ms** | **3 157 ms** |

**The reader grows 16 ms across a 100× corpus; the tier grows 3 120 ms.** The
shape of the argument is unchanged and the wording is corrected rather than left
to flatter.

🔴 **And the tier's growth is steeper than linear in the corpus** — ×6.6 from
100→1 000, ×13 from 1 000→10 000 — which is what rebuilding a graph plane by
parsing every committed record, once per query, looks like from outside.

## 3 · What I would not conclude from it

1. **"Node is faster than Python."** True at these tiers, on this machine, with
   the tier off — and the accelerator exists precisely for sizes above them.
   **Two tiers is not a curve.**
2. **"The graph tier should be off by default."** That is a trade against a
   benefit nobody has measured. Naming the price is not the same as ruling on it,
   and decision 6 says a benchmark rules nothing.
3. **"N4 passes."** A benchmark rules no threshold. N4 now has a number where it
   had none, and **which** number it gets depends entirely on the arm.

## 4 · The specific changes

| # | change | repro |
|---|---|---|
| 1 | `NODE_ARMS`, `ask_node`, `node_version` and `--node-arms` in `bin/bench.py` — the column, timed inside the same repeat as Python's arms | `bench.py latency … --node-arms B-node,B-node-nograph` |
| 2 | **N4 is measured**, and no longer *unmeasured* in any document | SR-WORK-BENCHMARK decision 12 |
| 3 | W-148 row 2 discharged; the item closes | `work/OPEN-WORK.md` |

## 5 · Unresolved

- 🔴 **The tier's price on the Python reader.** Different mechanism, different
  run, not owed here.
- 🔴 **The tier's VALUE, on either reader.** W-161's arms, gated on Codex.
- ⚠ **The harness is uncommitted.** `fux-benchmark` is scratch by decision 13;
  the column added for this run exists on one machine, and this analysis is the
  only place that says what it does.
- ⚠ **`docs-00100`'s absolute numbers are contended** — the unit suite ran
  beside them. The arm-to-arm differences are what survive.
