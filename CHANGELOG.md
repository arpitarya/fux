# Changelog

All notable changes to **fux-engine** (the rebuild line). Dates are ISO; versions
follow semver. The latest entry is mirrored in [README.md](README.md) § What's new.
Maintained on every version bump (registry-tracked).

## [0.25.0] — 2026-07-23 — trust & currency

Phase 6 (handoff 0006, ADRs 0013–0014). The acme-payments realistic corpus
measured Fux confidently serving **retired** and **fabricated** answers — two
honest, partial fixes, not two clean ones:

- **Supersession — annotated, never reordered.** `status: superseded` /
  `superseded_by: <doc-id>` frontmatter is parsed at index build, persisted in
  the substrate and `.fux/state/` (chains resolved to their terminal document,
  cycles detected and marked unresolved rather than looping), and surfaced in
  `find`/`ask --json` (`"superseded": true, "superseded_by": "<doc-id>"`) and
  human output — **ranking is unchanged; all four `--lexical-only` goldens
  stay byte-identical.** `answer` prefers the resolved successor's chunks when
  both are in the pool it retrieved for a query; when the successor is
  absent, it still answers and annotates the source as superseded. `fux why`
  surfaces the flag plus a query-level `answer` decline explanation with
  numbers. Measured recovery on acme's 9/12 planted inversions: only **5 of
  12** stale docs carry a machine-readable marker at all, only **3 of the 9**
  inversions do, and at the `answer` level the fix **fully corrects 1** and
  de-cites the retired doc in a 2nd — partial by design, not a full fix
  (`docs/conformance/2026-07-23-supersession-recovery/`).
- **`[answer] min_confidence`** — an absolute confidence floor, above the
  pre-existing empty-pool decline. Calibrated against all five eval gates
  (acme's 4 unanswerable + 55 answerable, the gibberish control, the 21-pair
  fixture gate, and the synthetic 1k/5k/10k baselines):
  **no single value clears both the unanswerable and answerable gates** — the
  score distributions interleave (decline-all-4 needs floor ≥0.25;
  zero-false-decline needs floor ≤0.087). **Shipped disabled (`0.0`)** per the
  compare doc's calibration rule — do not ship a default that declines a
  correct answer. The measured 0/4-decline defect is **not fixed** in this
  release; the knob and its evidence exist for a future cross-query-comparable
  signal (e.g. dense cosine) to use
  (`docs/conformance/2026-07-23-min-confidence-calibration/`).
- Sqlite backend `docs` table gained four columns (`superseded`,
  `superseded_by`, `superseded_by_resolved`, `superseded_unresolved`);
  `format_version` bumped 2→3 (an incompatible schema rebuilds on next
  `fux ingest`, per its existing recovery contract).
- Both source proposals graduated to `docs/archive/` with their ADRs.

Suites: 444 unit + 100 e2e (+1 gated skip).

## [0.24.0] — 2026-07-22 — debug & observability

Phase 5 (handoff 0005, ADR 0012). Fux was deterministic and cited, but not
*diagnosable* — this phase makes every stage inspectable without a debugger:

- **`[debug]` in `fux.toml`** — `level` (off/info/debug/trace), `categories`,
  `output` (stderr or a file), `timing`, `redact`, `max_bytes`. Precedence
  `--debug[=LEVEL]` > `FUX_DEBUG=<level|1>` > toml `level` > `off`.
- **`src/fux/debug.py`** — a hand-rolled, stdlib-only emitter (`dbg()`/
  `timer()`/`is_enabled()`). **Never touches stdout** (proven by a
  determinism test written before any instrumentation existed, and kept
  green through every milestone); redacts document content by default; no
  wall-clock unless `timing = true`; `off` costs nothing measurable.
  Instrumented at every pipeline stage: walk, convert, chunk, index, state,
  lock, query, lexical, dense, graph, answer, hooks, web.
- **`fux doctor`** — whole-install/corpus diagnosis across seven groups
  (environment, capabilities, config, corpus, consistency, agent surface,
  self-test); exit 0 healthy / 1 problems; `--json` for agents. Every failing
  check names what's wrong, why it matters, and the exact fix command — a
  `[sources]` entry matching zero files (the #1 silent misconfig) is now
  surfaced loudly instead of silently ingesting nothing.
- **`fux why "<query>" --doc <path>`** — explains why one document did or
  didn't rank, walking corpus-presence → chunks → lexical → dense → graph and
  ending in a single verdict sentence. Reads its dense/graph evidence from the
  same `kernel.retrieve()` a real query uses.
- **`fux-debug` skill** (`fux setup --skills` now writes three skills) — runs
  `doctor` → `ingest --check` → `why` → `--advanced` → `--debug=debug`, in
  that order, and tells the agent to report findings rather than guess. The
  existing `fux-query`/`fux-ingest` skills each gained a one-line escalation
  pointer to it.
- **New doc:** `docs/example/DEBUG.md` — worked failure → diagnosis → fix,
  for all five questions debug exists to answer.

Suites: 417 unit + 100 e2e (+1 gated skip).

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
  with the **same top-ranked result** as a full index; the tail order and scores
  are approximate, because the state plane is quantized (codes/signatures).
  Measured "top-1 stable, tail re-ranked" across the 1k/5k/10k and acme
  conformance runs (`docs/conformance/`); the earlier "same rankings *and scores*"
  wording was inaccurate.
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
