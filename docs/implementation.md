---
type: Implementation Tracker
title: Implementation tracker — live build status
description: Milestone-level status of everything being implemented; the building agent updates it at every milestone completion and at regular intervals during long runs.
timestamp: 2026-07-21T00:00:00Z
---

# Implementation tracker

*The live, honest ✅/🟡/⬜ of the build. **Update contract (binding on the building
agent):** flip a row the moment a milestone completes; during long milestones, bump
the "Now working on" line at regular intervals (roughly every significant commit or
~30 min of work) so an interrupted session loses nothing. Never mark ✅ with failing
tests. This file answers "where exactly is the build?" — the worklog answers "what
happened per exchange"; keep both.*

**Legend:** ⬜ not started · 🟡 in progress · ✅ done (tests green) · ⛔ blocked

## Now working on

> *(building agent: keep this one line current)* — **Phase 4 complete: v0.23.0
> shipped** (M1–M8 + close-out ✅). Suites: 365 unit + 71 e2e · eval hit@5 1.000.
> **Next phase's head: query-at-scale** — postings stored but unread (ADR 0011).

## Baseline (pre-build, done in Cowork)

| Item | Status | Notes |
|------|--------|-------|
| Package skeleton (src/, hatchling, 0.19.0, CLI + FuxError, smoke tests) | ✅ | 4 unit tests |
| All design decisions + compare docs | ✅ | `compare/` — all accepted |
| Build specs 0000–0003 | ✅ | `handoff/` |
| OKF-conformant docs bundle | ✅ | 26/26 files |

## Phase 1 — Query CLI v1 (handoff 0001) → v0.20.0

| Milestone | Status | Tests | Notes |
|-----------|--------|-------|-------|
| M1 config + `fux setup` (wizard/flags/-y, idempotent) | ✅ | 21 | config load/validate, find_root, wizard+flags+-y, idempotent merge |
| M2 frontmatter parser (load-bearing; unit-first) | ✅ | 13 | subset YAML: scalars/lists/nested/literal; permissive; round-trip |
| M3 ingest inferred tier → OKF cache + manifest + chunker | ✅ | 36 | converted_at = SOURCE_DATE_EPOCH/mtime (determinism; → ADR 0002 + Deviations) |
| M4 BM25F index + `ask`/`find` (+ --json/--explain) | ✅ | 16 | JSON index (open Q1 resolved), incremental by sha |
| M5 `answer` (extractive + TextRank + citations) | ✅ | 12 | passage × overlap × centrality; doc-order citations |
| M6 `setup --agents --skills --hooks` | ✅ | 8 | managed blocks, skills pair, fail-open hooks, settings merge |
| M7 `tests_e2e/` suite (corpus + goldens + determinism) | ✅ | 21 | found+fixed --check drift bug and answer noise; goldens pinned to no-extra corpus |
| Close-out: ADRs 0001–0004, docs law, archive pair, bump | ✅ | — | v0.20.0; DOGFOOD.md emitted; suites: 108 unit + 20 e2e (+1 gated skip) |

## Phase 2 — Ingest v1.1: web/CDP/advanced (handoff 0002) → v0.21.0

| Milestone | Status | Tests | Notes |
|-----------|--------|-------|-------|
| M1 HTML→Markdown converter (stdlib, goldens-first) | ✅ | 12 | html.parser; deterministic; link/title extraction |
| M2 urllib fetcher + crawl frontier + robots + `--web` e2e | ✅ | 12+4 | frontier/robots/dedupe/config + fixture-server e2e (M5) |
| M3 RFC 6455 WebSocket client + CDP capture | ✅ | 14 | RFC vectors + fake-server handshake; websocket-client = flagged fallback |
| M4 advanced tier (Docling/Tesseract, fidelity transitions) | ✅ | 6 | (sha, fidelity)-keyed index reuse; upgrades survive re-ingest |
| M5 e2e additions + docs | ✅ | 4+2 | fixture site (robots/oversize/off-domain), import-fence test, manual CDP smoke |
| Close-out: ADR 0005, docs law, archive pair, bump | ✅ | — | v0.21.0; suites: 154 unit + 24 e2e (+1 gated skip) |

