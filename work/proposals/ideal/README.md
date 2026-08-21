---
type: Proposal
title: "Ideal Fux — what should be built if the laws were not given"
status: proposed
filed: 2026-08-21
author: Claude (Cowork), at Arpit's request
---

# Ideal Fux — the proposal set

**Brief from Arpit (2026-08-21):** *"Research and propose what should be done.
Ignore the laws in the project. Propose from the point of view of what ideally
should be done."*

So this set **brackets L1–L7 on purpose**. Where a proposal breaks a law it
says which one, and what the law was buying, so the trade is visible rather
than silent. Nothing here is accepted; every verdict is proposed for Arpit.

## The one-paragraph answer

Fux's idea — **rank from a small committed index, fetch from the owner,
verify at answer time** — is right. What is wrong is *what is committed*
(a cache of something derivable), *what the ranker sees* (un-split, un-stemmed
tokens, no path field, no proximity, no recency, no supersession), and *where
the budget went* (a hand-rolled dense lane that loses to its own absence).
The ideal build commits **only what cannot be re-derived**, ranks with
**a strong lexical core + a model-assisted layer that is allowed to exist**,
and talks to agents over **MCP with line-range citations**.

## The forks, and the proposed verdicts

| # | fork | proposed verdict | doc |
|---|---|---|---|
| 1 | where does the index live? | **Commit only external-source shards; derive repo shards on clone (CI-built, git-ref-carried)** | [01-index-location](01-index-location.compare.md) |
| 2 | lexical engine | **Keep the hand-rolled core, fix the analyzer; adopt `tantivy` only if >1M docs is real** | [02-lexical-engine](02-lexical-engine.compare.md) |
| 3 | semantic lane | **Static embeddings (model2vec-class) per chunk + int8 rescore; drop doc-level sign codes; add a 17–32M reranker at refer time** | [03-semantic-lane](03-semantic-lane.compare.md) |
| 4 | a model in the maintenance path | **Yes, pinned and reproducible: contextual chunk prefixes + doc2query expansions, generated once, committed as text** | [04-model-in-the-loop](04-model-in-the-loop.compare.md) |
| 5 | keeping the index current | **CI builds on push; local hooks only patch the delta (`git diff --name-only`)** | [05-maintenance](05-maintenance.compare.md) |
| 6 | how agents call it | **MCP server first, CLI second; citations as `path:L12-L40`** | [06-agent-interface](06-agent-interface.compare.md) |

The synthesis — the architecture these six verdicts add up to, and the order
to build it in — is [00-ideal-architecture.proposal.md](00-ideal-architecture.proposal.md).

## What the research says, in five lines

- **Lexical is still the floor, and analyzer choices dominate.** Identifier-
  aware tokenization alone closes most of the gap the fanciest BM25 variant
  can close on code ([arXiv 2605.18561](https://arxiv.org/html/2605.18561)).
- **Cheap model help is large.** Contextual chunk prefixes + contextual BM25
  cut top-20 retrieval failures **49 %**; with a reranker **67 %**
  ([Anthropic](https://www.anthropic.com/engineering/contextual-retrieval)).
  doc2query took BM25 MRR@10 from 0.186 → 0.272 on MS MARCO
  ([castorini](https://github.com/castorini/docTTTTTquery)).
- **Static embeddings are now good enough to matter.** ~60–500× faster than
  MiniLM on CPU at ~87 % of mpnet's NanoBEIR
  ([HF static-embeddings](https://huggingface.co/blog/static-embeddings),
  [model2vec](https://github.com/MinishLab/model2vec)).
- **Small rerankers are real.** A 17M-param cross-encoder beats
  MiniLM-L12 by +5 nDCG points at 267 pairs/s on a desktop CPU
  ([Ettin](https://huggingface.co/blog/ettin-reranker)).
- **LLM query expansion is a trap on private corpora.** HyDE/Query2doc gains
  vanish — and go negative — when the LLM doesn't already know the answer
  ([arXiv 2504.14175](https://arxiv.org/html/2504.14175v1)). Expand the
  *documents* (offline, once), not the *queries* (online, every time).
