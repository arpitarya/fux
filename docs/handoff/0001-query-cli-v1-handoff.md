---
type: Handoff
title: Query CLI v1 — setup, ingest (inferred), BM25F, ask/find/answer
description: Self-contained build spec for the first shippable Fux deliverable, dogfoodable in Anton.
status: ready
timestamp: 2026-07-21T00:00:00Z
---

# Handoff 0001 — Query CLI v1

## Context (read first)

Fux's first deliverable is a CLI answering natural-language questions over documents
in configured folders. **Every design decision is closed** — see
[`../compare/`](../compare/) (engine, output, ingest, packaged model, CLI surface,
agent integration; each records its verdict and reopen-trigger) and CLAUDE.md (the
binding constraints). Do not relitigate decisions here; build them.

**The corpus is a long-term asset, not a disposable index** (Arpit, 2026-07-21): the
ingest cache is designed to be committed to git and maintained for years, ultimately
feeding product development (specs, decisions, agent-driven builds). Deterministic,
diff-friendly cache output is therefore a *requirement*, not a nicety.

**Pre-build debate (gate passed).** Top pre-mortem risks and their mitigations, baked
into scope below: (1) *scope drown* — web/CDP/OCR/advanced-tier are v1.1, not v1;
(2) *chunker quality on messy markdown* — golden-file tests on real-world fixtures,
code-fence/table atomicity asserted; (3) *golden brittleness* — goldens compare
normalized JSON (scores rounded to 3 dp), not raw text; (4) *hand-rolled frontmatter
parser correctness* — dedicated unit suite incl. edge cases + round-trip property
tests; (5) *cross-platform paths/encoding* — POSIX-style relative paths in all
frontmatter/manifest output; UTF-8 everywhere, errors="replace" on read.

## Definition of done

A user (Arpit, in Anton) can:

1. `uv run fux setup` → interactive wizard (or `-y` / flags) → writes `fux.toml`.
2. `uv run fux ingest` → walks configured local sources, converts to the OKF cache
   (`.fux/cache/`) with provenance frontmatter + manifest + per-dir `index.md`.
3. `uv run fux ask "why did we choose X?"` → ranked passages with `file:line` +
   scores, from BM25F over structure-aware chunks.
4. `uv run fux find "topic"` → ranked files. `uv run fux answer "…"` → extractive,
   cited answer. Both support `--json` and `--explain`.
5. `fux setup --agents --skills --hooks` → AGENTS.md + pointer files + SKILL.md
   skills + Claude Code/Kiro hooks, idempotent.
6. Both test suites pass: `uv run pytest -q tests` and `uv run pytest -q tests_e2e`.
7. Docs updated per CLAUDE.md (plan, README, registry, worklog, ADRs 0001–0004).

## In scope (v1)

- `fux.toml` config: `[sources]` per-type local dirs, `[ingest]`, `[engine.bm25f]`
  (weights heading 3.0/path 2.0/body 1.0, k1=1.2, b=0.75), `[answer]` (max
  sentences). Parse with `tomllib`; validate with clear FuxError messages.
- **Ingest, inferred tier, local files only:** md/txt native; code fenced with
  language tag; JSON flattened (stdlib) + fenced raw (cap via `max_kb`); YAML as
  fenced text; images → metadata stub (filename, dims via stdlib `struct` parsing of
  PNG/JPEG headers, EXIF only if trivially readable). Office/PDF via `markitdown`
  **extra** if installed, else skipped with a clear notice (`fux ingest --list-skipped`).
- **Cache = OKF bundle:** frontmatter `type: Ingested Document` + title/description/
  timestamp + provenance keys (source, source_sha256, origin, fidelity, converter,
  converted_at, fux_version); per-directory `index.md`; deterministic ordering
  (sorted walks, stable serialization) for clean git diffs.
- **Manifest** `.fux/manifest.jsonl` (sorted, one canonical JSON line per file) +
  `fux ingest --check` (sha drift) + `--list-inferred`.
- **Chunker:** heading-based, heading-path context, 256–512 token target (token ≈
  whitespace word for v1 — record this approximation in the ADR), ~10–15 % overlap on
  oversize paragraph splits, code fences/tables atomic, chunk → source `file:line`
  span map.
- **BM25F index:** built from cache at ingest time (`.fux/index/` — versioned format,
  stdlib pickle-free: JSON or simple binary w/ `struct`), weighted-tf-then-saturate
  (correct BM25F), incremental rebuild on changed files only.
- **`fux ask` / `find` / `answer`:** per the accepted CLI surface; `answer` =
  extractive (sentence split → score = BM25F passage score × question-term overlap ×
  TextRank centrality → top `answer_max` sentences, ordered, cited). `--explain`
  shows field hits + per-factor contributions. `--json` for all.
