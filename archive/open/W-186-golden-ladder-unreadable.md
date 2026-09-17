---
type: OpenItem
id: W-186
title: "W-186 — every golden rung is unreadable by HEAD: `fux.index.v2`, and two retired config keys"
description: "All eight frozen rungs carry a v2 index, a tune.toml with the three priors W-152 removed, and a fux.toml with the urls_file key W-164 moved. HEAD refuses all of them, so every read verb fails on every rung. Found 2026-09-15 while gathering W-181's latency capture."
status: open
lane: agent
timestamp: 2026-09-15T00:00:00Z
filed: 2026-09-15
ball: agent
---

# W-186 — the golden ladder cannot be read by the engine

**Model: Sonnet** for the re-ingest and the stamps; **Opus** only if the
ordering question in *Out of scope* turns out to matter.

**Found 2026-09-15**, taking a scratch copy of `rung-10000` for
W-181's latency capture (closed 2026-09-15). Three refusals,
in order, on a plain `fux ask`:

```
error: .../rung-10000/.fux/tune.toml: [ranking] `archived_weight` was REMOVED
       on 2026-09-13 (W-152).
error: .../rung-10000/fux.toml: [sources.url] urls_file moved to [sources]
       urls_file (2026-09-14)
error: shard .../00.jsonl declares _format 'fux.index.v2', this engine writes
       'fux.index.v3'
```

**All eight rungs carry all three.** `rung-seed` · `00100` · `00200` · `00500` ·
`01000` · `02000` · `05000` · `10000` — checked, not assumed:
`grep -c 'archived_weight\|superseded_weight\|recency_half_life_days'` returns
**3** on every one.

## Why it matters more than a stale fixture

🔴 **Four queued items measure on this ladder and not one of them can run**:
[W-180](W-180-b-sweep-run.md) (the frozen `b` sweep),
[W-154](W-154-rerank-weight-cost.md) Part B,
[W-175](W-175-correction-generalisation.md), and W-136's phase 5. Each is 🟢 or
🟣 on something other than this, so the queue currently says they are ready and
**they are not**.

⚠ **Nothing detected it.** A rung is exercised by a session that goes looking;
no test, hook or CI arm reads one, so a `_format` bump and two key retirements
landed over nine days and the ladder went quiet without a word.

## This is a KNOWN step, not an emergency

[`work/golden/README.md`](../golden/README.md) already decides it, twice: a
rung's index is *"built once per engine version and recorded in
`ladder/rung-NNNNN.index`"*, and the running instruction is **"use the rung's
own index — do not re-ingest; check the engine version matches
`ladder/rung-NNNNN.index`; if it does not, re-ingest that rung once, update the
record, and say so in the report."**

**So the work is the documented step, performed.** What makes it an item rather
than a footnote is that it is eight rungs, it changes committed bytes in frozen
corpora, and four things are waiting on it.

## Definition of done

1. **The two config retirements applied to every rung** — the three `[ranking]`
   priors deleted from `.fux/tune.toml`, `urls_file` moved up one level in
   `fux.toml`. ⚠ Deleting the priors is byte-neutral for ranking: all three
   shipped at their no-op values, which is why W-151/W-152 could remove them.
2. **Each rung re-ingested once** with `fux ingest --full`, and
   `ladder/rung-NNNNN.index` updated — engine version, document count,
   `index_root_sha256`, `rung_head_commit`.
3. ⚠ **The MANIFESTS are not touched.** `ladder/rung-NNNNN.sha256` hashes the
   **documents**, and no document changes here. If a manifest check fails after
   a re-ingest, something is wrong with the re-ingest and not with the manifest.
4. **Verify by asking**, per the README: one `fux ask` per rung, from inside the
   rung, that returns results and a band.
5. **Say so in a report**, which is the README's own instruction and the thing
   that makes the next session's numbers comparable.

## Out of scope

- **Any ranking claim.** This is a maintenance step; it measures nothing.
- **Rebuilding a rung's documents.** The corpus is frozen and stays frozen.
- ⚠ **Whether a re-ingest should have been automatic.** A gate that re-ingests
  frozen corpora on a version bump would be writing to a frozen thing without a
  person asking — a bigger decision than this item, and not one to take while
  clearing a backlog.

## Closes

Unblocks [W-180](W-180-b-sweep-run.md),
[W-154](W-154-rerank-weight-cost.md) Part B and
[W-175](W-175-correction-generalisation.md).
