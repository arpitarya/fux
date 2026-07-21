---
type: ADR
title: ADR-0008 — SQLite substrate, fux.lock, and the committed state plane
description: One store for the corpus, a committed sources ledger, and a lean state plane small enough for git — including the exact df sidecar that keeps lean scoring provable.
timestamp: 2026-07-22T00:00:00Z
---

# ADR-0008: SQLite substrate, `fux.lock`, and the committed state plane

- **Status:** accepted
- **Date:** 2026-07-22
- **Feature:** Knowledge substrate storage layer (handoff 0004, M1–M3a)

## Context

v0.22 stored the corpus as a per-file cache plus three whole-file artifacts:
`index.json`, `vectors.bin`, `manifest.jsonl`. Each is fine at Anton's scale and
each has a breakpoint the enterprise design point crosses immediately:

| Artifact | Breaks at | Why |
|----------|-----------|-----|
| per-file cache | ~10⁴ files | directory walks, inodes, AV/sync scanning |
| `index.json` | ~25–50k chunks | full JSON parse on every CLI invocation |
| `vectors.bin` | ~100k chunks | whole file loaded to score a handful |
| `manifest.jsonl` | ~100k rows | linear scan for one lookup |

A second problem was orthogonal to size: **git carried nothing useful.** A clone
had the sources and `fux.toml`, but no way to know whether an index built from
them was the same corpus a colleague indexed, and no way to answer anything
until a full ingest had run.

## Decision

**One SQLite file** (`.fux/index/fux.db`, `format_version = 2`) holds text,
chunks, postings, vectors, codes, edges and the crawl frontier. `sqlite3` is
stdlib, so the `$0` guarantee is untouched. SQLite is **storage, not scoring** —
Fux's BM25F remains the ranker.

`[index] format = json | sqlite | auto` keeps small corpora on the JSON path and
switches past `sqlite_threshold` chunks. Both backends persist the *same dict
shape*, so the `Searcher` cannot tell them apart — proven by running all six
v0.22 goldens against the sqlite backend byte-for-byte, not asserted.

**`fux.lock`** (repo root, committed) replaces `.fux/manifest.jsonl` as the
ledger: sorted JSONL, one line per source, canonical separators. Staleness is
structural per kind — `file` compares sha, `url` compares age against
`max_age_days`, because you cannot sha a page you have not re-fetched.
`fux ingest --check` reads *only* the lock, so it works on a fresh clone.

**`.fux/state/`** (committed) is the lean plane: 256 buckets per family, sharded
by `sha256(doc_id)[0]`, holding a 32 B FuxVec code, a Bloom term signature and a
compressed metadata record per document. Sharding is what makes it commit-safe —
a change touching 50 documents rewrites a few small files, not one 20 MB blob.

**`state/df/`** — the exact document-frequency sidecar (amended into §C by Arpit
on 2026-07-21, see below).

### Bloom sizing (handoff open question 1, decided)

k = 4 hashes, m = 9.6 bits per unique term, byte-aligned, clamped to [8, 128] B:

| unique terms | signature | bits/term | FPR |
|--------------|-----------|-----------|-----|
| ≤ 6 | 8 B (floor) | ≥ 10.7 | < 1 % |
| 25 | 30 B | 9.6 | ~1.4 % |
| 100 | 120 B | 9.6 | ~1.4 % |
| ≥ 107 | 128 B (cap) | ≤ 9.6 | grows with n |

9.6 bits/term is the knee where more bytes stop buying candidate reduction. The
cap bounds the committed plane; long documents simply surface as candidates more
often, which costs scoring time and never correctness — the filter is one-sided,
and exact scoring runs downstream.

### The df sidecar (spec amended by Arpit, 2026-07-21)

Building M3 surfaced a genuine conflict between two committed guarantees: DoD 7
promised rankings *identical* across profiles, but the lean profile could only
recover exact **tf** (by re-deriving text). BM25F also needs **df**, **n** and
**avg_wlen**, which are corpus-level and unavailable from a candidate slice.
Estimating df from Bloom signatures would have quietly redefined "identical" as
"approximately identical".

