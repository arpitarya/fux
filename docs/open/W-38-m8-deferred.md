# W-38 — M8: the deferred set

**Status:** **PARKED** — parked with triggers, never ambient.
**Blocked by:** W-26
**Spec:** [`PLAN.md` §M8](../PLAN.md)
**Gate:** **one ADR + Arpit sign-off, each.** Nothing here starts because
it is interesting.

## The set

| item | note |
|---|---|
| realistic-workload pruning | **Optimization only.** Could shrink T1/T2; **cannot block anything.** [ADR-0003](../adr/0003-pruning-criterion-rerun.md) killed it as a premise |
| sentence-unit selection + format-aware structure extractor | spine retest, Graphify-inspired |
| query-log views | [`proposals/query-log-pruning.md`](../proposals/query-log-pruning.md) |
| the `enriched` AI ingest tier | needs the pinning contract; naming is [ADR-0001](../adr/0001-ingest-mode-naming.md) |
| BIC codec inside T2 | superseded for the committed plane; survives only here |
| MCP adapters | [`proposals/mcp-adapters.md`](../proposals/mcp-adapters.md) — the escape valve that keeps the M4 adapter cap honest |
| knowledge-CI | [`proposals/knowledge-ci.md`](../proposals/knowledge-ci.md) |
| wavelet self-index | [`proposals/wavelet-self-index.md`](../proposals/wavelet-self-index.md) |

## The standing law

**Pruning work is forbidden outside this item.** If pruning appears in any
other milestone's diff, that is a plan violation, not a bonus.
