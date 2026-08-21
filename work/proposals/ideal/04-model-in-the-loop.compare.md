---
type: Compare Doc
title: "A model in the maintenance path — where, and under what contract"
status: proposed
filed: 2026-08-21
laws_bracketed: [L3, L4, L1]
---

# A model in the maintenance path — where, and under what contract

## The question

L3 says *no model may ever run in the maintenance path*. The project already
carved a side door (`enriched` mode, pinned output, its own command). With the
law bracketed: **where does a model buy the most retrieval quality per dollar
and per risk, and what contract keeps the result trustworthy?**

## The evidence

| technique | where it runs | measured gain | cost | source |
|---|---|---|---|---|
| **Contextual chunk prefix** (50–100 tokens of "this chunk is from X, about Y" prepended before indexing) | ingest, once per chunk | top-20 failure rate 5.7 % → 2.9 % (**−49 %**) with contextual BM25 + embeddings | $1.02 / M doc tokens with prompt caching | [Anthropic](https://www.anthropic.com/engineering/contextual-retrieval) |
| **+ cross-encoder rerank of top-150 → 20** | query, per answer | → 1.9 % (**−67 %**) | 17–32M-param model: 90–270 pairs/s on CPU | same; [Ettin](https://huggingface.co/blog/ettin-reranker) |
| **doc2query / docTTTTTquery** (predict likely questions, append to doc) | ingest, once per doc | BM25 MRR@10 0.186 → 0.272 (**+46 %**), +9 ms query | T5-base forward per doc | [castorini](https://github.com/castorini/docTTTTTquery) |
| **Learned sparse expansion (SPLADE/ELSER)** | ingest | ELSER: +17 % nDCG@10 over BM25 avg, 10/12 BEIR wins | transformer forward per chunk | [Elastic](https://www.elastic.co/search-labs/blog/elastic-learned-sparse-encoder-elser-retrieval-performance) |
| **HyDE / Query2doc** (LLM expands the *query*) | query, every time | positive **only** when the LLM already knows the answer; negative by 15+ pts on unfamiliar corpora | an LLM call per query | [arXiv 2504.14175](https://arxiv.org/html/2504.14175v1) |

The pattern is unambiguous: **expand documents offline, rerank online, never
expand queries with an LLM on a private corpus.**

## Options

| | A · no model anywhere (L3 today) | B · model at ingest, output pinned as text (contextual prefixes + doc2query) | C · model at query time only (reranker) | D · B + C |
|---|---|---|---|---|
| reproducibility | byte-identical | **reproducible from the pinned text**; the *generation* is not, the *index* is | deterministic given the model file + int8 ONNX on one machine; not bit-identical across machines | as B + C |
| offline | yes | generation needs a model (local or API); **indexing does not** | local model file, offline | as B + C |
| cost per 1M doc tokens | 0 | ~$1 (API, cached) or local small model | 0 at ingest | ~$1 |
| per-query latency | 0 | 0 (it's just more terms) | +75–200 ms for 20 pairs on CPU | +75–200 ms |
| quality gain (indicative) | — | −49 % failures / +46 % MRR class | −35 % failures class | **−67 %** class |
| ACL / L5 | n/a | pinned text is *derived content* — must obey hashed meta or live only in derived shards | model sees fetched bytes the caller is already allowed to read | as B |
| audit story | trivially | "which model, which prompt, which date" recorded per pinned record | model hash recorded per answer | both |

## Debate

- **Against any model (A):** L3's real purchase was *trust*: an index nobody
  can argue with. *Counter:* the index already contains an opaque model
  artifact — the 7.6 MB embedding table. The line was crossed; what is left
  to protect is **provenance**, not purity.
- **B's contract** makes it safe: (1) generation is a separate command
  (`fux enrich`), never inside `ingest`; (2) output is committed as plain
  text in `.fux/enrich/<sha>.md`, keyed by the source content sha so a
  changed doc invalidates its enrichment; (3) `ingest` consumes it as if it
  were an extra field (`ctx`, weight ~1) — deterministic from that point on;
  (4) every pinned record carries `model`, `prompt_sha`, `generated_at`. This
  is exactly the `enriched` mode the repo already ratified the *shape* of.
- **C** is the highest-leverage single addition because it runs on the
  **fetched bytes the refer plane already has**, on only 20 candidates, and
  a 17M model fits in ~35 MB int8. It replaces the passage BM25 rescore with
  something that actually reads the passage.
- **D** is what Anthropic measured: the two compound.

## Proposed verdict

**D, in this order: C first (no index change, immediate), then B.**

- **C:** add `fux.rerank = off | ettin-17m | <path>`; default **on** when the
  model file is present. Rerank the top-50 passages after the refer fetch;
  fall back to BM25F passage rescore when absent. Record `reranker_sha` in
  the bundle.
- **B:** `fux enrich [--model local|api]` writes contextual prefixes (and
  optionally 3–5 predicted questions) per chunk into `.fux/enrich/`. For
  `hashed` sources the enrichment is hashed like any other term. `ingest`
  reads it; `ingest` never generates it.
- **Never:** HyDE-style query expansion against the corpus. If a query-side
  model is wanted, it is the *agent* (who already has one) rewriting its own
  question — outside Fux.

## What this costs against the laws

- **L3** becomes: *the index is a deterministic function of (sources ∪
  pinned enrichment)*. Same property, larger input.
- **L4** unchanged: `fux enrich --model api` is as fenced as `--refresh-urls`.
- **L1** is broken by `onnxruntime` for C. If that is unacceptable, Ettin's
  architecture (ModernBERT) is not hand-rollable; the fallback is to stay
  with BM25F passage rescore + proximity (doc 02) and take B alone.

## Reopen trigger

Reopen if the graded set, after D, shows the reranker *demoting* gold
passages in > 5 % of queries (a domain-mismatch signal) — then the fix is a
fine-tuned reranker on the playground goldens, not removal.
