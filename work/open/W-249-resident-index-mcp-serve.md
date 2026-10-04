---
type: Handoff
name: W-249
description: "`fux mcp` and `fux serve` hold the loaded index across calls, keyed on `.fux/runtime/stamp.json`, re-reading when it changes — index RESIDENCY, which SR-MCP named as an unbuilt want needing its own decision. Not a query-result cache (W-242's refused T3). Ratified 2026-10-03 by delegation, NOT built."
item: W-249
filed: 2026-10-03
ball: agent
---

# W-249 — the long-running surfaces keep the index open

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
