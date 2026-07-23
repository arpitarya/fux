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
implemented proposals move to [`../archive/`](../archive/). Nothing here is a
commitment; everything here is findable.

# Index

* [Research-to-Spec](research-to-spec.md) - evidence-backed specs; every claim cites the corpus at a commit.
* [Knowledge diff & time-travel](knowledge-diff.md) - `fux diff`/`fux log`; ask questions of past knowledge.
* [Hybrid degrades at scale](hybrid-degrades-at-scale.md) - ✅ **RESOLVED (2026-07-22)**: the acme-payments realistic run settles it — the hybrid collapse was a **corpus artifact** (hybrid hit@5 .182→.855, parity with lexical). RRF reopen-trigger answered: no fusion/reranker change warranted. Residual threads split to the two proposals below.
* [Staleness — retrieval ignores supersession](../archive/v0.25.0-staleness-ranking-ignores-supersession.md) - ✅ **implemented (v0.25.0)**: annotate-not-down-rank ([ADR-0013](../adr/0013-supersession-awareness.md)) — moved to `../archive/`.
* [Honest-decline too permissive](../archive/v0.25.0-honest-decline-well-formed-queries.md) - ✅ **implemented (v0.25.0)**: absolute floor built + calibrated, shipped disabled — no value clears all five gates ([ADR-0014](../adr/0014-answer-confidence-floor.md)) — moved to `../archive/`.
* [Audit evidence trail](audit-evidence-trail.md) - deterministic cited answers as an auditable chain; seed of the deferred Plane.
* [Knowledge substrate v2](knowledge-substrate.md) - **the** consolidated post-v0.22 proposal: SQLite substrate (bulk text in-db), doc-index-IS-the-graph, one kernel / six projections, FuxVec binary dense search, git tiers, enterprise inputs, build milestones. Absorbed the document-knowledge-graph, corpus-at-scale, and fuxvec docs.

*(The fourth idea from the 2026-07-21 ideation — the **product-memory corpus**,
Arpit's own seed — was the winner and graduated straight into
[`../PLAN.md`](../PLAN.md) §"Why the corpus lives in git" and the v1
handoff, per the proposals lifecycle.)*