- **Agent files:** `fux setup --agents|--skills|--hooks` generating AGENTS.md
  (fux-managed block), CLAUDE.md/copilot-instructions/Kiro-steering pointers, one
  SKILL.md pair (`fux-query`, `fux-ingest`), Claude Code `UserPromptSubmit` +
  Stop-hook (doc-registry prompt), Kiro hooks. All fail-open.
- **Frontmatter parser:** hand-rolled, stdlib, subset-YAML (scalars, strings, lists,
  ISO dates); shared by ingest (write) and any consumer (read); round-trips
  preserving unknown keys (OKF conformance).
- **Both test suites** (see Tests below) and ADRs 0001–0004.

## Out of scope (v1.1+ / v2 — do not build)

Web ingestion (urllib crawl, attachments), CDP rendering, advanced tier (Docling/
OCR), embeddings + RRF (v2), `fux diff`/`log` (proposal), MCP (needs ADR), any LLM
anything (never on this path).

## Current state & key files

Package skeleton exists: `src/fux/__init__.py` (0.19.0), `cli.py` (argparse boundary,
`--version` only), `errors.py` (FuxError). Tests: `tests/test_smoke.py` (4 pass).
Suggested layout (follow, adjust judiciously):

```
src/fux/
  config.py         fux.toml load/validate → Config dataclass
  frontmatter.py    hand-rolled parser/serializer (subset YAML)
  ingest/__init__.py  public API: ingest_paths, check_drift, list_inferred
  ingest/walk.py      source discovery per config
  ingest/convert.py   per-type converters (md/txt/code/json/yaml/image stub/office-extra)
  ingest/chunk.py     heading-based chunker + span map
  ingest/manifest.py  manifest read/write/check
  index/bm25f.py      index build + scoring (+ incremental update)
  index/store.py      index (de)serialization
  query/api.py        ask/find/answer over the index
  query/answer.py     sentence split + extractive selection (TextRank)
  query/explain.py    explanation assembly
  agents/generate.py  AGENTS.md/pointers/skills/hooks templates + idempotent writer
  setup.py            wizard + flags (every prompt has a flag; -y)
  cli.py              wire subcommands; errors only rendered here
```

## Hard constraints (from CLAUDE.md — violations are build failures)

Stdlib-only runtime (converters/extras optional, never on the query path); no
numpy; no network anywhere in v1; deterministic everything (same corpus → same
index → same answer, byte-stable cache output); single FuxError; exit codes
0/1/2/130; Python ≥ 3.11; hooks fail-open, never fail-silent (trace under
`FUX_DEBUG=1`).

## Edge cases (tests must cover)

Empty corpus (helpful message, exit 0); no `fux.toml` (point to `fux setup`, exit 1);
query with zero hits (honest "no confident answer", suggest `--files`/re-ingest);
duplicate filenames across sources; markdown without headings (fallback: whole-file
chunking by paragraphs); huge file (chunk cap + warning); binary file with `.md`
extension (sniff, skip, notice); unicode content/paths; frontmatter edge cases
(no closing `---`, empty block, unknown keys preserved); stale cache (source changed
→ `--check` flags, `ask` warns); re-running `setup` (idempotent, preserves user
edits outside managed blocks); source file deleted after ingest (manifest orphan →
reported).

## Tests

- `tests/` (unit): frontmatter round-trip + fuzz-ish edge cases; chunker (atomicity,
  spans, sizes); BM25F math against hand-computed values on a toy corpus; extractive
  answer selection; config validation; manifest drift logic; agent-file idempotency.
- `tests_e2e/` (sibling suite, per CLAUDE.md): fixture corpus in `tests_e2e/corpus/`
  (~12 small real files: md w/ nested headings, txt, py, json, yaml, png, plus a
  docx+pdf exercised only when the extra is present — mark `skipif`); golden files
  in `tests_e2e/goldens/` as normalized JSON (paths POSIX, scores rounded 3 dp);
  flows: `setup -y` → `ingest` → `ask/find/answer` (+ `--json --explain`) via
  `subprocess`; determinism test (two runs → byte-identical cache + identical
  outputs); `--check` drift flow; agent-file generation.

## Open questions (answer during build, record in ADRs)

1. Index format: JSON vs `struct`-packed binary — pick by measured load time on a
   ~5k-chunk corpus; document.
2. Token approximation (whitespace) vs simple subword heuristic — validate chunk
   sizes look sane on the fixture corpus; note in ADR 0002.
3. `index.md` generation: per-directory always, or only above N files? (default:
   always; cheap.)
4. Where hooks live for Cowork specifically — mirror Claude Code settings if
   available; otherwise document limitation.

## ADRs to write on completion (one per feature)

0001 config + setup wizard · 0002 ingest/cache/OKF/chunker · 0003 BM25F index +
query surface · 0004 agent integration files/skills/hooks. Each with references
(the compare docs already hold them — link, don't duplicate). Then move this handoff
+ prompt to `docs/archive/` with `status: implemented`.
