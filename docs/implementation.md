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

> *(building agent: keep this one line current)* — Phase 1 complete (v0.20.0).
> Next: Phase 2 (handoff 0002, web/CDP/advanced ingest).

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
| M1 HTML→Markdown converter (stdlib, goldens-first) | ⬜ | — | |
| M2 urllib fetcher + crawl frontier + robots + `--web` e2e | ⬜ | — | |
| M3 RFC 6455 WebSocket client + CDP capture | ⬜ | — | |
| M4 advanced tier (Docling/Tesseract, fidelity transitions) | ⬜ | — | |
| M5 e2e additions + docs | ⬜ | — | |
| Close-out: ADR 0005, docs law, archive pair, bump | ⬜ | — | |

## Phase 3 — Hybrid engine v2 (handoff 0003) → v0.22.0

| Milestone | Status | Tests | Notes |
|-----------|--------|-------|-------|
| M1 eval harness + lexical baseline recorded | ⬜ | — | |
| M2 distillation pipeline (`tools/distill/`, ≤10 MB asserted) | ⬜ | — | |
| M3 stdlib inference (`fux.embed`, int8) | ⬜ | — | |
| M4 chunk-vector cache (manifest-invalidated) | ⬜ | — | |
| M5 RRF fusion + `--lexical-only` + explain | ⬜ | — | |
| M6 eval gate: hybrid ≥ lexical (numbers → ADR) | ⬜ | — | |
| M7 packaging (bundle in wheel, lazy load, size checks) | ⬜ | — | |
| Close-out: ADRs 0006–0007, docs law, archive pair, bump | ⬜ | — | |

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
