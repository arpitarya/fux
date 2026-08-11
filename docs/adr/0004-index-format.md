---
type: ADR
title: "ADR-0004: Index format & committed store — schema, canonical rules, unicode policy frozen"
description: Freezes the M1 T0-slice schema of record, the canonical-writer rules, and the analyzer version, closing several fields the compare doc named but did not fully specify (sha algorithm, ver semantics, meta shape, edge grades, stopword filtering). R1 measured PASS; R2 measured 2/3 PASS, 1/3 blocked on a pre-existing doc-hygiene gap unrelated to this build.
status: accepted
timestamp: 2026-08-10T00:00:00Z
---

# ADR-0004: Index format & committed store

- **Status:** accepted
- **Date:** 2026-08-10
- **Feature:** M1 — the T0 vertical slice (canonical store, git-dir ingest,
  scan-based `fux ask`), per
  [`../handoff/v0.30.0-m1-t0-slice-handoff.md`](../handoff/v0.30.0-m1-t0-slice-handoff.md).

## Context

[`index-format.compare.md`](../compare/index-format.compare.md) §5 named the
schema of record's fields (`id src loc sha ver mode meta … terms … edges …
code … title/phrases … wlen`) and pointed at "the session sample of
2026-08-09" as the governing example until this ADR shipped. That sample was
never committed to this repo — it existed only in an ephemeral session log.
Building `store/` therefore required resolving several field-level questions
the compare doc named but did not fully specify. Per the handoff's own
guardrail ("ask before … any schema field not in the spec"), those were
resolved with Arpit during the build rather than guessed; this ADR is where
they become the frozen record, per handoff §10.

## Decision

**The schema, canonicalization rules, and M1-era defaults below are frozen.**
Changing any of them is a schema change and needs its own ADR.

### Ledger fields

| field | value this milestone | decided |
|---|---|---|
| `id` | `"file:" + posix_relative_path`, NFC-normalized | compare doc §5 |
| `src` | `"git"` (the only adapter this milestone) | this build |
| `loc` | the posix relative path (no `file:` prefix) | this build |
| `sha` | `blake2b(content_bytes, digest_size=20).hexdigest()` — 40 hex | **this build, asked** |
| `ver` | monotonic int per record; starts at 1; bumps only when `sha` changes on a later ingest | **this build, asked** |
| `mode` | `"extracted"` (the only ingest mode this milestone; `enriched` is M8) | ADR-0001 |
| `meta` | string enum `"plain" \| "hashed"` — **not** a nested dict. `"plain"` carries `title`/`phrases`; `"hashed"` would carry `title_h` instead and no `phrases`. Only `"plain"` is exercised this milestone (git is never hashed-meta, per CLAUDE.md's non-git-only law) | **this build, asked** |

`sha` deliberately reuses the same hash family as `term_hash`/`shard_for`
(blake2b, different `digest_size`), not a literal git blob sha1 — one
algorithm across the whole store, and no dependency on git plumbing (the
git-dir adapter reads files directly off the filesystem, not via `git
cat-file`).

### Postings, dense, edges, display

- **`terms`**: `{16-hex blake2b(term, digest_size=8): [tf_heading, tf_body]}`.
  **Two fields, not three** — the archived engine's `path` field is dropped;
  path-derived signal now flows only through `code`/`ref` edges, not BM25F.
  Both tf values are non-negative integers; empty/zero entries are omitted.
- **`wlen`**: integer, `3*heading_tokens + 1*body_tokens` (heading weight 3,
  body weight 1 — matches the archived non-path BM25F defaults). A heading
  line's own tokens are excluded from the body count (there is no chunker
  yet; without this exclusion a heading's words would count twice).
- **`code`**: FuxVec sign-quantized embedding of `title + "\n" + body`,
  32 bytes, base64url, **no padding**. Omitted (not null) when nothing in
  the document is embeddable. **Bundled and computed this milestone** —
  `src/fux/embed/` (ported: `model.py`, `fuxvec.py`; `store.py`'s chunk-vector
  *cache* is not ported, since `code` lives directly in the ledger record now)
  including the 7.9 MB `data/model.bin`, even though the dense lane doesn't
  query it until M2/M3. Decided this build: the model is a packaged data
  asset, not a runtime dependency, and shipping it now avoids a schema
  migration later.
- **`edges`**: `[{"kind": "ref"|"tag"|"code", "dst": <id or "tag:<name>">,
  "grade": <int 0-10>}]`, sorted by `(kind, dst)`, deduplicated. Grades:
  `EXTRACTED = 10` (deterministic, unambiguous — a resolved link, a
  frontmatter tag, an exact backtick-path match), `AMBIG = 8` (a `code` span
  resolved only by unique basename among several path candidates),
  `INFERRED = 6` (unused until the `enriched` tier, M8 — kept for scale
  parity with the archived `EXTRACTED`:`INFERRED` ≈ 1.0:0.6 weight ratio).
  Written this milestone, not read — the graph lane is M3.
- **`title`/`phrases`**: `title` — frontmatter `title`, else the first
  heading, else the filename. `phrases` — **headings only**, capped at 12
  (the simpler of the handoff §10's two open options; first-sentence
  extraction is not built).

### Canonical writer (`store/`)

- `json.dumps(rec, sort_keys=True, separators=(",",":"), ensure_ascii=False)`
  + `"\n"`, encoded UTF-8.
- **No floats, no nulls, anywhere in committed bytes** — enforced
  recursively at the write boundary (`store/canonical.py`), not trusted of
  callers.
- **NFC normalization enforced on every string value AND every dict key** —
  `unicodedata.normalize("NFC", s) == s`, checked recursively. (A dict-key
  gap here was the first finding of this ADR's own Opus review checkpoint —
  see Consequences.)
- **U+2028/U+2029/U+0085 rejected in text** — legal JSON, but
  `str.splitlines()`-class readers (including an early version of this
  store's own reader) split on them even though the JSON writer emits them
  raw inside a string. Shard files are read by splitting on `\n` only, never
  `str.splitlines()`.
- Lone UTF-16 surrogates raise `FuxError` at the write boundary instead of a
  raw `UnicodeEncodeError` (reachable via `os.fsdecode` of an undecodable
  filename on Linux).
> **Path note (2026-08-12, added without altering this record):** every
> `examples/playground/` path below refers to the fixture that was deleted
> and rebuilt as the sibling repo `fux-playground`
> ([ADR-0012](0012-playground-sibling-repo.md)). The evidence this ADR
> cites was measured against that fixture as it stood; the text is left
> unedited because an accepted ADR is a record of what was decided and on
> what basis.

- **Sharding is fixed at 256, not configurable this milestone**:
  `shard = blake2b(id_bytes, digest_size=1).hexdigest()` → `.fux/index/{00..ff}.jsonl`.
  `fux.toml`'s `[index] shards` key is accepted but must equal `256` — it
  documents the value rather than setting it. (`examples/playground/fux.toml`
  originally set `shards = 16`, written before this ADR; corrected to `256`
  — see Consequences.)
- Every shard opens with the identical `_format` header line pinning
  `analyzer` and `tf_fields` order; the reader refuses a shard whose header
  doesn't match (a reversed `tf_fields` would silently invert every
  heading/body tf with no error anywhere downstream).
- **Full rewrite per shard, every run** — never an in-place patch. A shard
  whose bytes come out identical is left untouched on disk (no mtime churn);
  "incremental" is this emergent property, not literal line-patching. Writes
  are atomic (`os.replace` from a sibling temp file) — a crash mid-write
  cannot leave a truncated shard.
- **Collision detection**: one `CollisionTracker` shared across an entire
  ingest run (never per-document — a document's own `terms` are already
  deduplicated, so only *cross-document* collisions are possible, and a
  fresh tracker per document would catch none). Raises `FuxError` naming
  both colliding terms.

### Query (`query/`)

- **Tokenizer**: lowercase runs of `[a-z0-9_]`, ported from the archived
  BM25F module, **plus a fixed English stopword list — added during this
  build, not in the original spec.** R2 (below) measured its absence letting
  a glossary's dictionary-style repetition of "what"/"is"/"the" outrank the
  focused, correct answer to a natural-language question. Standard IR
  practice (every BM25 system pairs it with stopword removal), and the same
  list `archive/v0.26/src/fux/graph/extract.py` already used — not tuned to
  the one query that surfaced the gap; both R2 questions it touched were
  re-verified after the change, not just the one that had been failing.
- **Scan**: B2 byte-level prefilter — a shard line is `json.loads`'d only if
  it contains one of the query's term-hash patterns as a quoted substring.
  `n`/`avg_wlen` are still derived every run (never stored) via a cheap
  regex extraction of `wlen` from every line's raw bytes, not a full parse —
  the prefilter's purpose (avoid `json.loads` on the common case) survives
  even though corpus-wide stats need to touch every line.
- **BM25F**: weight-then-saturate once (CLAUDE.md law), heading=3.0/body=1.0/
  k1=1.2/b=0.75 — the archived defaults minus the dropped `path` field.
  Deterministic tie-break on `id` for equal (rounded) scores.

## Alternatives considered

| option | why it lost |
|---|---|
| Configurable shard count (`[index] shards` actually changes bucketing) | `examples/playground/fux.toml` had already committed to `shards = 16`, conflicting with the handoff's fixed `digest_size=1` formula. Store's canonical writer was already built and Opus-reviewed against the fixed scheme; making it configurable mid-build would have meant re-running that checkpoint for a knob nothing in M1 needs. Deferred, not ruled out — a real future knob if T0 corpora prove large enough to want fewer, denser shards. |
| Defer FuxVec's `code` to M2/M3 (skip the 7.9 MB model this milestone) | Considered — `code` is written but not queried until M2/M3, so bundling it now buys nothing operationally this slice. Decided to bundle anyway: it's the one place the *port* (not just the schema) needed doing, and doing it once now avoids a second schema-touching change later. |
| Literal git blob sha1 for `sha` | Matches `git cat-file`/`git ls-tree` output directly, useful for cross-checking against git. Costs a second hash algorithm in the codebase and ties the ledger to git-specific plumbing the git-dir adapter doesn't otherwise use (it reads files off the filesystem, not via git objects). |
| `ver` always `1` in T0, real semantics deferred to M5 | Simpler now, but M5's merge driver needs `(ver, sha)` LWW (PLAN.md §M5) and would have to retrofit versioning onto every already-committed line. Cheaper to get it right from the first commit. |
| Leave `fux ask` un-filtered (report the R2 miss as a known gap, no fix) | Real option, and the user was asked directly (see Consequences) — but stopword filtering is standard practice, not query-specific tuning, and the fix is one file. Chosen over reporting-only. |

## Consequences

**What R1/R2 measured, this build:**

- **R1 — PASS**, confirmed live on the full ubuntu+macos+windows CI matrix
  at the `v0.30.0` push (not just asserted locally). Double-ingest on this
  repo produces byte-identical shard sha256s (verified locally: `shasum -a
  256 .fux/index/*.jsonl` unchanged across two runs, second run reports `0
  shards written`); `tests_e2e/test_determinism.py` asserts the same
  through the real CLI. **The matrix earned its keep**: the first push
  (`c52948b`) was red on both `windows·py3.11` and `windows·py3.14` — not
  an R1 failure, but a real bug R1's own CI wiring caught: `fux doctor`
  printed a Unicode checkmark (U+2714) that crashes on Windows' default
  console codepage (`cp1252`/"charmap" can't encode it), so the process
  exited 1 with a raw `UnicodeEncodeError` instead of printing. Fixed
  (`83c1888`, ASCII `[OK]`/`[FAIL]` markers) with a regression test that
  forces `PYTHONIOENCODING=ascii` on any platform, not just Windows.
- **R2 — 2 of 3 PASS, 1 blocked on a pre-existing gap:**
  1. `"why did pruning fail"` → cites `docs/adr/0003-…` in the top 2. **PASS.**
  2. `"what format is the committed index"` → initially missed the top 5
     (`docs/compare/index-format.compare.md` ranked #9, behind
     `docs/GLOSSARY.md`'s dictionary-style term repetition). Fixed by adding
     stopword filtering to the tokenizer (see Decision); re-verified after
     the fix — now #1. **PASS, after a measured fix.**
  3. `"supersession penalty safe interval"` → the frozen citation target,
     `archive/v0.26-docs/…`, **does not exist**. This is not a defect
     introduced by this build: the (since-removed) `docs/archive/README.md`
     already flagged the discrepancy on 2026-08-09 (before M1 started) — the
     v0.26 doc set actually lives at
     `archive/v0.26-docs/adr/0015-supersession-downrank-penalty.md`,
     outside M1's configured sources (`docs`, `README.md`, `CLAUDE.md`) and
     explicitly out of scope to touch. The underlying content **is**
     reachable and correctly cited from an in-scope, live doc —
     `docs/conformance/README.md` ranks it #1 for this query, and states
     "safe interval `[11, ∞)` … → ADR-0015" directly. **Decided (asked):**
     report this as testing a stale assumption rather than move the doc
     set as part of this change — that move was Arpit's open call, out of
     scope for a schema-and-store ADR to resolve unilaterally.
     **[Resolved 2026-08-10 — Arpit's ruling: everything archived lives in the root `archive/`; there is no `docs/archive/`. The v0.26 doc set now sits at `archive/v0.26-docs/`, the nested double-archive is flattened, and the flagged discrepancy is closed.]**
- **Playground walkthrough** (`examples/playground/`): all three
  `PLAYGROUND.md` questions answer with on-topic citations from the real
  index; the retry-budget superseded pair (ADR-0002/ADR-0005) both surface
  for `"retry budget"`; double-ingest is a no-op (`git status` clean);
  editing one doc and re-ingesting changes exactly one shard file. Two doc
  bugs found and fixed in `PLAYGROUND.md` itself (never the fixture corpus,
  per the handoff's own rule): the "16 shards" comment (stale — fixed at
  256, most empty at 20 docs) and a hardcoded `.fux/index/03.jsonl` example
  path that doesn't exist under the real (sparse) shard assignment, replaced
  with `$(ls .fux/index/*.jsonl | head -1)`.
- **Opus review checkpoint** (handoff §11, before `ingest/`/`query/` were
  built on top of `store/`): two blockers found and fixed before proceeding
  — dict keys were never NFC-validated (only values), and the reader split
  shard bytes with `str.splitlines()`, which breaks on U+2028/2029/0085 that
  the writer legally emits raw inside string values, meaning the store could
  not read its own legal output. Ten further should-fix/nit findings
  (header field validation, atomic writes, golden-vector tests, shard-file
  glob scoping, cross-shard duplicate-id detection, and others) were also
  applied; see the store/ module docstrings and test suite for the specifics.

**What this does not settle:** whether `[index] shards` ever becomes a real
per-corpus knob (parked, see Alternatives); ~~whether the v0.26 doc set moves~~ (resolved 2026-08-10: root archive is
canonical — `archive/v0.26-docs/`); the dense (`code`) and graph (`edges`) lanes
remain unqueried until M2/M3, per the handoff's scope fence.

## References (required)

- [`docs/compare/index-format.compare.md`](../compare/index-format.compare.md)
  §5/§7 — the schema of record this ADR fills in and freezes.
- [`docs/handoff/v0.30.0-m1-t0-slice-handoff.md`](../handoff/v0.30.0-m1-t0-slice-handoff.md)
  — the binding contract this ADR closes out.
- [`archive/README.md`](../../archive/README.md) — the root-archive index;
  the discrepancy behind R2 question 3, since resolved (2026-08-10).
- `archive/v0.26/src/fux/index/bm25f.py`, `archive/v0.26/src/fux/frontmatter.py`,
  `archive/v0.26/src/fux/embed/` — the ported modules this ADR's schema
  builds on.
- **Robertson, S., Zaragoza, H.** *The Probabilistic Relevance Framework:
  BM25 and Beyond.* Foundations and Trends in Information Retrieval, 2009 —
  the weight-then-saturate BM25F formulation this store's scorer implements.
- **Manning, C., Raghavan, P., Schütze, H.** *Introduction to Information
  Retrieval*, ch. 2 — stopword removal as standard IR practice, the
  grounding for this build's tokenizer addition.
