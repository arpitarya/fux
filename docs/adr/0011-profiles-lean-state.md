---
type: ADR
title: ADR-0011 — full/lean profiles, the committed state budget, and the 100k scale benchmark
description: Lean stores ~230 B/doc and re-derives the rest, with rankings provably identical to full; measured against the proposal's estimates on a synthetic 100k corpus.
timestamp: 2026-07-22T00:00:00Z
---

# ADR-0011: Profiles, the state budget, and what 100k documents actually cost

- **Status:** accepted
- **Date:** 2026-07-22
- **Feature:** Storage profiles + the scale benchmark (handoff 0004, M7–M8)

## Context

Arpit's challenge: *can 100k documents cost ~20 MB of committed state instead of
1.4 GB?* No compressor turns 600 MB of text into 20 MB — entropy forbids it. But
Fux's own determinism law means the text does not have to be stored at all:

> **Sources are the storage.** Fux stores only how to find, verify and
> re-derive. Converters are deterministic, and `fux.lock` records each source's
> sha, so re-conversion provably reproduces the bytes the index was built from.

## Decision

Three profiles under `[index] profile`:

| profile | persists | a query |
|---------|----------|---------|
| `full` | chunks, postings, vectors | reads them |
| `lean` | doc-level state + df sidecar | re-derives candidates on demand |
| `auto` | — | resolves to one of the above |

**Lean is implemented as a normal `Searcher` over re-derived candidates with the
df sidecar injected.** That is what makes parity structural rather than
aspirational: `tf` is exact (deterministic re-derivation), `df`/`n`/`avg_wlen`
are exact (committed sidecar), and vectors are re-embedded rather than loaded —
the same model over the same text yields the same int8 vector. The kernel above
never learns which profile it is on.

A **bounded LRU** inside `fux.db` (`lean_cache_mb`, default 200) keeps the
working set warm. Eviction is least-recently-touched, where "recently" is a
**monotonic counter, not a wall clock** — determinism forbids clock values in
stored state, and the cache must never be able to change a result, only how fast
it arrives.

### `auto` needs a size threshold, not just re-derivability

§G defines `auto` as "lean when every source in a tier is re-derivable". Taken
literally that makes lean the default for every local repository — trading query
latency for a footprint win that does not exist below a few thousand documents,
and silently changing behaviour for every existing small corpus. `auto`
therefore also requires `[index] lean_threshold` documents (default 10 000).
`profile = "lean"` remains available explicitly at any size.

### A fresh clone answers exactly, not at doc level

DoD 2 asked for doc-level answers from committed state. The df sidecar makes
better possible: a clone with its sources present returns the **same rankings
and scores** as a full index, and `fux answer` works with real citations.
Doc-level ranking from codes and signatures became the honest *fallback* for
when sources cannot be re-derived — a crawled corpus, or a clone taken without
its documents. Exceeding a DoD is still a change to committed behaviour, so it
is recorded here and reflected in `example/CLI.md`.

## Measured — synthetic 100k corpus (M8)

Generator committed at [`tools/synth_corpus.py`](../../tools/synth_corpus.py),
benchmark at [`tools/bench.py`](../../tools/bench.py); both deterministic, so
these numbers are re-measurable. Corpus: **100 000 docs · 145.7 MB source ·
116 756 chunks**, with real link structure (see ADR 0009 on why that mattered).

### Sizes — every budget met

| artifact | proposal §8b estimate | measured | verdict |
|----------|----------------------|----------|---------|
| `fux.db` | ~1 400 MB | **1 081 MB** (10.8 KB/doc) | 77 % of estimate |
| `fux.lock` | ~30 MB | **21.5 MB** | 70 % |
| `.fux/state/` total | ≤30 MB (Arpit) | **22.96 MB** (230 B/doc) | ✅ **under** |
| └ `state/df/` | ≤5 MB (Arpit) | **0.92 MB** (9 B/doc) | ✅ **under** |
| └ `state/codes/` | — | 4.00 MB (40 B/doc) | |
| └ `state/sigs/` | — | 6.78 MB (68 B/doc) | |
| └ `state/meta/` | — | 11.25 MB (112 B/doc) | |

**The earlier size warning was a false alarm, and saying so is the point.** At
M3a an extrapolation from *this repository's own docs* projected ~35 MB, over
budget. That corpus is adversarial for the state plane — very long doc ids, long
titles, wide per-document vocabulary pinning signatures at the 128 B cap. The
real measurement is 230 B/doc against a projected 351. **Per Arpit's ruling the
per-bucket-zlib change was contingent on the synthetic confirming >30 MB. It did
not, so nothing was changed.** The extrapolation is left in the tracker as an
honest record of a prediction that missed, and the direction it missed in.

