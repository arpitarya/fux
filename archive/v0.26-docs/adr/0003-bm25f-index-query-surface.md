---
type: ADR
title: ADR-0003 — BM25F index (JSON, incremental) + ask/find/answer surface
description: Weighted-tf-then-saturate BM25F over heading/path/body; JSON index decided by measurement; extractive TextRank answers.
timestamp: 2026-07-21T00:00:00Z
---

# ADR-0003: BM25F index + the ask/find/answer query surface

- **Status:** accepted
- **Date:** 2026-07-21
- **Feature:** M4+M5 of handoff 0001 — retrieval + answers

## Context

Engine v1 is deterministic lexical retrieval (query-engine compare doc verdict);
the output shape (passages default, extractive cited `answer`) is the
query-output verdict; the verbs are the cli-surface verdict. Two open questions
from the handoff had to be answered by measurement/validation during build.

## Decision

- **Scoring is true BM25F** (weight term frequencies per field, *then* apply
  saturation once) — not per-field BM25 summed, which double-saturates and is
  the classic implementation mistake. Fields: heading (heading path + doc
  title), path (source path tokens), body. Defaults 3.0/2.0/1.0, k1=1.2,
  b=0.75, config-overridable. IDF = `ln((N−df+0.5)/(df+0.5)+1)`; length
  normalization uses the weighted length vs corpus average.
- **Index format: JSON** (`.fux/index/index.json`, `format: 1`) — open
  question 1 resolved by measurement on a synthetic 5k-chunk / 1.5M-word
  corpus: JSON parse 16 ms, in-memory postings build 525 ms, query 1.7 ms.
  The format is not the bottleneck; a struct-packed binary would save
  milliseconds of the 16 and cost debuggability and diffability. At Anton's
  real scale (hundreds of chunks) total load is tens of ms. If a dogfood corpus
  makes postings build hurt, the recorded escape hatch is persisting postings —
  not changing serialization.
- **Incremental:** the index stores per-file chunks keyed by source sha;
  unchanged files reuse their chunk records without re-reading the cache.
- **`fux answer` is extractive:** sentences (fences/tables/headings excluded,
  wrapped lines re-joined with line tracking) scored as normalized passage
  score × question-term overlap × TextRank centrality, then re-ordered into
  document order with `file:line` citations. Two quality guards earned by the
  fixture smoke: the overlap term ignores stopwords ("how are…" must not match
  every sentence containing "are"), and sentences under 35 % of the best
  sentence's score are dropped rather than padded in.
- **Explainability:** `--explain` exposes per-term idf, per-field tf and
  contribution (ask/find) and the per-factor product (answer) — the v3 "agent
  can see why" surface, shipped early because it fell out of the scoring loop.

## Alternatives considered

- struct-packed binary index — rejected by the measurement above.
- Per-field BM25 summed — rejected: not BM25F; over-rewards multi-field hits.
- Stopword removal in the *index* — rejected: BM25 IDF already discounts
  common terms at corpus scale and removal would change scores opaquely;
  stopwords are stripped only in the answer-overlap factor, where the fixture
  corpus proved the harm.
- Abstractive answers — permanently rejected (query-output compare): a ≤10 MB
  model cannot write faithful prose; we select and order, never generate.

## Consequences

Easier: scores are reproducible and explainable; the index diffs in git.
Harder: pure-paraphrase recall stays weak until engine v2 (RRF hybrid,
handoff 0003) — the accepted v1 trade.

## References (required)

- Query-engine + query-output + cli-surface compare docs (verdicts):
  [../compare/query-engine.compare.md](../compare/query-engine.compare.md),
  [../compare/query-output.compare.md](../compare/query-output.compare.md),
  [../compare/cli-surface.compare.md](../compare/cli-surface.compare.md)
- Robertson & Zaragoza, *The Probabilistic Relevance Framework: BM25 and
  Beyond* (BM25F): https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf
- Mihalcea & Tarau, *TextRank: Bringing Order into Texts* (EMNLP 2004):
  https://aclanthology.org/W04-3252/
