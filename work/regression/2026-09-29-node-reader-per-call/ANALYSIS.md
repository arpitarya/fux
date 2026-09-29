---
type: Analysis
description: "Why a Node query cost ~0.5 s, what fixed it, and what is left."
---

# W-235 — analysis

## Diagnosis

- **The graph tier parsed every committed record in full.** `compose.mjs`'s
  `allRecords` ran `JSON.parse` on all 1 851 lines (10 000 on the rung) to feed
  `buildPlane`, which reads only `id` and `edges`.
- **`terms` is ~95 % of a record's bytes**, so almost all the parse — and the
  garbage the collector then paid for — was data nothing used.
- **`rawRecordLines` split shards with a JS loop over every byte** (~120 ms of
  a 544 ms query), shared by the scan and the plane.

## Changes, each with a repro command

1. **`graphRecords(root)`** (`node/src/store/reader.mjs`): walk each line's
   top-level keys on raw bytes, `JSON.parse` only `id` and `edges`, stop when
   both are found. A line it does not recognise falls back to a full parse.
   All four plane builders use it: `query/compose.mjs`, `index.mjs`'s
   `_plane`, and `verbs/graph.mjs`'s three verbs, whose three copies of
   `allRecords` are gone.

   ```bash
   node work/regression/2026-09-29-node-reader-per-call/evidence/equal.mjs . .
   ```

2. **`rawRecordLines` splits with `Buffer.indexOf`**, native, same output.

3. **Pinned by** `node/test/graph-records.test.mjs`: escaped quotes and
   brackets in strings, keys out of order, whitespace, no `edges`, an escaped
   key, and a `terms` value that is not JSON (proving the skim stops at `id`).

## What is left

- **The profile is flat after the change.** File reads, `scanCandidates` and
  start-up lead; `graphRecords` + `buildPlane` together are ~20 ms. There is no
  single cost left worth a design change.
- **Python's 0.26 s (W-235 §1) was measured in process**, with no interpreter
  start-up; Node's 0.15 s here is a whole CLI process. They are not the same
  measurement, and this run does not compare them.
- **Unresolved:** the CI cells are slower than this machine (1.24 s vs 0.49 s
  before). The speed-up there is expected to be of the same ratio and is
  **not measured**; the next FULL stage's wall time is where it will show.