## Phase 3 — Hybrid engine v2 (handoff 0003) → v0.22.0

| Milestone | Status | Tests | Notes |
|-----------|--------|-------|-------|
| M1 eval harness + lexical baseline recorded | ✅ | 2 | 21 pairs; lexical: hit@1 0.762 · hit@5 0.952 · MRR 0.833 |
| M2 distillation pipeline (`tools/distill/`, ≤10 MB asserted) | ✅ | — | potion-base-8M re-pack, int8, 7.93 MB, sha-pinned, MIT-checked |
| M3 stdlib inference (`fux.embed`, int8) | ✅ | 10 | exact tokenizer parity; int8 dot; lazy load 10 ms |
| M4 chunk-vector cache (manifest-invalidated) | ✅ | 4 | single vectors.bin; (sha, fidelity)-keyed reuse |
| M5 RRF fusion + `--lexical-only` + explain | ✅ | 3 | k=60; v1 byte-parity proven by unchanged goldens |
| M6 eval gate: hybrid ≥ lexical (numbers → ADR) | ✅ | 1 | tie (gate ≥ passes, ships enabled); rank-level rescues; ADR 0006 |
| M7 packaging (bundle in wheel, lazy load, size checks) | ✅ | 1 | wheel 6.98 MB ≤ 15; bundle ≤ 10 asserted; warm query 0.2 ms |
| Close-out: ADRs 0006–0007, docs law, archive pair, bump | ✅ | — | v0.22.0; suites: 172 unit + 28 e2e (+1 gated skip) |

## Phase 4 — Knowledge substrate v3 (handoff 0004) → v0.23.0

*Pre-registered 2026-07-21 with the handoff (per the CLAUDE.md rule: every plan
seeds its milestone table here before building; the building agent updates a
row at EVERY milestone completion — no batching).*

