---
type: ADR
title: ADR-0004 — agent integration: AGENTS.md + pointers, one SKILL.md pair, fail-open hooks
description: One contract rendered into every agent surface; skills follow the open Agent Skills standard; hooks enforce injection where hosts support it.
timestamp: 2026-07-21T00:00:00Z
---

# ADR-0004: agent integration files, skills, hooks

- **Status:** accepted
- **Date:** 2026-07-21
- **Feature:** M6 of handoff 0001 — `fux setup --agents --skills --hooks`

## Context

The primary caller of the query CLI is an AI agent. The agent-integration
compare doc decided: instruction files *and* hooks, generated from one source;
AGENTS.md canonical; MCP deferred behind an ADR; and (the research's twist)
**one skill file per skill** on the open Agent Skills standard instead of the
old build's per-platform skillgen.

## Decision

- **`fux setup --agents`** writes the contract into AGENTS.md and thin pointers
  into CLAUDE.md, `.github/copilot-instructions.md`, `.kiro/steering/fux.md`.
  All live inside `<!-- fux:managed:start/end -->` markers: user content outside
  the block is never touched; regeneration replaces only the block; re-runs are
  byte-idempotent (`created`/`updated`/`unchanged` reported per file).
- **`--skills`** ships `fux-query` + `fux-ingest` as `.claude/skills/<name>/
  SKILL.md` (frontmatter name/description + workflow) — one file each, readable
  by every Agent-Skills consumer.
- **`--hooks`** merges (never clobbers) `.claude/settings.json`: a
  `UserPromptSubmit` hook injects top `fux ask` passages as additional context,
  and a `Stop` hook nudges about `docs/DOC-REGISTRY.md` triggers. Both route
  through `fux hook <event>` — a boundary like `cli.main`, but **fail-open**:
  any exception exits 0 (the host session is never broken) while tracing under
  `FUX_DEBUG=1` (never fail-*silent*). A Kiro hook file covers Kiro; Cowork has
  no hook surface today — the generated instruction files are its path
  (handoff open question 4: documented limitation).
- The v1 contract says "advanced re-ingest arrives in v1.1" rather than
  advertising a flag that doesn't exist yet; phase 2 updates the text.

## Alternatives considered

- Instruction files only — the floor: no enforcement; agents forget.
- Hooks only — gappy: most surfaces have no hook API.
- MCP server — real ceiling, deliberately deferred (needs its own ADR +
  sign-off per CLAUDE.md scope rules).
- Per-platform skill generation (old build) — obsoleted by the open standard.

## Consequences

Easier: every agent surface gets the same contract from one generator; hook
failures can never hurt a session. Harder: enforcement is only as strong as the
host's hook support; injection quality depends on index freshness (mitigated by
the staleness warning and the ingest skill).

## References (required)

- Agent-integration compare doc (verdict + skills research):
  [../compare/agent-integration.compare.md](../compare/agent-integration.compare.md)
- AGENTS.md — the open agent-instructions standard: https://agents.md
- Agent Skills / SKILL.md open standard: https://code.claude.com/docs/en/skills
- Claude Code hooks reference (UserPromptSubmit/Stop, hookSpecificOutput):
  https://code.claude.com/docs/en/hooks
