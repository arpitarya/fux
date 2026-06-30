# Fux Recall Engine — Comparison

> **Verdict:** **Hybrid, shipped in stages.** Phase 1 is lexical (BM25-lite over
> frontmatter-weighted fields + body) — the candidate-generation half of hybrid,
> `$0` and dependency-free. Phase 2 adds a **local** embedding re-rank over those
> candidates for paraphrase recall, gated so the default path stays `$0` (no API).
> **Status:** ✅ Accepted · **Confidence:** High · **Decided:** 2026-06-01 · **By:** arpit
> **Revisit when:** phase-2 trigger hit — rule count >~200 or recall misses paraphrased queries. Keep the re-rank model **local** to preserve `$0`.

## Context

`fux recall "<query>"` (and the optional `UserPromptSubmit` hook) retrieves the
rules relevant to a query and injects only those — keeping context cheap instead
of loading the whole rulebook (see [fux-plan.md §8–§10](fux-plan.md)). The
question: **which retrieval engine** backs it. The hard constraint is Fux's
founding principle — *`$0` deterministic maintenance, no mandatory LLM calls*
([fux-plan.md §3](fux-plan.md)). The corpus is small (tens to low-hundreds of
rules) and richly tagged (`id`, `domain`, `type`, `related`, `code_refs`).

## Options

- **A — Keyword / lexical.** BM25-lite over the body plus weighted frontmatter (`id`/`domain`/`related` boosted). *(phase 1 of the verdict)*
- **B — Embeddings / semantic.** Embed each rule, store vectors, cosine-rank queries. Local model or API.
- **C — Hybrid.** Lexical candidate set, then local embedding re-rank. *(verdict — full design)*
- **D — LLM-pick.** Hand the index to Claude and let it choose relevant rules.

## Comparison matrix

| Criterion (weight) | A: Keyword | B: Embeddings | C: Hybrid | D: LLM-pick |
|--------------------|------------|---------------|-----------|-------------|
| Cost (H) | $0 | API $ or local model | $0–$ (mode-dependent) | Per-call $ |
| Determinism (H) | Full | Model-version dependent | Mostly | None |
| Dependencies (M) | None | Vector store + model | Both | SDK + tokens |
| Recall on paraphrase (M) | Good w/ tags | Best | Best | Best |
| Index maintenance (M) | Trivial (text) | Re-embed on change | Re-embed | None |
| Latency (M) | Instant | Fast | Fast | Slow (network) |
| Fit for small corpus (M) | Excellent | Overkill | Good | Overkill |
| **Score** | Phase 1 (ships first) | Heavy | **Verdict — full design** | Violates `$0` |

## Analysis

### A — Keyword / lexical *(phase 1)*
- **Pros:** `$0`, deterministic, zero dependencies, instant, trivial to keep
  fresh (it's just text). Frontmatter weighting (`domain`, `type`, `related`,
  `id`) gives strong precision on a curated corpus. Same spirit as the
  no-API, deterministic model.
- **Cons:** misses pure paraphrase with no shared keywords (e.g. "how much did I
  make today" vs a rule titled "day-pnl") — mitigated by good `related`/synonym
  tags and the small corpus size.

### B — Embeddings / semantic
- **Pros:** best raw recall on paraphrase and fuzzy intent.
- **Cons:** adds a model + vector store, an index to re-embed on every edit, and
  either API spend (breaks the `$0` mandate) or a bundled local model. Overkill
  for a few hundred well-tagged files.

### C — Hybrid *(verdict)*
- **Pros:** lexical narrows to candidates, embeddings re-rank for semantic
  closeness — best quality. Gated behind an opt-in flag so default stays `$0`.
- **Cons:** two systems to maintain; only worth it once corpus size or recall
  complaints justify it.

### D — LLM-pick
- **Pros:** best understanding of intent.
- **Cons:** a per-call LLM cost on every recall directly violates Fux's `$0`
  principle; non-deterministic; slow. Non-starter for the default path.

## References

- Internal: [fux-plan.md §3](fux-plan.md) — the `$0` / no-mandatory-LLM principle the verdict rests on.
- Internal: [fux-plan.md §10, item 11](fux-plan.md) — "cheap by default, smart if asked" (embeddings opt-in).
- External: [Okapi BM25 — Wikipedia](https://en.wikipedia.org/wiki/Okapi_BM25) — lexical ranking the v1 engine approximates (accessed 2026-06-01).
- External: [SQLite FTS5](https://www.sqlite.org/fts5.html) — a zero-dependency full-text option if BM25-lite needs upgrading (accessed 2026-06-01).
- External: [Sentence-Transformers](https://www.sbert.net/) — candidate **local** (no-API) embedding model for the opt-in hybrid path (accessed 2026-06-01).

## Additional things to look into

- **Synonym/alias field:** add an optional `aliases:`/`keywords:` frontmatter
  field so lexical recall catches common paraphrases without embeddings.
- **Recall test set:** keep a small labeled set of "query → expected rule" pairs
  to measure recall before deciding A is insufficient.
- **Local-first embeddings:** if/when upgrading to C, prefer a bundled local
  model over an API to preserve the `$0` guarantee.
- Not tested: actual recall numbers — the verdict rests on corpus size and the
  `$0` mandate, not a benchmark. Add measurements before reversing.
