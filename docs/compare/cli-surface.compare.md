---
type: Compare Doc
title: CLI Surface (command naming)
description: Verb per intent — fux ask / find / answer — plus fux setup (interactive wizard + flags + -y).
status: accepted
timestamp: 2026-07-21T00:00:00Z
---

# CLI Surface (command naming) — Comparison

> **Proposed verdict:** **Three friendly verbs, one per intent** — `fux ask` (default,
> ranked passages), `fux find` (file locator), `fux answer` (extractive cited answer)
> — with `--json`/`--explain` available on all three for the agent path.
> **Status:** ✅ Accepted (Arpit, 2026-07-21) · **Confidence:** Medium-High
> Rationale in one line: a verb per intent reads like English and needs no flag
> memorization; flags remain for *modifiers*, not for switching intent.

## Context

Arpit asked for "a bit more friendly" than `fux query <q>` / `--files` / `--answer`.
The output formats are decided ([`query-output.compare.md`](query-output.compare.md));
this fixes only what the human (and agent) types.

## Options

### A — Three verbs *(proposed)*
```
fux ask    "why did we pick a composite index?"     # ranked passages (default intent)
fux find   "composite index decision"               # which files — locator
fux answer "why did we pick a composite index?"     # extractive, cited answer
```
- **Pros:** each command says what you get; discoverable via `fux --help`; no
  flag-vs-flag confusion; `ask`/`find`/`answer` are natural for an agent to choose
  between too.
- **Cons:** three top-level commands to document; intent split across verbs (minor).

### B — One verb + flags (the original)
```
fux query "<q>"            # passages
fux query "<q>" --files
fux query "<q>" --answer
```
- **Pros:** single entry point; smallest surface.
- **Cons:** flags switch *what you get*, which is the least discoverable pattern;
  `query` is jargon-y; exactly what Arpit flagged as unfriendly.

### C — Verbs *and* flag aliases
`fux ask` as the hub plus `fux ask --files` / `--answer` kept as aliases for B-style
callers.
- **Pros:** maximally forgiving.
- **Cons:** two ways to do everything — docs and tests double; violates "small
  engine" instincts. Not worth it at v1.

## Comparison matrix

| Criterion (weight) | A: Verbs | B: Flags | C: Both |
|--------------------|----------|----------|---------|
| Friendliness / reads like English (H) | **Best** | Weak | Best |
| Discoverability via --help (H) | High | Low | High |
| Agent ergonomics (M) | High (pick a verb) | Medium | High |
| Surface size / test burden (M) | Small | Smallest | Largest |
| **Fit** | **Verdict** | Rejected as unfriendly | Overkill |

## Modifiers (shared by all verbs)

`--json` (machine-readable, agent path) · `--explain` (why each result/sentence) ·
`--top N` · `--answer-max N` (answer only) · `-C/--context N` lines (passages only).

## `fux setup` — one setup command, interactive *and* flag-driven (accepted 2026-07-21)

Arpit's call: a single setup command that works both as an interactive wizard and
fully via flags — **named `fux setup`** (renamed from the initially proposed `fux
init`, Arpit 2026-07-21). This matches the researched CLI convention (npm init, gh
auth login, clig.dev): **interactive by default for first-time guidance, flags for
automation — an interactive command never *replaces* the non-interactive one.**

```bash
fux setup                     # interactive wizard: prompts for source folders per
                              # file type, cache location, web sources, agent files,
                              # skills, hooks — writes fux.toml + scaffolding
fux setup -y                  # accept all defaults, no prompts (npm init -y style)
fux setup --sources ~/notes,~/docs --pdf ~/papers \
          --agents --skills --hooks --no-web     # fully flag-driven, scriptable
```

Behavior contract: every question the wizard asks has a corresponding flag; flags
provided skip their prompts (partial-interactive works); `-y` + flags is fully
non-interactive for CI/scripts; re-running is idempotent (updates the fux-managed
blocks, never clobbers user edits). `fux setup --agents --skills --hooks` covers the
agent-integration scaffolding — one entry point for all setup.

References for this pattern: [npm init / -y](https://docs.npmjs.com/cli/v11/commands/npm-init/),
[gh auth login — flags replace prompts](https://github.com/cli/cli/issues/4506),
[UX patterns for CLI tools — interactive mode as guardrails, never a replacement](https://www.lucasfcosta.com/blog/ux-patterns-cli-tools)
(accessed 2026-07-21).

## References

- Internal: [`query-output.compare.md`](query-output.compare.md) — the three intents these verbs map onto.
- External: [Command Line Interface Guidelines (clig.dev)](https://clig.dev/) — "prefer subcommands for distinct actions; flags modify, they don't switch modes" (accessed 2026-07-20).
- External: [git — subcommand-per-intent design](https://git-scm.com/docs) — the convention users already know (accessed 2026-07-20).

## Additional things to look into

- Reserve `fux ingest` (already taken by ingest) and keep verb namespace small.
- Shell completion for the three verbs once the surface settles.
