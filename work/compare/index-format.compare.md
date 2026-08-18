---
type: Compare Doc
title: Index Format
description: What the committed index physically is — tiered JSONL (doc-major committed, blocked term-major derived, binary-as-property at mega-scale) vs the MST + bit-packed wire design. Decided by four measurements.
status: accepted
timestamp: 2026-08-09T00:00:00Z
---

# Index format — Comparison

> **Verdict: tiered JSONL, one schema.** The committed index is **doc-major
> canonical JSONL** (one line per document, 256 shards by id-hash, sorted;
> git itself is the Merkle tree). The query accelerator is **derived,
> gitignored, blocked term-major JSONL** with integer `mx` (block-max)
> skipping. At mega-scale the same record swaps `terms:{…}` for
> `tpack:` (a base64 binary property) and the mmap segment design returns
> as tier T2 — a field-level change, not a format fork. Full postings, no
> pruning (P1-RERUN). **Supersedes the MST keyspace + BIC wire verdicts
> for the committed plane** ([keyspace-unification](keyspace-unification.compare.md),
> [wire-format](wire-format.compare.md) — see their amendment notes).
> **Status:** ✅ accepted (Arpit, 2026-08-09, in session) ·
> **Confidence:** high — every load-bearing claim below is measured, not
> estimated.
> **Reopen when:** a corpus needs T2 before ~200k docs (JSONL parse tax
> worse than modeled), or canonical-JSON reproducibility breaks across
> Python versions (then the writer pins harder or goes binary).

## §1 · For humans — the idea in one paragraph

Arpit's question was: "`fux ask` can deterministically parse a JSONL file —
why a binary index at all?" Measurement says he is right up to a large
scale: a JSONL file **sorted by term is already an index** (binary search
over mmap = 0.035 ms/query — the SSTable idea), git's own delta compression
absorbs large JSONL beautifully (a one-line edit in a 138 MB shard commits
in 2.5 s and packs to almost nothing), and the one genuine failure mode —
common terms with megabyte posting lines — is fixed by splitting postings
into 128-entry block lines with a max-impact integer read *without parsing*
(397 ms → 44 ms, measured). So: commit the readable thing, derive the fast
thing, and reserve binary for the tier where text arithmetic genuinely
stops working (~200k+ docs). Binary lives *inside* the same records as
base64 properties (`code`, `tpack`) — his "binary can be another property"
rule.

## §2 · The measurements (cloud sandbox, 2026-08-09; RFC-measured density ~1 000 terms/doc)

| # | question | result |
|---|---|---|
| B1 | naive scan: json-parse every doc line, 5k docs / 65 MB | 653 ms per query → dead past ~10k docs |
| B2 | C-speed substring prefilter, parse matches only | 191 ms @5k → usable cold-clone fallback to ~20k |
| B3 | **sorted term-major JSONL, mmap bisect** (offset table: 2 MB, built in 0.1 s) | **0.035 ms** per 4-term lookup, O(log n) — flat in corpus size |
| B4 | common-term line, df=400k (the trap B3 hides) | 5.1 MB of JSON, **397 ms** to parse |
| B5 | B4 split into 128-posting block lines + `mx` skip (string-slice read, no parse) | **44 ms**, parsing 12 % of blocks |
| B6 | git: 138 MB JSONL shard, commit; edit ONE line; commit; gc | 2.4 s / 2.5 s / repo **52 MB** after both (0.38× pack; the edit deltas to ~nothing) |

Also relied on: P1-RERUN (full postings required — pruning FAILED);
corpus-gate measurements (RFC density 13 KB/doc raw doc-major; the actual
target domain measured ~2.5× lighter at median 425 terms).

## §3 · The tiers — one schema, one knob

| tier | corpus | committed | query path | measured basis |
|---|---|---|---|---|
| **T0** | ≤ ~20k docs | sharded doc-major JSONL | derived term-major (seconds to build); cold clone answers via B2 scan | B2, B3 |
| **T1** | ≤ ~200k | same | + blocked accelerator with `mx` skipping | B3, B5 |
| **T2** | beyond | same records, `terms` → `tpack` (binary property); external-source shards only; partial clone | mmap byte-aligned segments (the old wire/runtime design, demoted to top tier) | P1-RERUN option E; archived wire-format numbers |

`[index] tier = t0 | t1 | t2 | auto` — the same shape as v0.26's
`json | sqlite | auto`, a pattern this repo has already run in production.

