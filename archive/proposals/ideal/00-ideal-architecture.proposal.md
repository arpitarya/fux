---
type: Proposal
title: "Ideal Fux — the architecture the six verdicts add up to"
status: proposed
filed: 2026-08-21
laws_bracketed: [L1, L3]
---

# Ideal Fux — the architecture the six verdicts add up to

**Read the compare docs first** ([README](README.md)). This is the synthesis:
what the system looks like if every proposed verdict is accepted, and the
order to get there that keeps each step measurable.

## The shape

```
sources (git tree · URLs · Confluence)                content stays here
   │
   │  fux enrich   (optional, separate command, model allowed)
   │     └─> .fux/enrich/<sha>.md   pinned text, committed, keyed by content sha
   │
   │  fux ingest   (deterministic over sources ∪ enrichment)
   ▼
COMMITTED   .fux/external/*.jsonl      only what a clone cannot re-derive
DERIVED     .fux/derived/              repo shards · postings · int8 chunk vectors
            (gitignored; built by hooks/CI; optionally carried on refs/fux/<tree>)
   │
   │  query: lexical (BM25F, split+stem, path/title fields, block-max)
   │         ⊕ gated dense (static chunk embeddings, Hamming → int8 rescore)
   │         ⊕ priors (recency, supersession via edges)
   ▼
REFER       fetch top-k from owner → chunk → proximity rescore → rerank top-50
            → cite  path:L12-L40 @ sha  with freshness verdict
   │
   ▼
MCP server (warm) · CLI (humans)
```

## What changes, component by component

| component | today | ideal | doc |
|---|---|---|---|
| committed index | all shards, JSONL, 256 hash buckets | **external shards only**; repo shards derived | 01 |
| merge driver, runtime stamp/manifest | correctness machinery | **deleted / demoted to cache notes** | 01 |
| analyzer | `[a-z0-9_]+` + stopwords | **identifier split + stem + path/title fields + heading bigrams** | 02 |
| ranker | BM25F(heading, body) | BM25F(title, path, heading, body, ctx) + **recency prior + supersession offset** | 02, 04 |
| accelerator | block-max over JSON block lines | + **impact-ordered blocks**, fixed-width doc table | 02 |
| dense | doc-level 256-bit sign code, default off | **per-chunk static embeddings**, int8 rescore, **gated** fusion | 03 |
| enrichment | ratified shape, unbuilt | **`fux enrich`**: contextual prefixes (+ predicted questions), pinned as text | 04 |
| refer rescore | BM25F over passages | **proximity/phrase + 17–32M cross-encoder** on top-50 | 02, 04 |
| hooks | full ingest per event (44 s @ 100k) | **`git diff` delta + reverse-edge index** (< 1 s) | 05 |
| interface | CLI `--json`, `loc#p3` | **MCP + CLI**, `path:L12-L40`, warm process, answer cache | 06 |

## What the laws become

| law | today | ideal |
|---|---|---|
| L1 stdlib-only | absolute | **stdlib reference path always works**; `numpy` (dense) and `onnxruntime` (reranker) are optional accelerators, each behind a differential/fallback test |
| L2 no durable content | absolute | unchanged |
| L3 byte-deterministic, no model | absolute | **result-deterministic** index over (sources ∪ pinned enrichment); models run only in `enrich` (offline, separate) and `rerank` (read-only, per answer) |
| L4 offline default | absolute | unchanged; `enrich --model api` is a fenced path like `--refresh-urls` |
| L5 hashed meta | absolute | unchanged; applies to enrichment text too |
| L6 "index" | — | unchanged |
| L7 py ≥ 3.11 | — | unchanged |

**The product promise survives in a stronger form:** *"Fux never stores your
content, never needs a server, works offline, and every citation is a
verbatim span with a fresh hash."* None of that required byte-identical
shards or a model-free ingest; those were means.

## Build order — each step measurable on the existing 50 goldens

| step | change | gate | why this order |
|---|---|---|---|
| 1 | analyzer: split + stem + path/title fields | hit@5 / MRR on goldens, ≥ today | biggest expected lift, zero new deps, zero format risk (derived index only) |
| 2 | supersession offset + recency prior | same + "retired ADR outranks live" class → 0 | ⚠ ~~code is ported already (`rrf(offsets=)`)~~ — **false since 2026-08-26**, `query/fuse.py` is deleted (W-79). The live path is `[ranking] superseded_weight` at `query/rank.py:205`, which exists but is inert on the fixture (W-78) |
| 3 | delta hooks (`git diff` + reverse edges) | **re-run R5**; expect PASS at 100k | turns the one FAIL into a PASS without touching ranking |
| 4 | split committed/derived; stop committing repo shards | R6 becomes moot; clone→first-query time measured | removes the merge driver and two ADRs |
| 5 | MCP server + line-range citations | an agent completes the playground tasks with fewer tool calls than grep (measure calls + tokens) | the consumer-facing change; everything above makes it good |
| 6 | reranker at refer time (optional dep) | failure rate on goldens, top-20 → top-5 | largest quality step per line of code |
| 7 | per-chunk static embeddings, gated fusion | the 3-fixed/9-broken result must become ≥ 3-fixed/0-broken | replaces the one component that currently earns nothing |
| 8 | `fux enrich` (contextual prefixes) | failure-rate delta, measured with and without | last because it adds a workflow (a command people must run) |
| 9 | `refs/fux/<tree>` publish/fetch | clone→first-query at 100k docs ≈ fetch time | only matters once a team is on it |

Steps 1–5 need **no new dependency and no law change beyond L3's relaxation
to result-determinism**. Steps 6–8 are where the laws are actually bracketed,
and each is optional at runtime with a stdlib fallback.

## Out-of-the-box ideas worth a spike (not in the plan)

- **Query-term expansion from the static table** — nearest vocabulary
  neighbours of each query token, at low weight, fully lexical and
  deterministic. Might close class-3 goldens for free. Spike before step 7.
- **Learned sparse as the second lane** instead of dense: a SPLADE-class
  vector *is* a posting list, so it reuses the whole block-max machinery and
  the hashed term space. Spike after step 8 when a model at ingest exists.
- **Local overlay index** for uncommitted edits (Cursor's pattern): the
  derived index is the anchor at `HEAD`, a tiny in-memory delta covers the
  working tree. Answers "what did I just write?" — the question agents ask
  most and no committed index can answer.
- **Usage signal as a committed, deterministic prior**: when an agent opens a
  cited file, append `(query-hash, doc-id)` to a committed `.fux/votes`
  file; ingest folds it into a click prior. Deterministic, auditable, and the
  only feedback loop a zero-infra tool can have.

## What I would *not* do

- Replace the lexical engine (tantivy/FTS5) before a corpus > 2×10⁵ fails the
  150 ms bar. The engine is correct; the analyzer is the problem.
- LLM query expansion (HyDE-class) — measured negative on unfamiliar corpora.
- A bigger embedding model before a reranker — the reranker reads the actual
  passage; the embedding model guesses from 1024 tokens.
- Keep committing repo shards "for audit." `git show refs/fux/<tree>` is the
  audit.
