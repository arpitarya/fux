---
type: Handoff
name: W-249
description: "`fux mcp` and `fux serve` hold the loaded index across calls, keyed on `.fux/runtime/stamp.json`, re-reading when it changes — index RESIDENCY, which SR-MCP named as an unbuilt want needing its own decision. Not a query-result cache (W-242's refused T3). Ratified 2026-10-03 by delegation, NOT built."
item: W-249
filed: 2026-10-03
ball: agent
---

# W-249 — the long-running surfaces keep the index open

**✅ CLOSED 2026-10-04 — built, byte-identical** (Claude Code; an Opus subagent built, Opus 5.5 reviewed):
- `src/fux/store/resident.py`: one `Holder` per process keeps each shard's record lines and the parsed records; `fux mcp` brackets every `tools/call` and `fux serve` its `/ask`, `/answer`, `/graph` with `Holder.call()`. **Residency of the input, never a memo of an output** — W-242's T3 stays refused. Node's `fux mcp` keeps its `Shards` the same way.
- **The key is the stamp digest plus every shard's name, size and mtime_ns**, recomputed before each call: the stamp alone is not enough, since `ingest --no-accelerator`, a pull, a checkout or a merge move the shards and not the stamp (each test fails with the key cut to the stamp). Absent `.fux/runtime/` is a `None` half, never an error. The derived plane and committed config are NOT held — `fux build` rewrites the former in place, the latter changes with no key moving.
- **Gate:** 228 of 229 surface rows byte-identical on three roots (this repo, the same without runtime, a migrated copy of rung-10000); the one difference is a pre-existing `PYTHONHASHSEED` tie order in `inspect/lenses.py`, fixed in the next commit. Differential arm 0/225. Memory, reported: +184 MB at rung-10000, +296 MB on this repo; warm `fux_search` 342 → 48 ms and 499 → 93 ms. [Run](../../work/regression/2026-10-04-resident-index/report.md).
- Live successors: [SR-MCP](../../records/0136_mcp.md) d13, [SR-SERVE](../../records/0158_serve.md) d3, [SR-NODE-SEARCH](../../records/0153_node-search.md) d24.

**Model:** Claude Code, **Opus** — it decides when a resident index is stale,
and a wrong answer there is a correct-looking answer from the wrong index.

**From** backlog B-034. [SR-MCP](../../records/0136_mcp.md) Consequences:
*"Holding the index open across MCP calls is a real and unbuilt want … It needs
its own decision, and is not made here."* Today every tool call re-reads; the
module docstring claims the opposite (W-245 fixes the sentence either way).

**Ruling (by delegation).** `fux mcp` and `fux serve` keep the result of
`read_index` resident for the life of the process, **keyed on the digest of
`.fux/runtime/stamp.json`** (the same freshness signal W-242 made the contract
between both readers). Before each call the stamp is re-read (one small file);
on change the index is reloaded. **This is residency of the loaded index, not a
memo of query results** — W-242's compare doc parks T3 (a query-result cache)
and this item does not reopen it. Say so in the SR-MCP amendment, by name.

## Definition of done

1. One resident loader shared by `mcp.py` and `serve`'s server, keyed on the
   stamp digest; stdout/JSON byte-identical to the per-call path on every tool
   and tab (captured, filed).
2. A test: ingest → call → re-ingest → call returns the new index without a
   restart; and a stamp rewritten with identical bytes does not reload.
3. SR-MCP gains a decision (residency; not T3); SR-SERVE a sentence; the
   `[mcp]` output defaults unchanged. `sr-hash` restamped.
4. Both suites whole. Memory of a resident index on fux-lab rung-10000 is
   reported, not asserted.

## Hazards

- A `.fux/runtime/` that is **absent** (fresh clone, no `fux build`) must take
  the scan path exactly as today — the stamp key is `None`, never an error.
- W-242 Tier 2 (Node builds the plane) landed 2026-10-03; the stamp's shape is
  Python's and does not change. Coordinate on `stamp.json` only.
