---
type: Proposal
title: Agent search-API landscape — where the funded peer set converged with index-and-refer
description: Research note on Parallel, Perplexity, Exa, Brave, Tavily, Linkup and the web-index cost literature. Three of their load-bearing decisions match the index-and-refer paper independently; one gap names Fux's wedge. Evidence base for the two proposals it spawned.
status: proposed
timestamp: 2026-08-10T00:00:00Z
tags: [landscape, refer-plane, evidence, positioning]
---

# Agent search-API landscape — the convergence with index-and-refer

> **Not a fork and not a build item.** A preserved research note, filed the
> same way [`wavelet-self-index.md`](wavelet-self-index.md) preserves a
> rejected option: the evidence base two proposals cite, and the record of
> *why* they were filed.
>
> **Spawned:** [`caller-set-freshness-policy.md`](caller-set-freshness-policy.md) ·
> [`token-budget-retrieval.md`](token-budget-retrieval.md)

## Signal

**Arpit asked how [platform.parallel.ai](https://platform.parallel.ai) works
under the hood, because Fux is "building something along the same lines."**

The answer that matters is not that Parallel is a competitor — it is not, and
§"The wedge" explains why. It is that **a $2B-valuation company with 100k+
developers independently arrived at three of the decisions the index-and-refer
paper already makes**, and published enough detail to check.

Convergent arrival is the strongest evidence a design gets short of a
measurement.

## Who Parallel actually is

- Parag Agrawal's (ex-Twitter CEO) web-research API for AI agents. **$230M
  raised, $2B valuation** (Apr 2026, Sequoia-led), 100k+ developers.

- **Own crawler, own index, no federation.** The crawler is `ShapBot`, with a
  separate `Shap-User` agent for on-behalf-of-a-user fetches. "Every layer —
  crawl, index, query processing, and ranking — is engineered for how machines
  consume information, not how humans browse."

- Index claimed at "billions of pages", "millions added daily". A separate post
  claims **1B+ pages added-or-refreshed daily** — that is 10× Brave's published
  100M/day and roughly a third of Common Crawl's *entire monthly* output, every
  day. **Treat it as unverified**; it is most likely counting cheap
  re-validations.

- Market context: **Microsoft retired the Bing Search API in August 2025.**
  That is the event that created this market — it removed the cheap federation
  substrate, so "we own an index" went from a fakeable claim to a real one.

## The three convergences

### 1 · The index is a cache with a caller-set TTL, not the source of truth

Parallel's Search API takes a per-request `fetch_policy`:

```
fetch_policy: { max_age_seconds: 86400, timeout_seconds: 60 }
```

Below the age bound, serve from index. Above it, fetch live — bounded by a
latency guard so a crawl cannot blow the SLA.

**That is the refer plane**
([paper](../paper/the-fux-index-paper.md) §refer): rank in the index, fetch
from the system that owns the content, verify at answer time. Arrived at
independently, from the opposite end of the scale axis.

The one thing they add that Fux does not yet have is that the *caller* sets the
staleness tolerance. That became
[`caller-set-freshness-policy.md`](caller-set-freshness-policy.md).

### 2 · The unit of retrieval is a token budget, not a result count

- `max_chars_total` — "default is **dynamic based on** `search_queries`,
  `objective`, and **`client_model`**". The engine keeps per-model context
  profiles server-side and sizes its own output to the caller's window.

- Stated ranking signals: **"token relevancy"**, **"context window
  efficiency"**, "the most information-dense pages for the agent's next
  action."

- Everyone else ranks documents and then truncates. Parallel claims to rank
  *for* the truncation. It is the sharpest idea in the peer set, and it became
  [`token-budget-retrieval.md`](token-budget-retrieval.md).

### 3 · The retrieval unit is the passage, not the document — four independent arrivals

| who | their words |
|---|---|
| Parallel | "information-dense excerpts compressed and prioritized for reasoning quality" |
| Perplexity | documents decomposed into **"self-contained spans"** retrieved and ranked individually, "explicitly to fit LLM context windows" |
| Exa | per-passage Contents API, priced separately from ranking |
| Wilson Lin (solo build) | a **DistilBERT classifier trained to identify which prior sentences a statement depends on**, so chunks stay self-contained |

Four independent arrivals at the same unit is the single strongest external
support the refer plane's "re-score passages on the fetched bytes" gets.

## What the peer set is, structurally

The useful axis is **who actually owns an index** — marketing deliberately
blurs it.

| tier | who | evidence |
|---|---|---|
| own crawl + own index | Exa, Perplexity, Brave, **Parallel** | detailed public engineering writing on internals |
| own crawl + aggregation | Tavily | never states a source; rivals call it a hybrid aggregator |
| fetch-on-demand, no index | Firecrawl, Jina Reader | Jina states it outright: "does not index or rank the web on your behalf" |
| SERP resale / scraping | Serper, SerpAPI | scraping a Big Tech index |
| opaque | Linkup | no disclosure |

Two of these publish enough engineering detail to be worth reading properly:

- **Perplexity** — [architecting an AI-first search API](https://research.perplexity.ai/articles/architecting-and-evaluating-an-ai-first-search-api)
  is the densest public document in the set. **200B+ unique URLs** tracked,
  "tens of thousands of indexing operations per second", ML models that predict
  *whether and when* a URL needs re-indexing, hybrid lexical+semantic retrieval
  → heuristic prefilters → **cross-encoder rerankers**, scored at document *and*
  sub-document level. Crawler rate limits enforced **distributed across the
  fleet** — the actually-hard part of politeness.

- **Exa** — publishes real numbers: Matryoshka embeddings **4096→256 dims**
  ("20× memory"), binary quantization ("another 16×"), 100k clusters, asymmetric
  dot product with lookup tables in CPU registers. **And a Rust BM25 inverted
  index** — "1.8 TB per 1B documents", doc IDs **4 bytes → 1.3 bytes** via delta
  + varint, zstd on postings, ~50 % memory cut for a 10 % *latency
  improvement*. Their founder said "we never even thought about using keywords
  really ever… we were neural all the way" — **the BM25 post postdates that
  interview.** They added lexical because pure-neural under-performed.

  *(That reversal is worth holding onto: it is external support for the
  full-postings lexical core accepted in [ADR-RECORD](../../archive/adr/0004_index-format.md),
  from a company with a $5M GPU cluster and every incentive to go dense.)*

- **Brave** has the one genuinely structural moat: the **Web Discovery
  Project**, anonymized visit data contributed by the Brave browser. It is a
  crawl-frontier signal gathered through *browsers, not crawlers* — which also
  routes around bot walls entirely.

## The cost literature — the part that actually transfers

[Wilson Lin's solo build](https://blog.wilsonl.in/search-engine/) (280M pages,
3B embeddings, two months, no prior search experience) publishes the cost table
nobody else will.

**The finding is not "search is cheap."** It is that the **hyperscaler markup
on exactly the primitives a search index needs is 20–30×**:

| component | rented bare metal | hyperscaler |
|---|---|---|
| vector DB, 1B inserts | $150 | $3,578 |
| high-memory server | $164 | $7,011 (AWS r7a) |
| NVMe storage | $6.63 | $243 (AWS i4g) |
| KV store | $125 (RocksDB) | $5,000 (DynamoDB) |
| blob storage | $250 | $7,300 (S3) |
| queue | ~$0 (self-hosted) | $1,200 (SQS) |

Supporting evidence in the same direction: **turbopuffer** measures in-memory
vector DBs at "$2+ per GB" vs object storage at "$0.02 per GB" — per TB per
month, **RAM+3×SSD $3,600 vs S3+SSD-cache $70**. **Quickwit/Tantivy** searches
straight off S3 with "only 3 random seeks", index open in ~70 ms.

**Why this belongs in a Fux doc:** it is independent confirmation that the
`$0`/stdlib law is not an ascetic constraint but the economically correct
architecture. The commercial players are paying 20–30× to rent what a committed
index gets for free, and the ones who publish numbers are all moving *toward*
object-storage-and-mmap, which is where the wire/runtime split already sits.

## The wedge

> Parallel's own FAQ: they access "only publicly available web content
> **without login credentials**."

**The entire funded peer set is locked out of the corpus Fux is designed for.**
Confluence estates, SharePoint, thousands of internal repos, access-boundaried
multi-team knowledge — the litmus in [`../../CLAUDE.md`](../../CLAUDE.md) — are
behind exactly the login wall their crawlers refuse to cross.

Only Linkup gestures at this ("run the full indexing layer inside your own
infrastructure… zero data leaving your environment") and discloses nothing about
how.

**And the risk that dominates their roadmaps is a non-event for Fux.**
[Cloudflare Pay Per Crawl](https://blog.cloudflare.com/introducing-pay-per-crawl/)
default-blocks AI crawlers and returns **HTTP 402** with a `crawler-price`
header. It converts crawling from a fixed infrastructure cost into a
**third-party-priced variable cost**, asymmetrically — Googlebot grandfathered,
new AI crawlers not. Every owned-web-index player is exposed; none has publicly
addressed it. An inside-the-firewall index has no exposure at all.

## What does *not* transfer

Stated plainly so a future session does not mistake this note for a build plan:

- **Do not compete on public-web index scale.** Exa runs 224 GPUs
  ($5M cluster); Parallel raised $230M. That axis is closed and it is not the
  design point.
- **Do not import their pricing psychology.** Parallel Turbo at **$1/1k
  requests** is the market floor and there is no public evidence anyone is
  profitable there.
- **Do not adopt "calibrated confidence" language.** Parallel asserts
  calibration on a three-value enum (`high`/`medium`/`low`) with **no published
  calibration curves, no ECE, no citation-faithfulness eval**. A 3-level ordinal
  is not a probability. If Fux ever emits confidence, it emits a measured one or
  none.

## Benchmark caution — this market vindicates the pre-registration law

**Every published comparison here is vendor-run on a vendor harness, and they
contradict each other:**

- Perplexity scores Exa at **.781** SimpleQA. Linkup scores Exa at **90.04 %**
  on the same benchmark.
- Parallel scores Exa at **58.67 %** on its own WISER set; Exa's own evals
  report Exa best on all three of its internal sets.
- Parallel benchmarked Brave on BrowseComp **without giving Brave a `web_fetch`
  tool**, and acknowledges this "accounts for some of the gap."
- Parallel's own WISER-Fresh half is **"generated by Parallel with o3 pro"** and
  tested within 24 h of generation.
- Exa's "open evals" have **no fixed corpus** and are LLM-graded — unfalsifiable
  by construction.

Only Perplexity open-sourced its harness (`search_evals`).

**The reading for Fux:** the divergence is not noise, it is methodology — query
mix, grader, and whether a fetch tool was allowed alongside search. This is what
a world without
[pre-registration](../../tools/pruning-eval/PRE-REGISTRATION.md) looks like, at
scale, with money on it. Believe only a harness you control, registered before
the number exists.

## References

**Parallel** — [Introducing Parallel](https://parallel.ai/blog/introducing-parallel) ·
[Search products page](https://parallel.ai/products/search) ·
[Search best practices](https://docs.parallel.ai/search/best-practices) ·
[Search API reference](https://docs.parallel.ai/api-reference/search-beta/search) ·
[research basis / FieldBasis](https://docs.parallel.ai/task-api/guides/access-research-basis.md) ·
[crawler / ShapBot](https://docs.parallel.ai/resources/crawler) ·
[Index by Parallel — Shapley-value publisher payouts](https://parallel.ai/blog/introducing-index-by-parallel) ·
[Search Turbo benchmark](https://parallel.ai/blog/parallel-search-turbo) ·
[search API benchmark / WISER](https://parallel.ai/blog/search-api-benchmark) ·
[deep research pipeline](https://parallel.ai/blog/deep-research) ·
[pricing](https://docs.parallel.ai/getting-started/pricing) ·
[FAQs](https://docs.parallel.ai/resources/faqs) ·
[Agrawal on the First Round podcast](https://review.firstround.com/podcast/twitters-former-ceo-on-rebuilding-the-web-for-ai-parag-agrawal-co-founder-and-ceo-of-parallel/) ·
[Fortune — paying publishers](https://fortune.com/2026/05/19/parag-agrawal-parallel-startup-pay-publishers-when-ai-agents-use-their-work/) ·
[TechCrunch — $2B](https://techcrunch.com/2026/04/29/parallel-web-systems-hits-2b-valuation-five-months-after-its-last-big-raise/)

**Peers** — [Perplexity — architecting an AI-first search API](https://research.perplexity.ai/articles/architecting-and-evaluating-an-ai-first-search-api) ·
[Exa — web-scale vector DB](https://exa.ai/blog/building-web-scale-vector-db) ·
[Exa — BM25 optimization](https://exa.ai/blog/bm25-optimization) ·
[Exa — Exacluster](https://exa.ai/blog/meet-the-exacluster) ·
[Latent Space — Will Bryk interview](https://www.latent.space/p/exa) ·
[Brave — what sets the API apart](https://brave.com/search/api/guides/what-sets-brave-search-api-apart/) ·
[Jina Reader](https://jina.ai/reader/) ·
[Linkup — SimpleQA claim](https://www.linkup.so/blog/linkup-establishes-sota-performance-on-simpleqa)

**Cost & substrate** — [Wilson Lin — a search engine from scratch](https://blog.wilsonl.in/search-engine/) ·
[turbopuffer — fast search on object storage](https://turbopuffer.com/blog/turbopuffer) ·
[Quickwit first release](https://quickwit.io/blog/quickwit-first-release) ·
[Common Crawl](https://commoncrawl.org/blog/january-2025-crawl-archive-now-available) ·
[Cloudflare Pay Per Crawl](https://blog.cloudflare.com/introducing-pay-per-crawl/)

**Internal** — [`../paper/the-fux-index-paper.md`](../paper/the-fux-index-paper.md) ·
[`../compare/cache-policy.compare.md`](../compare/cache-policy.compare.md) ·
[`../adr/0004_index-format.md`](../../archive/adr/0004_index-format.md) ·
[the ADR register](../../docs/adr/README.md) §M4
