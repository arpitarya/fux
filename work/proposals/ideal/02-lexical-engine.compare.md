---
type: Compare Doc
title: "The lexical engine — keep, replace, or augment?"
status: proposed
filed: 2026-08-21
laws_bracketed: [L1]
---

# The lexical engine — keep, replace, or augment?

## What exists

- Hand-rolled BM25F (`heading`×3, `body`×1; k1 1.2, b 0.75), block-max
  skipping over JSONL block lines, 16-hex term hashes, 256 hash shards.
- Analyzer: `[a-z0-9_]+` lowercase + 50 stopwords. **No** stemming, **no**
  identifier splitting, **no** `path`/`title` fields, **no** phrases/proximity.
- Measured: p95 27 ms warm on 8.8k RFCs; hit@5 0.952 on the fixture, 0.887 on
  the lab corpus.

## The two separable decisions

1. **The analyzer** — where the quality is. Independent of engine choice.
2. **The engine** — where the speed/scale ceiling is.

## Decision 1 — the analyzer (no fork; do all of it)

| change | evidence | expected effect |
|---|---|---|
| split `camelCase` / `snake_case` / `kebab-case`, emit whole + parts | identifier-aware tokenization captures most of the gain available to BM25 on code; the best BM25 variant adds only +0.2 % on top of it ([arXiv 2605.18561](https://arxiv.org/html/2605.18561)) | largest single lift for a codebase tool |
| Porter/Snowball stemming (English) | standard IR; Lucene/Elastic default for `english` analyzer | recall on morphology (`deploy`/`deployment`) |
| `path` field (segments + split filename) and `title` field, separate weights | the archived engine had `path`; Zoekt ranks on filename & path ([Zoekt](https://github.com/sourcegraph/zoekt/blob/main/doc/design.md)) | "where is X" queries |
| bigram shingles for headings/titles only | cheap phrase signal without positional postings | precision on multi-word names |
| proximity / exact-phrase **at rescore time on fetched bytes** | the refer plane already has the bytes; positional scoring there is free | precision of the *cited passage* |
| recency prior from `git log -1 --format=%ct` per doc | Zoekt uses file recency as a signal | runbooks/ADRs: newer wins ties |
| supersession down-rank via extracted `supersedes` edges, through the already-ported `rrf(offsets=)` | archived ADR-0015 calibrated offset 15 | retired decisions stop outranking live ones |

**Keep the hashed term space** — it is what makes `hashed` meta (the ACL
leak fix) possible. Stem *before* hashing.

## Decision 2 — the engine

| | A · hand-rolled (today) | B · SQLite FTS5 | C · `tantivy` (Rust, Python bindings) | D · `bm25s` (numpy/scipy eager scoring) |
|---|---|---|---|---|
| runtime deps | none | stdlib `sqlite3` (FTS5 compiled in on macOS/Linux/Windows py.org builds) | one wheel | numpy + scipy |
| BM25F / field weights | yes (own code) | BM25 with column weights (`bm25(t, 3.0, 1.0)`) | yes, native | BM25 only, no fields |
| dynamic pruning | block-max (own) | none | block-WAND | n/a (eager precompute) |
| positional / phrase | no | yes (`NEAR`, phrase) | yes | no |
| custom analyzer | full control | tokenizer plugin via C API or pre-tokenize | custom tokenizers | pre-tokenize |
| 10⁵–10⁶ docs | unproven past 8.8k; Python-bound | proven to 10⁶+ | proven to 10⁸ (Quickwit) | fast but RAM-heavy |
| incremental update | full rewrite of shard | row-level | segment merge | full rebuild |
| diff/merge-friendly artifact | JSONL yes | binary | binary | binary |
| hashed-meta compatible | yes | yes (store hashes as tokens) | yes | yes |
| query speed | 27 ms @ 8.8k (measured) | ~ms @ 10⁵ | sub-ms–ms @ 10⁶ | ~100× faster than rank_bm25 ([BM25S](https://arxiv.org/html/2407.03618v1)) |
| what L1 bought | auditable supply chain | still effectively stdlib | one vetted Rust crate | numpy is everywhere anyway |

## Debate

- **Keep A** because the differential law (scan ≡ accelerator) is a genuinely
  good testing story and the code is correct. Its ceiling is Python: the doc
  table, JSON block lines and list-based candidate handling will be the wall
  at 10⁵–10⁶. Lucene got 3–7× on term queries from block-max WAND alone
  ([Elastic](https://www.elastic.co/blog/faster-retrieval-of-top-hits-in-elasticsearch-with-block-max-wand)) —
  A already has that; what it lacks is native decode.
- **B** is the pragmatic middle: zero new deps in practice, phrase queries
  for free, and the derived index (doc 01) can *be* an FTS5 file. It gives
  up block-max and custom BM25F saturation (FTS5's column weighting is
  per-column BM25 summed — exactly the "never sum per-field BM25" rule says
  not to do).
- **C** is what you'd pick with no laws: Lucene-class engine, BM25F, phrase,
  WAND, segment files that mmap. One wheel.
- **D** is fastest for batch eval but is a research tool; no fields, no
  incremental, no phrase.

## Proposed verdict

**Keep A as the engine; spend the effort on Decision 1.** Reopen for C the
day a real corpus above ~2×10⁵ documents is measured against the 150 ms
warm bar and fails. Do **not** take B: losing weight-then-saturate BM25F for
a convenience is a ranking regression dressed as a simplification.

Two engine-level improvements worth doing inside A regardless:

- **Impact-ordered blocks** (postings within a term sorted by weighted tf
  desc) — tighter `theta` earlier, more skipping, no format change to the
  committed shards.
- **Fixed-width doc table** for the runtime (offset + length per docidx, lazy
  `json.loads`) — removes the O(corpus) first-query cost that R5 attributed.

## Reopen trigger

A measured p95 above 150 ms warm on a corpus ≥ 2×10⁵ documents *after* the
two improvements above.