| Milestone | Status | Tests | Notes |
|-----------|--------|-------|-------|
| M1 sqlite store + fux.lock (parity goldens; lock-only --check; migration) | ✅ | 33+12 | all 6 v0.22 goldens pass byte-for-byte on the sqlite backend; lock at root, manifest → runtime plane |
| M2 bulk tier (docs_text) + `fux cat` + committed `.fux/state/` sharding + three-way check | ✅ | 35+13 | fresh clone answers doc-level from state; rebuild reproduces state byte-for-byte; Bloom sized 9.6 bits/term, k=4 (→ ADR 0008) |
| M3 edges + nodes (deterministic extraction; thin-layer payloads) | ✅ | 22 | references/cites/crawled_from/tagged, all EXTRACTED; tag nodes (N not N² edges); on this repo's docs: 92 refs · 13 cites · 9 tagged |
| M3a df sidecar (`state/df/`) — Arpit's DoD-7 amendment | ✅ | 23 | exact df/n/Σfield-lengths; lean == full proven over the *whole* vocabulary on a subset (mutation-tested: removing the injection fails the test) |
| M4 kernel `retrieve()` + verb projections (explain/graph/path; v0.22 golden byte-parity) | ✅ | 23+6 | all 6 goldens byte-identical through the re-plumb; `explain` = ask seeded by a node (top_terms as query), so no second retrieval path; paths BFS + reliability (PPR at M6) |
| M5 FuxVec (codes, Hamming scan, exact rerank, dense_global into RRF) | ✅ | 16 | **eval gate beats v0.22 hybrid**: hit@1 .762→.810 · hit@5 .952→**1.000** · MRR .833→.873; ADR 0006's named zero-overlap miss rescued; `--lexical-only` still exactly .762/.952/.833 |
| M6 expansion (PPR-lite, paths + reliability, graph list into RRF) | ✅ | 20 | constants as specced; seed-rank personalization; `[engine.graph] in_rrf` is the **open-question-2 instrument** — on the 9-doc fixture graph on/off both measure .810/1.000/.873 (too few edges to discriminate; M8's generator must carry real link structure) |
| M7 profiles (full/lean/auto, LRU) + `db pull` v1 | ✅ | 19 | mid-corpus switch (full→lean) keeps rankings *and* scores — mutation-verified non-vacuous; LRU counter-based (no wall clock); `auto` gated on `lean_threshold` (→ Deviations); `db pull` sha-verified, refuses mismatch |
| M8 scale benchmark (synthetic 100k) + eval gate (≥ v0.22 hybrid + zero-candidate rescue) | ✅ | 9 | 100k measured: state **23 MB ≤30 ✓**, df **0.9 MB ≤5 ✓**, db 1081 MB (77% of §8b), FuxVec scan **54 ms < 150 → IVF not built**; gate beaten (1.000 hit@5); ⚠ **query latency 10.6 s @100k** — postings stored but not read at query time (→ ADR 0011, next phase) |
| Close-out: ADRs 0008–0011, docs law, archive pair, bump | ✅ | — | **v0.23.0**; suites: 365 unit + 71 e2e (+1 gated skip); citations in 0010 verified at build time; 0004 pair archived |

## Size envelope — MEASURED at 100k (M8)

The M3a extrapolation below was **wrong, and in the pessimistic direction** —
recorded rather than deleted, because a prediction that missed is worth keeping
next to the measurement that corrected it.

| component | M3a projection @100k | **measured @100k** | budget |
|-----------|---------------------|--------------------|--------|
| `state/df/` | ~2.1 MB | **0.92 MB** (9 B/doc) | ≤5 MB ✅ |
| `state/codes/` | ~5.1 MB | **4.00 MB** (40 B/doc) | — |
| `state/sigs/` | ~14.4 MB | **6.78 MB** (68 B/doc) | — |
| `state/meta/` | ~15.6 MB | **11.25 MB** (112 B/doc) | — |
| **state TOTAL** | ~35 MB ⚠ | **22.96 MB** (230 B/doc) | ≤30 MB ✅ |
| `fux.db` | — | 1 081 MB | ~1 400 MB est (77 %) |
| `fux.lock` | — | 21.5 MB | ~30 MB est (70 %) |

Why the projection missed: it extrapolated from *this repository's own docs*,
which are adversarial for the state plane — very long doc ids
(`docs/handoff/0004-knowledge-substrate-handoff.md`), long titles, and wide
per-document vocabulary that pins Bloom signatures at the 128 B cap. 351 B/doc
projected vs 230 B/doc actual.

**Per Arpit's ruling, the per-bucket-zlib change was contingent on the synthetic
confirming >30 MB. It did not, so nothing was changed.**

## Decisions taken during the build (→ ADRs)

- **M5 / dense_global does not fire when BM25F returns zero candidates.**
  Removing that early return made the honest "No confident matches" answer
  unreachable, because a binary prefilter always has a nearest neighbour.
  Measured on the fixture corpus: pure-noise queries score **0.23–0.26** cosine
  against a true rescue's **0.34** — the ranges overlap, so any absolute floor
  separating them is a magic number that only degrades as the corpus grows.

  Re-reading ADR 0006 settled it: *"zero lexical candidates"* there means the
  **correct document** had no lexical overlap, not that the query matched
  nothing at all (that query does return `docs/guide.md`). So the rescue path
  is the third RRF list, which always has candidates — and honest emptiness is
  preserved. → ADR 0010.

## Deviations from spec

*(record any deliberate deviation from a handoff here, with the why and the ADR
that captures it — an empty section is the goal)*

- **0001 / `converted_at`:** derived from `SOURCE_DATE_EPOCH` (reproducible-builds
  convention) or the source file's mtime — never wall clock. The handoff lists
  `converted_at` as provenance *and* requires byte-identical double-ingest; a wall
  clock cannot satisfy both. Captured in ADR 0002.
- **0001 / cli-examples.md sketches:** the pre-build examples were aligned to
  as-shipped v1 (2026-07-21): setup wizard = one prompt per source type (no
  cache-location prompt — cache path is fixed in v1); ask/find scores are raw
  BM25F magnitudes, not 0–1; `--check` gained explicit new/missing annotations;
  answer JSON/citation shapes specified. The implementation was reworked to match
  the doc's normative shapes (`--check` advisory + `--strict`→2, JSON `path`/
  `line_start`/`line_end`/`heading_path`/`fidelity` keys, `[n]`+Sources answer
  citations, per-field explain tree, per-kind ingest summary).

