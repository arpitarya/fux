---
type: Index
title: Archive — implemented doc artifacts
description: Completed handoffs, prompts, and proposals — moved here with status implemented + ADR links; the rebuild's finished-work trail.
timestamp: 2026-07-21T00:00:00Z
---

# Archive — implemented doc artifacts

Handoffs, prompts, and proposals that have been **fully implemented** land here, in
the same change that completes them (CLAUDE.md law). Each arrives with frontmatter
updated: `status: implemented`, a link to its ADR, and its original path.

Distinct from the repo-level [`../../archive/`](../../archive/) (the old,
non-working build): this directory is the *completed-work trail* of the rebuild.
Active directories (`../handoff/`, `../proposals/`) hold live work only.

**Naming.** Archived handoffs/prompts are keyed by the **release version they
shipped**, not their in-flight `NNNN` index (CLAUDE.md law, 2026-07-22):
`vX.Y.Z-name-{handoff,prompt}.md`. Orchestrator/meta docs that map to no single
release stay unversioned.

## Shipped artifacts

| Version | Feature | Docs |
|---------|---------|------|
| **v0.20.0** | Query CLI v1 (setup/ingest/BM25F/ask/find/answer) | [handoff](v0.20.0-query-cli-v1-handoff.md) · [prompt](v0.20.0-query-cli-v1-prompt.md) |
| **v0.21.0** | Ingest v1.1 (web/CDP/advanced tier) | [handoff](v0.21.0-ingest-web-advanced-handoff.md) · [prompt](v0.21.0-ingest-web-advanced-prompt.md) |
| **v0.22.0** | Hybrid engine v2 (bundled model + RRF) | [handoff](v0.22.0-hybrid-engine-v2-handoff.md) · [prompt](v0.22.0-hybrid-engine-v2-prompt.md) |
| **v0.23.0** | Knowledge substrate v3 | [handoff](v0.23.0-knowledge-substrate-handoff.md) · [prompt](v0.23.0-knowledge-substrate-prompt.md) |
| **v0.24.0** | Debug & observability v4 | [handoff](v0.24.0-debug-observability-handoff.md) · [prompt](v0.24.0-debug-observability-prompt.md) |
| **v0.25.0** | Trust & currency (supersession + answer confidence floor) | [handoff](v0.25.0-trust-currency-handoff.md) · [prompt](v0.25.0-trust-currency-prompt.md) · proposals: [staleness](v0.25.0-staleness-ranking-ignores-supersession.md), [honest-decline](v0.25.0-honest-decline-well-formed-queries.md) |
| *(spans v0.20–v0.22)* | Master orchestrator prompt | [master-prompt.md](master-prompt.md) |