## §4 · Size model (replaces paper §5; full postings, measured densities)

| corpus | raw doc-major | git-packed (×0.38 measured) |
|---|---|---|
| 100k docs, target-domain density (~4–5 KB/doc) | ~450 MB | **~170 MB** |
| 100k docs, RFC density (13 KB/doc) | ~1.3 GB | ~500 MB |
| 1M docs | 4–13 GB | T2 territory — binary + external-shards-only + partial clone |

## §5 · Schema of record

Authoritative field-by-field: [`../adr/0004_index-format.md`](../../archive/adr/0004_index-format.md)
*(written at M1; until then the session sample of 2026-08-09 governs)*.
Summary: per-doc record carries ledger (`id src loc sha ver mode meta`),
postings (`terms: {16-hex-hash: [tf_heading, tf_body]}` — 8-byte hashes,
collision-checked at build), dense `code` (32 B base64url), typed graded
`edges` (int grades 0–10, incl. `ambig`), display `title/phrases` (or
`title_h` under `meta:hashed`), `wlen`, `community`. Line 1 of every shard
is the `_format` header pinning schema/analyzer/field-order. Canonical
rules: sorted keys, `,`/`:` separators, lines sorted by `id`, **no floats
anywhere in committed bytes**, no wall-clock. Corpus statistics (df, N,
averages) are never committed — derived in one pass.

## §6 · Options considered

- **A — tiered JSONL** *(verdict)*: as above.
- **B — MST keyspace + BIC bit-packed wire** (the prior verdict): smallest
  committed bytes (~5–8× less than JSONL), but: opaque to diff/review,
  ~800 LOC custom substrate, decode-once inflation on every clone, and its
  size advantage mattered most under the 6 %-pruning assumption that
  P1-RERUN killed. Survives as T2's internals.
- **C — pure scan, no derived structure** (the literal reading of Arpit's
  question): B2 says workable to ~20k docs; kept as T0's cold path, not
  the steady state.
- **D — SQLite** (v0.26's answer): known-good, but reintroduces a binary
  blob git can't diff and a second storage engine; the JSONL + git pair
  covers the same ground with one fewer moving part.

| criterion (weight) | A JSONL tiers | B MST+BIC | C scan | D SQLite |
|---|---|---|---|---|
| committed size @100k (H) | ~170–500 MB packed | **~60–150 MB** | same as A | ~300 MB, undiffable |
| diff/review/merge in git (H) | **line-wise, measured** | opaque | line-wise | opaque |
| query latency (H) | 0.035–44 ms | fastest | 191 ms→dead | fast |
| implementation cost (H) | **~300 LOC** | ~2k LOC | ~100 LOC | moderate |
| zero-build-step clone answers (M) | **yes (B2)** | no (inflate) | yes | no |
| determinism surface (M) | canonical text | binary spec | text | SQLite internals |

## §7 · For AI agents — binding rules

- Committed writer: canonical JSON (`sort_keys`, `(",",":")` separators),
  shard = `blake2b(id)[0]` hex pair, lines sorted by `id`, header line
  first. Byte-identical double-ingest is a test, not a hope.
- 16-hex (8-byte) term hashes; build fails loudly on collision (archived
  ADR-0008 discipline).
- `mx` and edge grades are **integers**. A float in committed bytes is a
  bug.
- The accelerator is derived, gitignored, and **must reproduce scan
  results exactly** (differential test, same law as the ARC cache).
- `tpack` swap-in is per-record and mechanical; readers must accept both
  forms from day one (the schema is the contract, the tier is a knob).

## §8 · References

SSTable (LevelDB/RocksDB storage primitive) · [Loki's small-index +
scan philosophy](https://letsbuildsolutions.com/blog/system-design/how-grafana-loki-works-internally-label-based-indexing-log-chunk-storage-and-the-cost-efficient-architecture/) ·
[Loki vs Elasticsearch](https://signoz.io/blog/loki-vs-elasticsearch/) ·
Block-Max WAND (Ding & Suel, SIGIR '11 — reborn here as the `mx`
property) · internal: [P1-RERUN](../regression/2026-08-09-pruning-rerun/VERDICT.md)
(why full postings) · session benches B1–B6 (reproduce: the bench scripts
are in the 2026-08-09 session log; M1 re-lands them as
`tools/bench-format/`).

## §9 · Reopen-trigger

See verdict block. First measurement that can fire it: M2's accelerator
bench on the RFC corpus.
