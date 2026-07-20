---
type: Proposal
title: Audit evidence trail — who knew what, when, from where
description: Provenance frontmatter + git history + deterministic answers = an auditable knowledge chain for regulated work.
status: proposed
timestamp: 2026-07-21T00:00:00Z
tags: [compliance, provenance, audit]
---

# Audit evidence trail

## Signal

Every fux answer is already deterministic, extractive (verbatim source sentences),
and cited to `file:line`; every cached file carries source, sha256, converter, and
fidelity; the corpus lives in git with full history. That is, structurally, an
**evidence chain**: the same question at the same commit produces the same cited
answer, forever. Regulated domains (finance — Arpit's day job; healthcare; legal)
pay for exactly this property, and no LLM-based tool can offer it (non-determinism
breaks the chain).

## Sketch

- `fux answer --audit` — emits the answer plus a verifiable bundle: corpus commit
  hash, source shas, chunk ids, ranking explanation.
- A CI check that re-runs recorded Q→A pairs and fails if answers drift (knowledge
  regression testing).
- Long-term: this is the seed of the deferred compliance Plane from the old vision —
  reactivate only on a real design partner.

## Why parked

Real, differentiated, and monetizable — but it needs a paying context to shape it,
and the old build's pre-mortem verdict stands: don't build fleet/compliance features
before the fleet exists. Graduates when: an enterprise/regulated design partner (or
Ameriprise-adjacent use) materializes.

# Citations

[1] [Knowledge as Code](https://knowledge-as-code.com/) — automated verification / drift detection as a core pattern (accessed 2026-07-21).
[2] Internal: [`../compare/packaged-model.compare.md`](../compare/packaged-model.compare.md) — determinism/extractiveness that makes answers reproducible evidence.
