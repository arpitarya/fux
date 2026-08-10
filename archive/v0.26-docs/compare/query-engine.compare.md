---
type: Compare Doc
title: Query Engine
description: Staged hybrid — v1 BM25F, v2 bundled embeddings + RRF, v3 agent surface; sub-decisions resolved (no reranker, heading chunking, BM25F weights).
status: accepted
timestamp: 2026-07-21T00:00:00Z
---

# Query Engine — Comparison

> **Verdict:** **Staged hybrid, all three stages planned — and every stage stays
> `$0`, no *external* model.**
> **v1** — deterministic lexical retrieval by default: hand-rolled **BM25F**
> (field-weighted BM25) over chunked docs. Pure stdlib.
> **v2** — add a **packaged static-embedding model** (≤10 MB, bundled, no external
> service — see [`packaged-model.compare.md`](packaged-model.compare.md)) and fuse
> lexical + semantic rankings with **Reciprocal Rank Fusion (RRF)**. This is the
> "local embedding + reranking" stage.
> **v3** — agent-facing surface: the CLI answers questions and *explains* (which
> passages, why ranked) so an AI agent can `ask`, get replies, and get the reasoning
> — still no external LLM.
> **Status:** ✅ Accepted (Arpit, 2026-07-20) · **Confidence:** Medium-High
> Sub-decisions **resolved 2026-07-21** (research below): no bundled reranker (RRF
> only, revisit on eval evidence); chunking = structure-aware heading-based,
> 256–512 tokens; BM25F weights = heading 3.0 / path 2.0 / body 1.0, k1=1.2, b=0.75,
> all config-overridable.

## Context

The CLI answers natural-language questions over documents in configured folders, and
its primary caller is an **AI agent** using it to ask questions, get replies, and get
explanations. Hard constraint carried into this tool: **no external model or service
of any kind** — anything "smart" must be *built and packaged inside* this package and
stay small (≤10 MB) with no external deps (see
[`packaged-model.compare.md`](packaged-model.compare.md)). So the staged hybrid keeps
its `$0`/offline character at every stage; the semantic stage is a *bundled* model,
not an API.

## Retrieval algorithms — what to use (researched)

BM25 is the right default, but it isn't the only lever. The current (2026) consensus
for offline hybrid retrieval:

- **BM25 / BM25F / BM25+.** Sparse lexical. **BM25F** weights fields (title/heading vs
  body vs path) — a real precision win on structured Markdown, and free to compute.
  *Chosen for v1.*
- **Dense retrieval (embeddings).** Vectors + cosine; best on paraphrase. In-budget
  only via the bundled static-embedding model (v2).
- **SPLADE (learned sparse).** Term-expansion sparse vectors — great paraphrase recall
  with sparse-index efficiency, but it needs a trained neural model to encode →
  **out of the ≤10 MB / no-external-model budget.** Noted, deferred.
- **Cross-encoder reranking (e.g. MiniLM ms-marco).** +5–10 nDCG, but ~22 M params
  (~80–90 MB) → **out of budget.** Deferred; not v2.
- **Reciprocal Rank Fusion (RRF).** Combines *ranks*, not scores — `score = Σ 1/(k+rank)`
  (k≈60) — sidestepping the score-incompatibility that breaks weighted blends of
  heterogeneous retrievers. Research shows BM25+dense fused via RRF lifts recall@10
  from ~65 % (BM25) / ~78 % (dense) to **~91 %**. *This is our "reranking" for v2.*

**Net:** v1 = BM25F. v2 = BM25F + static-embedding dense, fused with RRF. SPLADE and
cross-encoders are the natural v-next upgrades *if* we ever relax the size/model
budget — recorded so a successor doesn't re-derive them.

## Options (engine shape)

- **A — LLM-first (external RAG).** Rejected — violates the no-external-model rule.
- **B — BM25F only.** v1 of the verdict; ships now, `$0`, weak on pure paraphrase.
- **C — BM25F + bundled dense, RRF-fused.** v2 of the verdict; semantic recall with no
  external model.
- **D — Staged B→C→(agent surface).** *(verdict)*

