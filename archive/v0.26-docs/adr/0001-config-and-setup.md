---
type: ADR
title: ADR-0001 — fux.toml config + single `fux setup` command
description: One TOML config mapping file types to source dirs; one setup command that is both wizard and flag-driven.
timestamp: 2026-07-21T00:00:00Z
---

# ADR-0001: `fux.toml` config + the `fux setup` wizard

- **Status:** accepted
- **Date:** 2026-07-21
- **Feature:** M1 of handoff 0001 — configuration + setup

## Context

The query CLI needs per-project configuration: which folders hold which file
types, ingest limits, BM25F weights, answer length. The CLI-surface compare doc
fixed the command (`fux setup`, renamed from `fux init` by Arpit) and the
convention: interactive wizard by default, a flag for every prompt, `-y` for
defaults, idempotent re-runs.

## Decision

- **`fux.toml`**, parsed with stdlib `tomllib` (the Python ≥ 3.11 floor exists
  partly for this): `[sources]` maps the four types (docs/code/data/images) to
  directory lists; `[ingest]` (`max_kb`, `exclude`); `[engine.bm25f]` (heading
  3.0 / path 2.0 / body 1.0, k1=1.2, b=0.75); `[answer]` (`max_sentences`).
- Validation raises the single `FuxError` with the offending key path; unknown
  keys/tables are ignored (permissive, OKF-style: newer configs open in older
  engines).
- `find_root()` walks up from cwd like git, so `fux ask` works from subdirs.
- `fux setup` merges into the existing file rather than clobbering it: managed
  keys are updated from answers/flags, user-edited values and unknown sections
  survive, and the writer is deterministic (identical inputs → identical bytes).
  A hand-rolled TOML writer (stdlib has none) covers the subset we emit.
- Non-interactive stdin (EOF) degrades to `-y` behaviour, so CI never hangs.

## Alternatives considered

- `pyproject.toml` `[tool.fux]` section — rejected: Fux targets any folder of
  documents, not just Python projects (Anton's corpus is not a Python package).
- Separate `fux init` + `fux config` commands — rejected in the CLI-surface
  compare: one verb, both modes.
- JSON/YAML config — rejected: JSON has no comments; YAML would need the
  hand-rolled parser to grow far beyond frontmatter subset scope.

## Consequences

Easier: one file to read for any agent; re-running setup is always safe.
Harder: the TOML writer only serializes the subset we emit (scalars, lists,
tables) — exotic user TOML (dotted keys, arrays of tables) would be rewritten
into canonical form or rejected; acceptable for a config this small.

## References (required)

- CLI-surface compare doc (verdict + wizard research):
  [../compare/cli-surface.compare.md](../compare/cli-surface.compare.md)
- Command Line Interface Guidelines — prompts must have flag equivalents:
  https://clig.dev/#interactivity