The df sidecar lands at 9 B/doc against a 14 B/doc reading at 1k — vocabulary
grows sublinearly (Heaps' law) while documents grow linearly, exactly as
predicted.

### FuxVec scan — IVF not built

**54.5 ms** at 100k, against the handoff's 150 ms authorisation threshold. IVF
is therefore **not implemented**. Note this is ~15× the 3.5 ms measured on
raw integers, because `prefilter` converts each stored 32-byte code with
`int.from_bytes` on every query; caching codes as integers at load would
recover most of that. Not done, because 54 ms is already well inside budget and
an unnecessary optimization is unnecessary risk.

### Latency — the honest finding

| path | measured |
|------|----------|
| full | 10 570 ms |
| lean, cold | 16 733 ms |
| lean, **warm** | **4 105 ms** |

**These are bad, and the cause is specific: the query path still loads the whole
index into memory to build the `Searcher`, even though the substrate now stores
it in queryable rows.** `postings` is populated and indexed at ingest but is
*not read at query time* — `load()` returns every chunk and `Searcher.__init__`
rebuilds all postings in RAM on every CLI invocation. The substrate solved
*storage* at scale; it has not yet solved *query* at scale.

Two consequences worth stating plainly:

1. **Phase 4 does not deliver sub-second queries at 100k**, and nothing in this
   ADR should be read as claiming it does. Below ~25k chunks (the JSON/sqlite
   threshold) the load cost is the tens of milliseconds ADR 0003 measured.
2. **Lean is *faster* than full at scale** — 4.1 s warm vs 10.6 s — which
   inverts the expected trade. Lean builds a `Searcher` over ~50 candidate
   documents; full builds one over 116 756 chunks. The footprint profile turns
   out to also be the latency profile, for the opposite reason to the one the
   proposal anticipated.

**The fix is scoped and obvious**: query `postings` by term instead of loading
every row — the table, its index, and the exact corpus statistics needed to
score without a full scan all already exist. That is the first item for the next
phase, not a defect to hide here.

### Ingest

**566.6 s** for 100k documents (5.7 ms/doc), dominated by stdlib embedding of
116 756 chunks. Linear in corpus size and fully incremental afterwards.

## Alternatives considered

- **Compress the text instead of dropping it** — entropy forbids the target;
  600 MB of prose does not become 20 MB.
- **Per-bucket zlib for `meta/`** — prepared as the contingency if the benchmark
  confirmed >30 MB. It did not; not implemented.
- **Approximate lean scoring** — rejected at M3a; see ADR 0008.
- **Lean as the `auto` default at any size** — rejected above.

## Consequences

**Easier.** 100k documents cost 23 MB of committed state — small enough that a
clone is instantly useful, and `git log .fux/state/` becomes corpus history.

**Harder.** Cold-document latency is real: the first query touching a document
pays re-conversion. The LRU bounds the pain to once per document per eviction
cycle.

**Owed.** The postings-lookup work above. Until it lands, `[index] format` at
scale improves storage and determinism, not query speed.

## References (required)

- [BitFunnel (SIGIR 2017)](https://dl.acm.org/doi/10.1145/3077136.3080789) —
  signature-based indexes as a production-viable way to keep an index small;
  the lean plane's lexical prefilter follows it.
- [Managing Gigabytes (Witten, Moffat, Bell)](https://people.eng.unimelb.edu.au/ammoffat/mg/) —
  the classic-IR baseline the lean profile is measured against: compressed
  inverted indexes land at 10–15 % of corpus size (~15–22 MB here for text
  alone); storing only what determinism cannot reproduce goes an order of
  magnitude below that.
- [Heaps' law](https://en.wikipedia.org/wiki/Heaps%27_law) — why the df sidecar
  grows sublinearly in documents, which is what keeps it at 0.9 MB @100k.
- Internal: [ADR 0008](0008-substrate-store-lock-state.md) (the sidecar that
  makes lean provable) · [ADR 0003](0003-bm25f-index-query-surface.md) (the
  JSON-load measurement this benchmark supersedes at scale) ·
  [`../proposals/knowledge-substrate.md`](../proposals/knowledge-substrate.md)
  §8b, §8c.
