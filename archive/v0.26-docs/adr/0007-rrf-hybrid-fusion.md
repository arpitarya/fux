---
type: ADR
title: ADR-0007 — hybrid retrieval via Reciprocal Rank Fusion
description: BM25F candidates + dense over candidates only, fused with RRF (k=60); --lexical-only preserves v1 byte-for-byte; no reranker.
timestamp: 2026-07-21T00:00:00Z
---

# ADR-0007: RRF hybrid fusion

- **Status:** accepted
- **Date:** 2026-07-21
- **Feature:** handoff 0003 M5 — fusing lexical and dense retrieval

## Context

BM25F and dense similarity produce incomparable score scales. The query-engine
compare doc chose RRF — rank-based, calibration-free, and the literature's
consistent recall-lifter — and *closed* the reranker question (cross-attention
models start ~80 MB, 8× the budget; the eval set is the only thing that can
reopen it).

## Decision

- **Pipeline:** BM25F top `candidate_pool` (200) → dense similarity computed
  **over candidates only** (never the full corpus — the stdlib-speed
  invariant) → `RRF(d) = Σ 1/(k + rank)` with k=60 → final order. Config under
  `[engine.hybrid]` (`enabled`, `rrf_k`, `candidate_pool`).
- **Determinism:** every stage tie-breaks on (score, file, ordinal); dense
  similarity is exact int8 math; RRF is rational arithmetic on ranks.
- **`--lexical-only` is byte-identical to v1** — enforced by the pre-v2 e2e
  goldens, which pass unchanged under the flag.
- **Graceful fallbacks, all silent-but-visible:** missing bundle, all-OOV
  query, or empty dense set → pure lexical (`engine: bm25f` in the output);
  chunks missing vectors → lexical-only ranking for those chunks + one stderr
  warning to re-ingest.
- **Explainability:** every fused result carries `bm25f_rank`, `bm25f_score`,
  `dense_rank`, `similarity`, `rrf` (JSON always; human under `--explain` as
  `bm25f rank 1 (score 7.4) + dense rank 2 (sim 0.83) → rrf 0.0325`).
  The headline `score` becomes the RRF value when fused — the engine field
  says which scale you're reading.
- **`answer`** reuses hybrid retrieval and multiplies in a question-similarity
  factor `(0.5 + 0.5·max(0, sim))` from the same model — skipped entirely on
  the lexical path so `--lexical-only` answers match v1.

## Alternatives considered

- Weighted score mixing (`α·bm25 + β·cos`) — rejected: needs per-corpus
  calibration RRF doesn't; brittle across corpora.
- Dense-first retrieval over the full corpus — rejected: breaks the
  candidate-only stdlib-speed math and buys nothing at per-repo scale.
- Bundled cross-encoder reranker — closed decision, unchanged (see context).

## Consequences

Easier: paraphrase queries rescue lexically-weak-but-present documents;
agents can audit the fusion per result. Harder: a document with *zero* lexical
term overlap (not even stopwords) never enters the candidate set — the
recorded trade, measured in ADR 0006's eval notes.

## References (required)

- Query-engine compare doc (verdict, RRF, no-reranker + reopen-trigger):
  [../compare/query-engine.compare.md](../compare/query-engine.compare.md)
- Cormack, Clarke & Buettcher, *Reciprocal Rank Fusion outperforms Condorcet
  and individual rank learning methods* (SIGIR 2009):
  https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
