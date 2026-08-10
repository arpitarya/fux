---
type: ADR
title: ADR-0009 — one retrieval kernel, six verb projections, and PPR-lite expansion
description: Every verb becomes a view of one retrieve() call; the document graph is extracted deterministically and expanded by a fixed-iteration personalized PageRank.
timestamp: 2026-07-22T00:00:00Z
---

# ADR-0009: One retrieval kernel, six verb projections, PPR-lite expansion

- **Status:** accepted
- **Date:** 2026-07-22
- **Feature:** The retrieval kernel and graph surfaces (handoff 0004, M3/M4/M6)

## Context

v0.22 had three verbs (`ask`, `find`, `answer`) sharing a retrieval helper but
each owning its own assembly. Adding `explain`, `graph` and `path` on that shape
would have meant three more pipelines to keep in agreement — and the moment two
pipelines can disagree, the trust story ("query → seed → edge → passage") stops
being checkable.

Separately, the corpus already contained a graph nobody was reading: the links
authors wrote, the citation sections they kept, the crawl parentage the fetcher
recorded, the tags in frontmatter.

## Decision

**One kernel.** `retrieve(config, seed, ...) -> ResultGraph`, where `seed` is
either text or a `NodeRef`. Every verb is a projection:

| verb | seed | projection |
|------|------|------------|
| `ask` | text | passages |
| `find` | text | seed docs |
| `answer` | text | extractive synthesis over passages |
| `explain <doc>` | node | one node deep: outline + edges + key passages |
| `graph "<topic>"` | text | nodes + edges |
| `path <a> <b>` | two nodes | the paths slice, filtered a→b |

`explain` is genuinely `ask` seeded by a node: the document's own `top_terms`
(computed at ingest) become the query. There is no second retrieval path.

**Edges are extracted, never inferred.** Four kinds, each read off an artifact
that already exists — `references` (markdown links), `cites` (links under a
citations heading), `crawled_from` (recorded crawl parent), `tagged` (frontmatter
tags). All `EXTRACTED` grade; zero model calls. `INFERRED` exists in the schema
for a future host-session pass, and is weighted lower wherever it appears.

Two shaping choices worth naming:

- **`cites` is separated from `references`.** A link in a Citations section is
  evidence; a link in prose is a mention. Separating them lets path reliability
  and expansion treat them differently, which is the whole point of having
  grades.
- **Tags become `tag:` nodes, not doc↔doc edges.** N documents sharing a tag
  cost N edges rather than N², and any two of them still connect in two hops.

**PPR-lite expansion.** Personalized PageRank restricted to the seed
neighbourhood, with every constant fixed: damping 0.85, exactly 3 iterations,
top 10 expanded above 0.01, EXTRACTED 1.0 / INFERRED 0.6, 0.8 decay per hop, all
under `[engine.graph]`. Determinism is designed in — a **fixed iteration count
rather than a convergence test**, sorted adjacency traversal so float
accumulation order is stable, ties broken on doc id. Seeds are personalized by
retrieval *rank*, not score, because score is RRF on one path and raw BM25F on
another.

**The graph joins RRF as a list, not a bonus.** A document reached only by
traversal gets a voice through fusion and still has to be corroborated to rank
highly. `--lexical-only` and `[engine.graph] in_rrf = false` bypass it entirely.

### Handoff open question 2, answered by measurement

*"Does graph-expansion join RRF always, or only when lexical+dense agree
weakly?"* The instrument is `in_rrf`, and the honest answer is that **the
available eval set cannot discriminate**:

| corpus | graph in RRF | graph out | note |
|--------|--------------|-----------|------|
| fixture (21 pairs) | 0.810 / 1.000 / 0.873 | 0.810 / 1.000 / 0.873 | identical |

The reason is not subtlety — it is that **the fixture corpus contains no links
at all**, so PPR has nothing to walk. That was itself a finding: it is why the
M8 synthetic generator was built with real link structure, and why a separate
relational eval fixture now exists.

**Decision: ship `in_rrf = true` (always).** It never harmed the metric,
it demonstrably adds reachability (the relational eval exercises routes the
retrieval metrics cannot see), and the flag remains as the reopen instrument.
The conditional variant is *not* implemented, because implementing a heuristic
no measurement supports would be taste wearing evidence's clothes.

**Reopen trigger:** an eval set with relational questions — "which runbook does
this ADR depend on?" — on a corpus with genuine link density. Re-run both
settings before changing the default.

## Alternatives considered

- **Separate pipelines per verb** — rejected: three more code paths that can
  disagree, and the provenance story stops being checkable.
- **Conditional graph fusion** (only when lexical and dense agree weakly) — the
  handoff's alternative. Not implemented: no measurement supports it, and
  `in_rrf` keeps the question open at zero cost.
- **Iterate PPR to convergence** — rejected: reproducibility is a hard law here,
  and a convergence test makes the output depend on float noise.
- **ASCII-art graph rendering** — rejected (open question 4): unreadable past a
  handful of nodes, and the list form stays greppable and diff-friendly.

## Consequences

**Easier.** New verbs are projections, not pipelines. `--explain` and `path`
share one trust story because they read the same `ResultGraph`.

**Harder.** The kernel is now on the hot path for every verb, so its parity
obligations are absolute — all six v0.22 goldens are asserted byte-for-byte
through the re-plumb, on both storage backends.

**Owed.** Two correctness guards found during the build, both now tested:
graph fusion is skipped for node seeds (a neighbour's passage presented among a
document's own would misattribute it), and the edge frontier grows with the hop
count (collecting only seed-adjacent edges made `path --hops 2` report "no
route" for routes that exist).

## References (required)

- [PathRAG (arXiv:2502.14902, AAAI'25)](https://arxiv.org/abs/2502.14902) —
  nodes → flow-pruned scored paths → answers as one pipeline; the shape this
  kernel's paths projection follows.
- [GraphRAG vs HippoRAG vs PathRAG](https://medium.com/graph-praxis/graphrag-vs-hipporag-vs-pathrag-vs-og-rag-choosing-the-right-architecture-for-your-knowledge-graph-a4745e8b125f) —
  PPR-from-seeds as the cheap multi-hop operator; the "operators beat structure"
  reading this design takes (accessed 2026-07-21).
- [LiteSemRAG (arXiv:2604.16350)](https://arxiv.org/pdf/2604.16350) — the
  LLM-free graph-retrieval lane, which is the only lane Fux is allowed to be in.
- [Reciprocal Rank Fusion (Cormack et al., SIGIR 2009)](https://dl.acm.org/doi/10.1145/1571941.1572114) —
  why adding a weak-but-independent list to RRF is safe: fusion rewards
  agreement across lists rather than trusting any one list's magnitude.
- Internal: [ADR 0007](0007-rrf-hybrid-fusion.md) (the k=60 fusion this extends) ·
  [`../proposals/knowledge-substrate.md`](../proposals/knowledge-substrate.md) §4–§5.
