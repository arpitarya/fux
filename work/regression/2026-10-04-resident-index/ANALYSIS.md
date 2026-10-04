---
type: Analysis
description: "W-249 analysis: identical surfaces license the resident index; they do not license a claim about staleness (the tests own that), ranking, or memory as a bound."
run: 2026-10-04-resident-index
item: W-249
---

# Analysis: what identical surfaces license

**Licensed:** `fux mcp` and `fux serve` may keep the loaded index through `store/resident.py` ([SR-MCP](../../../records/0136_mcp.md) decision 13), and Node's `fux mcp` its `Shards`. On an index that does not move, a held index prints what the per-call path printed, including on the second asking, which is the call residency serves.

**Not licensed:**

- **Staleness.** No capture changes the index mid-session. Six tests in `tests/test_resident.py` and four in `node/test/resident.test.mjs` cover the stamp moving, `--no-accelerator` (the stamp does not move), no runtime at all, an identical stamp rewrite, and a mid-call change. Each was checked to fail with the key cut down to the stamp alone.
- **Ranking.** These captures compare the engine with itself.
- **Memory or latency as a bound.** One machine, one run: shape, not a threshold.
- **The Index-tab difference** is HEAD's own hash-seed tie order in `inspect/lenses.py` and is owed its own fix.
