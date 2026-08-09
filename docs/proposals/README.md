# Proposals — parked ideas

Ideas worth keeping that are **not being built now**. Same rigor as a compare doc
(context, sketch, grounded references) but for future work rather than an active
fork. Per OKF, every proposal carries frontmatter:

```yaml
---
type: Proposal
title: <idea>
description: <one line>
status: proposed        # proposed | graduated | rejected
timestamp: <ISO 8601>
---
```

Lifecycle: `proposed` → picked up → **graduates** into a compare doc (if there's a
fork) or a plan entry (if not), and this file's status is updated with a link. Fully
implemented proposals move to [`../archive/`](../archive/README.md). Nothing here is a
commitment; everything here is findable.

# Index

**Filed 2026-08-09 for the v0.30 architecture:**

* [MCP as the adapter endgame](mcp-adapters.md) - one protocol instead of per-app adapters; org's own auth. Graduates on the first MCP-gateway design partner or a fourth adapter request.
* [Knowledge CI](knowledge-ci.md) - PRs fail when the index is stale; decisions the diff contradicts surface as cited review comments. Graduates after M6 dogfoods green two weeks.
* [Wavelet-tree self-index](wavelet-self-index.md) - research note preserving the rejected option C of the keyspace compare; reopens only on a law change or a P5 bottleneck.

**Carried over — architecture-agnostic survivors:**

All three survivors are architecture-agnostic and, if anything, *strengthened*
by the v0.30 index-and-refer rebuild (the MST keyspace gives knowledge-diff and
the audit trail their substrate natively — see [`../PLAN.md`](../PLAN.md) M8+):

* [Research-to-Spec](research-to-spec.md) - evidence-backed specs; every claim cites the corpus at a commit.
* [Knowledge diff & time-travel](knowledge-diff.md) - `fux diff`/`fux log`; ask questions of past knowledge. Natural fit for the one-root-hash keyspace.
* [Audit evidence trail](audit-evidence-trail.md) - deterministic cited answers as an auditable chain; seed of the deferred Plane. The ledger's sha@index + fresh-sha citations are its raw material.

**v0.26-era proposals** (tied to the archived substrate engine) moved to
[`archive/v0.26/proposals/`](../../archive/v0.26/proposals/):
knowledge-substrate (the SQLite substrate — superseded by the index-and-refer
architecture), chunk-level-dense-codes, hybrid-degrades-at-scale (✅ resolved
2026-07-22 as a corpus artifact). Earlier implemented proposals remain in
[`../archive/`](../archive/README.md) as before.

*(The fourth idea from the 2026-07-21 ideation — the **product-memory corpus**,
Arpit's own seed — graduated into the v0.26 plan; its successor concept lives on
as the committed index + ledger of the current architecture.)*
