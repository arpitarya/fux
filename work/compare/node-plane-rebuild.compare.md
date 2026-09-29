---
type: Compare
description: "W-235 — how the Node reader stops paying ~80 % of every query to rebuild the graph plane. Options: a cheaper rebuild (parse only id and edges), a lazy rebuild, or reading Python's derived graph.json when fresh. Option 1 built: find/ask/answer ~0.50 s → ~0.15 s on this repo and on rung-10000, output byte-identical, no contract change."
---

# The Node graph-plane rebuild — cheaper, lazier, or not at all?

> **Verdict:** ✅ **O1 built, 2026-09-29 (Claude Code, Opus).** The rebuild
> now parses only `id` and `edges` from each record and never `terms`. A Node
> `find`, `ask` or `answer` dropped from **~0.50 s to ~0.15 s**, on this repo
> and on `rung-10000`, with byte-identical stdout. The graph build is now
> ~20 ms of a 174 ms query, so **O2 has nothing left to save**. **O3 is not
> needed**, and [SR-NODE-SEARCH](../../records/0153_node-search.md) decision 9
> stands unchanged.

| | |
|---|---|
| **status** | ✅ **O1 built** ([W-235](../../archive/open/W-235-node-reader-per-call-cost.md)). O2 and O3 not taken |
| **the call** | O1: `graphRecords()` in `node/src/store/reader.mjs` skims each record line's top-level keys on raw bytes and `JSON.parse`s only `id` and `edges` |
| **confidence** | **high**: the plane digest is equal on 1 851 and 10 000 records, stdout is byte-identical on six verb × corpus cells, and the arm is at 0 discordant on both passes. The timings are one machine, medians of 7 |
| **reopen-trigger** | a Node `find` on a corpus ≤ 10 000 documents spends **more than half** its CPU profile in `graphRecords` + `buildPlane` + GC again; **or** the record writer stops sorting keys, so `terms` precedes `id` (the skim stays correct and becomes a full walk) |

## Context

- **The cost.** A Node `find` on this repo took 1.24 s on a 2-core CI cell and
  0.49 s locally. About 80 % of it was building the graph tier's input:
  `JSON.parse` on every committed record, then collecting the garbage.
- **Why every record.** The plane needs every document's edges, not the
  candidates' (the tier exists to find what the words missed).
- **Why it was so expensive.** A record is ~95 % `terms` by bytes. The plane
  reads two fields, `id` and `edges`, and never looks at `terms`.

## Options

| | option | contract change | measured cost of a `find` (this repo) |
|---|---|---|---|
| **O0** | leave it | none | **0.49 s** median |
| **O1** | **parse only `id` and `edges`**; split shards with native `indexOf` | none — the output is equal to a full parse by construction; a line the skim cannot read falls back to one | **0.14 s** median |
| **O2** | build the plane lazily, only when a query reaches the tier | none | the tier runs whenever the window is non-empty, which is every query that returns anything. After O1 the build is ~20 ms, so O2 saves at most that on a query with results and ~0 overall |
| **O3** | read Python's `.fux/runtime/graph.json` when fresh | **yes** — SR-NODE-SEARCH decision 9, Arpit's | not measured. Its ceiling is the ~20 ms O1 leaves, bought with a freshness check and the loss of N2's independence (plane.mjs's docstring) |

## Matrix — what O1 does to the differential law

| check | result |
|---|---|
| `graphRecords` vs a full parse, field for field | 0 mismatched of 1 851 (this repo) and 10 000 (`rung-10000`) |
| plane digest, lean vs full input | equal on both corpora |
| stdout, before vs after, `find`/`ask`/`answer` | byte-identical, 6 of 6 cells |
| `node_arm.py . --python-tune off`, both passes (ordinary, adversarial) | **0 of 225** discordant on each; N2 digest IDENTICAL on the adversarial index — [the run](../regression/2026-09-29-node-reader-per-call/report.md) |

## Consequences

- **Every Node consumer pays ~0.35 s less per call** on a corpus this size.
- **CI's arm pays it ~2 700 times a run**, so the FULL stage shortens with no
  change to coverage.
- **The skim is a second JSON reader in the tree.** It is bounded: it reads
  top-level keys only, parses the values it keeps with `JSON.parse`, and hands
  any line it does not recognise to a full parse.

## References

- [W-235](../../archive/open/W-235-node-reader-per-call-cost.md) — the item and its measurements.
- [SR-NODE-SEARCH](../../records/0153_node-search.md) decisions 9 and 17 — the asymmetry O3 would change.
- [`2026-09-29-node-reader-per-call`](../regression/2026-09-29-node-reader-per-call/report.md) — the filed run.
