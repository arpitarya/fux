# Changelog

All notable changes to **fux-engine** (the rebuild line). Dates are ISO; versions
follow semver. The latest entry is mirrored in [README.md](README.md) § What's new.
Maintained on every version bump (registry-tracked).

## [0.23.1] — 2026-07-22 — docs & examples (no engine change)

Documentation-only patch. The wheel is functionally identical to 0.23.0 — the
only source edits are docstring/comment pointers to moved docs and one test that
reads the config example at its new path.

- **Docs bundle reorganized.** Core navigation docs promoted to ALL-CAPS
  entry-point files — `PLAN.md`, `INTERVIEW.md`, `WORKLOG.md`,
  `IMPLEMENTATION.md` — each shedding YAML frontmatter per the repo convention.
- **New `docs/example/` bundle** — copy-from contracts, every block verified
  against real v0.23.x output: `CLI.md` (command I/O), `TOML.md` (annotated
  config), `SETUP.md` (setup variants + `--agents --skills --hooks` install),
  `SKILLS.md` (the two shipped skills + a usage flow), `API.md` (drive the
  engine from another script: create a file → ingest → query).
- **Archive keyed by release version** (`vX.Y.Z-name.md`) instead of the
  in-flight `NNNN` index; in-flight handoffs still use `NNNN-name.md`.

## [0.23.0] — 2026-07-22 — the knowledge substrate

Phase 4 (handoff 0004, ADRs 0008–0011). The engine grew from "index a folder"
to "carry a corpus":

- **One SQLite runtime plane** (`.fux/index/fux.db`): docs, chunks, postings,
  vectors, edges, crawl frontier — replacing `index.json` + `vectors.bin` above
  the threshold; JSON path preserved for small corpora, golden-proven identical.
- **`fux.lock`** — committed sources ledger (sha/date per source; files stale by
  sha, URLs stale by age); `--check` works on a fresh clone, lock-only.
- **Committed lean state** (`.fux/state/`, ~230 B/doc measured): FuxVec codes +
  Bloom signatures + metadata + the **exact-df sidecar** — a fresh clone answers
  with the *same rankings and scores* as a full index (provable, not
  approximate; mutation-tested).
- **FuxVec** — from-scratch stdlib binary dense search (256-bit sign codes,
  XOR + `bit_count()` at ~27 M cmp/s, exact int8 rerank). Eval: hit@1
  .762→.810 · hit@5 .952→**1.000** · MRR .833→.873; ADR 0006's named
  zero-overlap miss now retrieved. `--lexical-only` byte-preserved.
- **One retrieval kernel** — every verb is a projection of `retrieve()`;
  new verbs: `fux explain`, `fux graph`, `fux path`, `fux cat`, `fux db pull`.
- **Profiles** — `full | lean | auto` (lean ≈ 23 MB @100k measured; identical
  rankings across profiles); PPR-lite graph expansion in RRF (instrumented
  on/off — fixture too small to discriminate; real measurement next phase).
- Measured @100k synthetic: state 23 MB, df 0.9 MB, FuxVec scan 54 ms (IVF not
  needed). Known limit → next phase: query latency 10.6 s @100k (postings
  stored but unread at query time; ADR 0011).
- Suites: 365 unit + 71 e2e; eval gate beaten.

## [0.22.1] — 2026-07-21 — release-pipeline hygiene

- sdist no longer ships the archived old build / lockfile / CI plumbing (found
  in 0.22.0); CI asserts sdist cleanliness.
- Publish workflow gained a tag↔version guard + `twine check --strict` (no more
  silent no-op publishes); build-check job restored on PRs.

## [0.22.0] — 2026-07-21 — hybrid engine v2

Phase 3 (handoff 0003, ADRs 0006–0007):

- Bundled **7.93 MB static-embedding model** (potion-base-8M re-pack, int8,
  sha-pinned) inferred in pure stdlib; ships inside the wheel (6.98 MB).
- **RRF hybrid** (k=60) over BM25F candidates; `--lexical-only` preserves the
  v1 path byte-for-byte; eval harness (21 pairs) gates retrieval — gate passed
  as a tie, rank-level rescues recorded.
- Warm hybrid query 0.2 ms; wheel ≤ 15 MB asserted.

## [0.21.0] — 2026-07-21 — web, CDP, and the advanced tier

Phase 2 (handoff 0002, ADR 0005):

- Fenced **web ingestion**: stdlib HTML→Markdown, BFS crawl with robots.txt,
  depth/budget/domain caps, attachments, full `url`/`parent`/`depth` provenance.
- **CDP rendered pages** via a hand-rolled RFC 6455 WebSocket client driving the
  user's own headless Chrome (no bundled browser).
- **Advanced fidelity tier**: `fux ingest --advanced` re-converts one source
  with Docling / Tesseract OCR; upgrades survive re-ingest.
- Import-fence test: query/index can never touch network modules.

## [0.20.0] — 2026-07-21 — query CLI v1

Phase 1 (handoff 0001, ADRs 0001–0004):

- `fux setup` (wizard + flags + `-y`), two-tier `fux ingest` → OKF Markdown
  cache with provenance frontmatter, structure-aware heading chunker.
- **BM25F** retrieval (heading 3.0 / path 2.0 / body 1.0, weight-then-saturate);
  `fux ask` / `find` / `answer` (extractive, cited, never generative) with
  `--json` / `--explain`.
- Agent integration: AGENTS.md + tool pointers, `fux-query`/`fux-ingest`
  skills (open SKILL.md standard), Claude Code + Kiro hooks (fail-open).
- Deterministic by construction: byte-identical double-ingest; e2e suite with
  fixture corpus + goldens.

## [0.19.0] — 2026-07-20 — the rebuild begins

- From-scratch restart (old 0.18.x build archived under `archive/`).
- New skeleton: `src/` layout, hatchling, `fux-engine` name kept, CLI boundary +
  single flat `FuxError`, smoke tests; CLAUDE.md contract, compare-doc
  lifecycle, docs bundle.