## Comparison matrix

| Criterion (weight) | A: External LLM | B: BM25F | C: BM25F+dense (RRF) | D: Staged |
|--------------------|-----------------|----------|----------------------|-----------|
| No external model (H, hard) | ✗ Fails | ✓ | ✓ (bundled) | ✓ |
| Paraphrase recall (H) | Best | Weak | Strong (~91 % w/ RRF) | Grows B→C |
| Cost / offline (H) | $/online | $0 offline | $0 offline | $0 offline |
| Determinism (H) | None | Full | Full (pinned model) | Full |
| Time-to-first-working (M) | Med | **Fastest** | Med | Fastest (ships as B) |
| Agent explainability (M) | Opaque | High | High | High |
| **Fit** | Rejected | v1 | v2 | **Verdict** |

## Analysis

### v1 — BM25F (deterministic, stdlib)
Ships immediately, `$0`, reproducible, air-gapped, trivial to keep fresh. Field
weighting on Markdown structure gives strong precision on curated corpora. Limit: pure
paraphrase with no shared terms. Good enough to dogfood in Anton this week.

### v2 — BM25F + bundled static embeddings, RRF-fused
Adds semantic recall for paraphrase using the packaged ≤10 MB model — no API, no
network. RRF fusion is the honest, score-calibration-free way to combine the two
rankings and is what the literature reports as the big recall jump. "Reranking" here =
RRF over the two candidate lists (not a heavy cross-encoder, which is out of budget).

### v3 — agent surface (ask / reply / explain)
The engine exposes not just ranked results but *why*: matched terms, field hits, RRF
contribution per source. An agent can `fux ask "…"`, read passages, and request an
`--explain` trace to decide whether to trust the answer or trigger an advanced ingest
pass on a thin file. Still deterministic; no generation.

## Sub-decisions — resolved with research (2026-07-21)

### 1. Reranker beyond RRF? **No — resolved.**
The gains cross-encoders bring (+5–10 nDCG, ~35 % accuracy lift over pure vector
retrieval) come from full query-document *cross-attention* — and the smallest
production-grade model doing that (ms-marco-MiniLM class) is ~22 M params, ~80–90 MB:
**8–9× over our 10 MB budget**. Nothing at ≤10 MB has demonstrated meaningful
reranking gains, and a static-embedding model *cannot* do cross-attention by
construction — it would just re-score with the same signal dense retrieval already
contributed to RRF. Meanwhile RRF alone lifts hybrid recall@10 to ~91 %. **Verdict:
no bundled reranker in v1/v2.** Revisit trigger (recorded, not vague): the Anton eval
set shows RRF plateauing — i.e. relevant passages retrieved in the candidate set but
persistently mis-ordered in the top 5.

### 2. Chunking unit — **structure-aware, heading-based. Resolved.**
2026 benchmarks are unambiguous: for content with inherent structure (exactly our
case — the ingest cache is Markdown *by design*), structure-aware splitting is "the
single biggest and easiest improvement" — chunking choice alone swings recall by up
to ~9 points, a 7-strategy benchmark found a 15-point accuracy spread, and
structure-aware chunking beats recursive baselines on MRR. Design:

- Split on **heading boundaries**; each chunk carries its **heading path**
  (`# Doc > ## Section > ### Sub`) as retrievable context — this also feeds BM25F's
  heading field.
- Target **256–512 tokens** per chunk (the QA sweet spot in current benchmarks);
  oversized sections split at paragraph boundaries with ~10–15 % overlap.
- **Code blocks and tables stay atomic** — never split mid-fence, mid-table.
- Chunk boundaries recorded as source line ranges → citations stay `file:line`.

This is also a design payoff: converting everything to Markdown at ingest is what
*makes* structure-aware chunking universally applicable, PDFs included.

### 3. BM25F field weights — **defaults set, config-overridable. Resolved.**
BM25F's correct form (per Robertson; Lucene's `CombinedFieldsQuery`): compute
**effective term frequency as the weighted sum across fields** (`tf_eff = w_title·tf_title
+ w_path·tf_path + w_body·tf_body`), *then* apply saturation once — not per-field
scoring glued together. Industry practice weights titles 2–5× body. Our defaults:

