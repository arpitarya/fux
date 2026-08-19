# W-38 — M8: the deferred set

**Status:** **PARKED** — parked with triggers, never ambient.
**Blocked by:** W-26
**Spec:** this file — see §Scope below (migrated from the retired `PLAN.md`, 2026-08-18)
**Gate:** **one ADR + Arpit sign-off, each.** Nothing here starts because
it is interesting.

## The set

| item | note |
|---|---|
| realistic-workload pruning | **Optimization only.** Could shrink T1/T2; **cannot block anything.** [P1-RERUN](../regression/2026-08-09-pruning-rerun/VERDICT.md) killed it as a premise |
| sentence-unit selection + format-aware structure extractor | spine retest, Graphify-inspired |
| query-log views | [`../proposals/query-log-pruning.md`](../proposals/query-log-pruning.md) |
| the `enriched` AI ingest tier | **named and fenced** by [ADR-ENRICHED](../../docs/adr/0017_enriched-mode.md) (**accepted** 2026-08-19) — it carries the pinning contract, the four candidate enrichments, and the L2 exclusion of prose summaries. That record explicitly does **not** authorize this work; this gate does |
| BIC codec inside T2 | superseded for the committed plane; survives only here |
| MCP adapters | [`../proposals/mcp-adapters.md`](../proposals/mcp-adapters.md) — the escape valve that keeps the M4 adapter cap honest |
| knowledge-CI | [`../proposals/knowledge-ci.md`](../proposals/knowledge-ci.md) |
| wavelet self-index | [`../proposals/wavelet-self-index.md`](../proposals/wavelet-self-index.md) |

## The standing law

**Pruning work is forbidden outside this item.** If pruning appears in any
other milestone's diff, that is a plan violation, not a bonus.

---

## Scope — M8 — deferred (parked with triggers, never ambient)

*Migrated verbatim from `PLAN.md` §M8 on 2026-08-18, when
that document was archived. **This file is now the spec**; there is no other.*

Realistic-query-workload pruning experiment — now purely an *optimization*
study (could shrink T1/T2; cannot block anything) · sentence-unit selection +
the format-aware structure extractor (spine retest, Graphify-inspired) ·
query-log views · the `enriched` AI ingest tier (pinning contract) · BIC codec
inside T2 · MCP adapters · knowledge-CI · wavelet self-index note.