The escalation was ruled on rather than absorbed: **do not soften the guarantee;
store the missing inputs exactly.** `state/df/XX.bin` holds term hashes sharded
by hash low byte, ascending and delta-encoded, each followed by a varint df.

Two implementation choices inside that amendment, **both approved by Arpit as
improvements rather than deviations**:

1. **`_stats.bin` stores per-field token *sums* as integers, not averages.**
   Integers round-trip exactly, and `avg_wlen = (h·ΣH + p·ΣP + b·ΣB) / n` can
   then be recomputed for *any* `[engine.bm25f]` weights without re-ingesting —
   re-weighting the ranker no longer invalidates the sidecar.
2. **Stats live in one file, not repeated per bucket.** Corpus counts change
   whenever any document does; duplicating them 256 times would dirty every
   bucket on every commit, defeating the sharding they live inside.

Collisions are detected at build time and raise. Two terms sharing a u64 hash
would merge their df and make the exactness claim false with no symptom, so it
fails loudly instead.

## Alternatives considered

- **FTS5 instead of own postings** — rejected for now: score parity with the
  shipped BM25F is the whole point, and FTS5 brings its own ranker. Recorded as
  the fallback if posting-row volume disappoints; M8 measured `fux.db` at
  ~107 B/doc, which does not force the question.
- **Lock replaces the manifest entirely** — the lock deliberately carries only
  the committed fields; ingest and query still need cache path, line offset and
  title. The manifest survives *relocated* into the gitignored runtime plane.
  Git carries the recipe; the runtime keeps its joins.
- **Approximate df from Bloom signatures** — the option the escalation rejected.
  Cheaper, and it would have made the parity guarantee unfalsifiable.
- **Storing full term strings in the sidecar** — exact without collision risk,
  but ~2× the bytes. The u64 hash plus build-time collision detection is exact
  *for any corpus that indexes successfully*, which is the same guarantee.

## Consequences

**Easier.** One file on disk at any corpus size. `--check` works on a fresh
clone. `git log .fux/state/` becomes the history of what the corpus knew.
Re-weighting BM25F no longer requires a re-ingest.

**Harder.** Two backends to keep behaviourally identical — mitigated by running
the same goldens against both. The state plane is binary, so humans diff the
lock (readable JSONL, same commit) to see what changed.

**Owed.** `web:` ids now apply to *all* fetched pages, not just bulk-tier ones:
scoping them to bulk would have made every curated web document a permanent
STATE-DESYNC, since state and lock would key it differently. The URL travels
beside the id as JSON `url` provenance.

## Measured (M8, 100k synthetic)

See [ADR 0011](0011-profiles-lean-state.md) for the full size table. The
sidecar's own numbers: **~10 B/term**, well inside its 5 MB budget at 100k,
because vocabulary grows sublinearly (Heaps' law) even as documents do not.

## References (required)

- [BitFunnel: Revisiting Signatures for Search (SIGIR 2017)](https://dl.acm.org/doi/10.1145/3077136.3080789) —
  the Bing production system that validates per-document Bloom signatures as a
  real index structure rather than a toy; the basis for the lean plane's
  lexical prefilter.
- [SQLite FTS5 in practice](https://thelinuxcode.com/sqlite-full-text-search-fts5-in-practice-fast-search-ranking-and-real-world-patterns/) —
  scale characteristics of SQLite as a text-search substrate (accessed 2026-07-21).
- [pip requirements file format](https://pip.pypa.io/en/stable/reference/requirements-file-format/) —
  the `@list` precedent for keeping a committed recipe small at scale.
- Internal: [`../proposals/knowledge-substrate.md`](../proposals/knowledge-substrate.md)
  §3, §8, §8a, §8c · [`../handoff/0004-knowledge-substrate-handoff.md`](../archive/0004-knowledge-substrate-handoff.md)
  §A–§C (§C amended 2026-07-21).
