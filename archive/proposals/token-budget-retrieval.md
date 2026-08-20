---
type: Proposal
title: Token-budget retrieval — the answer limit is a byte budget, not k
description: Agents do not want ten results, they want the most answer that fits. Replace top-k as the primary limit with a caller-supplied byte/token budget the assembler fills. Parallel makes context-window efficiency a ranking signal; k=10 is a human-browsing artifact.
status: implemented
timestamp: 2026-08-10T00:00:00Z
tags: [refer-plane, query-api, m2, m4]
---

> **Implemented 2026-08-20.** Successor:
> [ADR-REFER](../../docs/adr/0031_refer-plane.md) decisions 10-13 — *still
> `proposed`; its gate R4 has not run.* Byte budget primary, `k` demoted to
> a secondary cap, deterministic ties, a per-document cap, and a floor the
> proposal did not anticipate: greedy score-per-byte is systematically
> biased toward short passages, so the best answer is seated first.


# Token-budget retrieval

**The idea.** `k` is the wrong limit for an agent. **The binding constraint is
the context window, not the result count.**

Replace top-k as the *primary* control with a byte budget the assembler fills:

```
fux ask "…" --budget 8000        # bytes of assembled answer, not results
```

The engine returns the highest-value assembled answer that fits — which may be
one long passage from one document, or twelve short ones from nine.

## Why it is worth filing

**Parallel makes this the centre of their design**, and it is the sharpest idea
in the peer set:

- `max_chars_total` — "default is **dynamic based on** `search_queries`,
  `objective`, and **`client_model`**". They keep per-model context profiles
  server-side and size output to the caller's window.
- Stated ranking signals include **"context window efficiency"** and **"token
  relevancy"**, not click-through.
- **Everyone else ranks documents and then truncates. They rank *for* the
  truncation.**

Evidence and the four-way convergence on the passage as the retrieval unit:
[`agent-search-landscape.md`](agent-search-landscape.md) §2–§3.

**Fux is unusually well placed to do this honestly.** Because the refer plane
re-scores passages on the *fetched bytes*, it knows the real size of every
candidate at assembly time — not an estimate from index statistics. A
web-scale player has to guess; Fux does not.

## Sketch

- `--budget` (bytes) becomes the primary limit on `ask`/`answer`; `-k` survives
  as a secondary cap and as the default for humans, who genuinely do want a
  list.

- The assembler runs a **bounded selection over scored passages** under the
  budget: greedy by score-per-byte, with a floor so no single citation is
  truncated into incoherence and a cap so one document cannot consume the whole
  budget.

- **Deterministic tie-breaking is mandatory** — equal score-per-byte resolves by
  `(score, sha, locator)`, never by set iteration order. Same corpus + same
  budget → byte-identical assembly.

- Byte budget, **not** token budget, in the engine. Tokenizing to count is a
  model-specific dependency and the `$0`/stdlib law forbids carrying a
  tokenizer per model family. A caller who thinks in tokens converts at the
  boundary; document a conservative bytes-per-token rule of thumb and stop
  there.

## Why not now

- **The scoring path it sits on is M2** ([`../OPEN-WORK.md`](../OPEN-WORK.md)
  W-22) and the passage re-scoring it depends on is **M4** (W-24). T0's
  scan-based `ask` has neither.

- It changes the shape of the answer contract, so it should land **once**, with
  the refer plane, not as a later break.

- One question needs a deliberate call: **does the budget bound the citations
  or the whole rendered answer** (headers, locators, the ranking explanation)?
  Bounding the whole thing is the honest reading of "fits in my context" and
  the harder one to implement.

## Graduation trigger

**Fold into the M4 handoff alongside
[`caller-set-freshness-policy.md`](caller-set-freshness-policy.md)** — the two
are the same insight applied to different axes (*how fresh* and *how much*), and
both belong to the refer API's first shape.

Measurable version: extend **R4**'s bench with a budget sweep and report
**answer quality per byte returned**, not just latency. If quality-per-byte is
flat across budgets, the greedy assembler is not earning its complexity and
plain top-k with truncation wins.

## Risks to hold

- **Greedy score-per-byte is a knapsack heuristic, not an optimum.** Say so;
  do not oversell it. It is the right complexity for a stdlib target — the
  archived engine's own history says the simple thing usually holds.

- **A short high-scoring passage can crowd out the one long passage that
  actually answers the question.** The per-citation floor is what stops this,
  and it needs a real test, not an assertion.

- **Do not import Parallel's benchmark framing with the idea.** Their published
  comparisons measure search-cost *plus* LLM-token-cost combined, which is the
  metric a token-efficiency-optimized ranker wins by construction. The idea can
  be right and the evidence for it self-serving at the same time — see
  [`agent-search-landscape.md`](agent-search-landscape.md) §"Benchmark caution".

## References

[`agent-search-landscape.md`](agent-search-landscape.md) (the evidence base) ·
Parallel `max_chars_total` / `client_model` —
[Search best practices](https://docs.parallel.ai/search/best-practices) ·
[Search API reference](https://docs.parallel.ai/api-reference/search-beta/search) ·
"context window efficiency" as a ranking signal —
[Parallel Search products page](https://parallel.ai/products/search) ·
Perplexity's "self-contained spans" —
[architecting an AI-first search API](https://research.perplexity.ai/articles/architecting-and-evaluating-an-ai-first-search-api) ·
sentence-dependency chunking —
[Wilson Lin, a search engine from scratch](https://blog.wilsonl.in/search-engine/) ·
[the ADR register](../../docs/adr/README.md) §M2, §M4 ·
[`../paper/the-fux-index-paper.md`](../paper/the-fux-index-paper.md) §refer