- **0004 / df sidecar — SPEC AMENDED BY ARPIT, not deviated from (2026-07-21).**
  The M3 escalation found a real gap between two guarantees: DoD 7 promised
  rankings *identical* across profiles, but lean could only recover exact `tf`
  (by re-deriving text) — `df`, `n` and `avg_wlen` are corpus-level and were
  unavailable, so Bloom-derived `df` would have made "identical" mean
  "approximately". Arpit's call: **do not soften the guarantee; store the
  missing inputs exactly.** Handoff §C now specifies `state/df/XX.bin` and
  DoD 7 now requires a full-corpus lean-vs-full comparison test with the eval
  set as a belt. Implemented in `src/fux/state/df.py`; captured in ADR 0008.

  Two implementation choices inside that amendment, both recorded here:

  - **Per-field *sums* are stored, not averages.** Integers round-trip exactly
    (no float drift), and `avg_wlen = (h·ΣH + p·ΣP + b·ΣB) / n` can then be
    recomputed for *any* `[engine.bm25f]` weights without re-ingesting.
  - **Stats live in `df/_stats.bin`, not repeated per bucket.** The handoff says
    "one header record"; writing it into all 256 buckets would dirty every
    bucket whenever any document changed, defeating the sharding it exists for.
  - **Recomputed per ingest rather than delta-maintained.** The spec describes
    incremental upkeep (`df -= old, df += new`); the index is already fully
    loaded when the plane is written, so one pass is the same cost and cannot
    drift the way a running total can. Output bytes are identical either way.
  - **Hash collisions fail loudly.** Two terms sharing a u64 hash would merge
    their `df` and silently turn the exactness claim into an approximation, so
    the builder detects it and raises rather than absorbing it.

- **0004 / `web:` ids apply to *all* fetched pages, not just bulk-tier ones.**
  Handoff §B shows the `web:<slug>` id in the context of the bulk tier. Applying
  it only there breaks the three-way `--check`: state and index would key curated
  web docs by URL while the lock keys them by `web:` id, so every curated web doc
  would read as a permanent STATE-DESYNC. One id scheme everywhere; the URL rides
  along as provenance (JSON `url` field). → ADR 0008.

- **0004 / the operational manifest survives, relocated.** The handoff says
  `manifest.py` becomes `lock.py`. The lock is the committed *ledger* and
  deliberately carries only the fields §B lists — but ingest and query still need
  cache path, line offset and title. Those live on in
  `.fux/index/manifest.jsonl`, inside the gitignored runtime plane, written in
  the same scope as the lock. Git carries the recipe; the runtime keeps its
  joins. → ADR 0008.

- **0004 / `fux answer` has no state-only mode** *(superseded at M7 — kept for
  the trail)*. This held while a clone could only answer at doc level. Once the
  df sidecar landed, the lean path re-derives candidates and produces real
  line-anchored passages, so `answer` works on a fresh clone with full
  citations. The decline path survives only for the doc-level fallback, where
  sources are genuinely absent. → ADR 0011.

- **0004 / a fresh clone answers *exactly*, not at doc level (M7).** DoD 2 asks
  for doc-level answers from committed state; the df sidecar makes something
  strictly better possible, so a clone with its sources present now returns the
  same rankings *and scores* as the full profile. Doc-level ranking became the
  honest fallback for when sources cannot be re-derived (crawled corpora, or a
  clone without its documents). Exceeding a DoD is still a change to committed
  behaviour, so it is recorded here and reflected in cli-examples. → ADR 0011.

- **0004 / `auto` requires a size threshold, not just re-derivability (M7).**
  §G defines `auto` as "lean when every source in a tier is re-derivable". Taken
  literally that makes lean the default for *every* local repo, silently
  trading query latency for a footprint win that does not exist below a few
  thousand documents — and changing behaviour for every existing small corpus.
  `auto` now additionally requires `[index] lean_threshold` documents
  (default 10 000); `profile = "lean"` remains available explicitly at any
  size. → ADR 0011.
