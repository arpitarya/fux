---
type: Handoff Prompt
title: Claude Code prompt — Query CLI v1
description: Paste-ready prompt that executes handoff 0001 (explore → plan → implement → verify).
status: implemented
adrs: [../adr/0001-config-and-setup.md, ../adr/0002-ingest-cache-chunker.md, ../adr/0003-bm25f-index-query-surface.md, ../adr/0004-agent-integration.md]
timestamp: 2026-07-21T00:00:00Z
---

# Claude Code prompt — Query CLI v1

Paste everything below into Claude Code at the repo root.

---

Build **Query CLI v1** for the Fux engine, executing the committed spec exactly.

**Explore first (do not skip):**
1. Read `CLAUDE.md` fully — it is binding (constraints, docs law, worklog duty).
2. Read `docs/handoff/0001-query-cli-v1-handoff.md` — the spec you are executing:
   definition of done, scope in/out, layout, constraints, edge cases, tests.
3. Read `docs/model-handoff-interview.md` (succession context) and skim the verdict
   blocks of every doc in `docs/compare/` — decisions are closed; each records its
   reopen-trigger. Do not relitigate any of them.
4. Inspect the existing skeleton: `src/fux/` (cli.py, errors.py), `tests/`,
   `pyproject.toml`.

**Then plan:** produce a milestone plan in this order — M1 config + `fux setup`
(wizard + flags + `-y`, idempotent); M2 frontmatter parser (unit-tested first — it is
load-bearing for everything); M3 ingest inferred tier → OKF cache + manifest +
chunker; M4 BM25F index + `ask`/`find` (+ `--json`, `--explain`); M5 `answer`
(extractive + TextRank + citations); M6 `setup --agents --skills --hooks`; M7
`tests_e2e/` suite (fixture corpus + normalized-JSON goldens + determinism test).
Keep each milestone independently green: unit tests pass at every step.

**Implementation rules (hard):**
- Stdlib-only runtime. No numpy, no network, no LLM, no new runtime deps.
  `markitdown` is an *optional extra* touched only inside ingest converters.
- Deterministic + git-friendly: sorted walks, stable serialization, POSIX relative
  paths, UTF-8; two ingest runs on the same sources must produce byte-identical
  cache, manifest, and index.
- Cache files are OKF-conformant (frontmatter `type: Ingested Document` + provenance
  keys; per-dir `index.md`).
- Errors: raise `FuxError` internally; render only in `cli.py:main`; exit codes
  0/1/2/130. Hooks fail-open, trace under `FUX_DEBUG=1`.
- Match the handoff's module layout unless you find a strictly better structure —
  if you deviate, say why in the ADR.

**Verify (definition of done):**
- `uv run pytest -q tests` and `uv run pytest -q tests_e2e` both green.
- Manual smoke: `fux setup -y` → `fux ingest` → `fux ask "…"` → `fux answer "…"
  --explain --json` on the fixture corpus.
- The determinism e2e test passes (byte-identical double-ingest).
- Every edge case listed in the handoff has a test.

**Track as you go:** update `docs/implementation.md` (Phase 1 table) at every
milestone completion and keep its "Now working on" line current.

**Close out (required, per CLAUDE.md):**
- Write ADRs 0001–0004 in `docs/adr/` (link the compare docs for references).
- Update: `docs/fux-plan.md` status table, `README.md` (commands + install),
  `docs/DOC-REGISTRY.md` rows touched, `docs/worklog.md` (append an entry for this
  build), `docs/model-handoff-interview.md` state of play.
- Move `docs/handoff/0001-*` to `docs/archive/` with `status: implemented` + ADR
  links in frontmatter.
- Bump version to 0.20.0 in `src/fux/__init__.py`.

Work milestone by milestone. Show the plan before writing code.