| Field | Weight | Why |
|-------|--------|-----|
| Heading path | **3.0** | Titles/headings are the strongest relevance signal (2–5× is standard practice) |
| File path/name | **2.0** | File names encode topic ("db-indexing.md") |
| Body | **1.0** | Baseline |

`k1 = 1.2`, `b = 0.75` (the standard Elastic/Lucene defaults; tune only with eval
evidence). All overridable in `fux.toml` under `[engine.bm25f]`; the Anton eval set
is the instrument for tuning, not taste.

## References

- Internal: [`../../CLAUDE.md`](../../CLAUDE.md) — `$0`/no-external-model constraints; [`packaged-model.compare.md`](packaged-model.compare.md) — the bundled embedding model powering v2.
- External: [Okapi BM25 — Wikipedia](https://en.wikipedia.org/wiki/Okapi_BM25) — BM25/BM25F, the v1 ranker (accessed 2026-07-20).
- External: [Hybrid Search: BM25, Vector & Reranking Reference 2026](https://www.digitalapplied.com/blog/hybrid-search-bm25-vector-reranking-reference-2026) — hybrid + RRF recall numbers behind v2 (accessed 2026-07-20).
- External: [Hybrid RAG: BM25 + RRF Guide 2026](https://aiworkflowlab.dev/article/how-to-build-hybrid-search-rag-bm25-rrf-fusion-cross-encoder-reranking) — RRF formula and pipeline (accessed 2026-07-20).
- External: [Sparse vs Dense Retrieval for RAG (BM25, embeddings, hybrid)](https://mljourney.com/sparse-vs-dense-retrieval-for-rag-bm25-embeddings-and-hybrid-search/) — where each wins; SPLADE context (accessed 2026-07-20).
- External: [Lewis et al., 2020 — RAG (arXiv:2005.11401)](https://arxiv.org/abs/2005.11401) — the external-RAG pattern we deliberately avoid (accessed 2026-07-20).
- External: [RAG chunking strategies — 2026 retrieval playbook](https://www.digitalapplied.com/blog/rag-chunking-strategies-2026-retrieval-quality-playbook) — structure-aware vs fixed-size; ~9-pt recall swing; 256–512-token sweet spot (accessed 2026-07-21).
- External: [Best chunking strategies for RAG (Firecrawl, 2026)](https://www.firecrawl.dev/blog/best-chunking-strategies-rag) — MarkdownHeaderTextSplitter as the biggest single improvement for structured content (accessed 2026-07-21).
- External: [BM25F in Lucene/Elasticsearch — combined_fields](https://opensourceconnections.com/blog/2021/06/30/better-term-centric-scoring-in-elasticsearch-with-bm25f-and-the-combined_fields-query/) — weighted-tf-then-saturate, the correct BM25F formulation our v1 implements (accessed 2026-07-21).
- External: [Sourcegraph — keeping it boring (and relevant) with BM25F](https://sourcegraph.com/blog/keeping-it-boring-and-relevant-with-bm25f) — BM25F field weighting in a real code/doc search engine (accessed 2026-07-21).
- External: [Practical BM25 — picking b and k1 (Elastic)](https://www.elastic.co/blog/practical-bm25-part-3-considerations-for-picking-b-and-k1-in-elasticsearch) — why k1=1.2, b=0.75 stay default until eval evidence says otherwise (accessed 2026-07-21).
- External: [Cross-encoder reranking in practice](https://tianpan.co/blog/2026-04-19-cross-encoder-reranking-cosine-similarity) — why reranking gains require cross-attention (≥MiniLM-size), grounding the no-reranker verdict (accessed 2026-07-21).

## Additional things to look into

- **Eval set:** ~10–20 real "question → expected passage" pairs from Anton to measure
  v1 before adding v2 — and the only instrument that can reopen the reranker or
  retune weights.
- **RRF k tuning** (k≈60 default) on the eval set.
- *(Chunking unit and BM25F field weights: resolved above, 2026-07-21.)*
