---
type: Analysis
name: node-column-analysis
description: "What exact reader parity buys, why the CAP-4 hazard was worth checking by hand even though it did not materialise, and the interpreter trap that lands at the end of a long run."
---

# What the zero means, and what it does not

## `max |Δscore| = 0.000000` is a stronger claim than *the lists match*

Two readers can produce identical orderings from different arithmetic — ties
broken the same way by luck, or scores that differ below the sort's resolution.
**The parity file records the largest absolute score difference at any compared
rank, and it is exactly zero on all 60 queries.**

So the two readers are not merely agreeing about order; they are computing **the
same numbers**. That is what the differential law's third arm was for, and it is
the claim `node/README.md` has been making without a measurement behind it.

⚠ **It is one index, one tier, one machine.** Parity is a property that can
break on a branch neither reader took here — the differential arm exists because
*"both readers saw the same drifted bytes and agreed perfectly"* is a failure
mode, not a success.

## The CAP-4 hazard did not materialise, and checking it was still right

W-188 named a specific way the column could lie: if Node's `--band` payload
lacked the `confidence` block, **every Node row would read `answered`** and the
column would look like a fabrication machine.

**It has the block, in full.** One question by hand, then 52 measured: 0 differ
in verdict, band or citation.

🔴 **The check was cheap and the alternative was not.** A missing block does not
produce an error — it produces a column of plausible numbers that says the Node
reader never declines. Nobody comparing `answered 24 / declined 18` against
`answered 52 / declined 0` would suspect a schema gap first; they would suspect
the reader. **A hazard that is disproven in one command is worth the command**,
and the item was right to demand it before the sweep.

## The interpreter trap, and why it belongs in MACHINE.md

`python3` is **3.9.6** on this machine. `bench.py`'s `report` imports `tomllib`
(3.11+); **every other subcommand runs fine on 3.9**.

So the failure lands **after** prepare, latency, hits, answers and rankdiff —
about three minutes of measurement — and it lands as a `ModuleNotFoundError`
that looks like a broken harness rather than a wrong interpreter. The evidence
was already written; only the HTML was not. **The fix is one interpreter on one
line**, which is exactly the shape `work/MACHINE.md` exists for.

## What is still open after this run

- **The other two tiers.** `docs-01000` and `docs-10000` would say whether parity
  holds as the corpus grows, which is where a reader divergence would most
  plausibly appear (different accumulation order, different float paths).
- **The graph tier's worth**, which is W-161's and needs a corpus with links —
  [W-191](../../open/W-191-the-ladder-carries-no-links.md).
- **The abstention shape**, seen a fourth time and belonging to W-176.

## Cost

About four minutes of measurement: 14 s prepare, 2 min 30 s latency, 9 s hits,
18 s answers, and rankdiff/report in under a second each.
