# Fux CLI reference

Every command is deterministic and `$0` — no LLM calls (plan §9). Run them from
anywhere inside a project that has a `.fux/` footprint (the engine walks up to
find it), except `fux init` which scaffolds one in the current directory.

| Command | What it does | Cost |
|---|---|---|
| `fux init [--recall]` | Scaffold `.fux/` footprint, wire the 3 core hooks into `.claude/settings.json`, drop a CLAUDE.md pointer. `--recall` also wires the optional UserPromptSubmit recall hook. | $0 |
| `fux build` | Regenerate `.fux/out/INDEX.md` + `rules.json` + `graph.json` + `graph.html` from source frontmatter. | $0 |
| `fux check [--fix]` | Validate schema, dead `code_refs`, git-staleness, and conflicts; write `DRIFT.md`. `--fix` applies mechanical repairs (drop dead refs, bump `updated`). Exit 2 under `strict` mode with blocking findings. | $0 |
| `fux context` | Emit the compact Tier-1 INDEX (global ⊕ packs ⊕ project) — the SessionStart injection. | $0 |
| `fux recall "Q" [--top N]` | BM25-lite lexical retrieval of the rules relevant to a query (frontmatter-weighted). | $0 |
| `fux why <id>` | Explain a rule: rationale + linked code + edges + invariant + body. | $0 |
| `fux refs <file>` | Reverse lookup — which rules govern this file. | $0 |
| `fux new <type> <id> [--domain D]` | Scaffold a schema-valid stub from a template into the right directory for its type. | $0 |
| `fux coverage` | % of "important" code files (config globs) with at least one governing rule; lists the uncovered. | $0 |
| `fux verify` | Run invariant `check:` assertions against verification data (`verify_cmd:` / `.fux/verify/<id>.json`). Skips when no data. | $0 |
| `fux tour` | Emit an ordered `ONBOARDING.md` reading path from the rules. | $0 |

### Internal hook entrypoints

Wired by `fux init`, not for direct use:

| Command | Hook event | Behaviour |
|---|---|---|
| `fux context` | SessionStart | Prints the INDEX to stdout (injected as context). |
| `fux hook-touch` | PostToolUse (Edit\|Write) | Reads the event JSON; if an edited code file is governed by a rule not edited this session, prints a reminder. Marks edited rule files so they are not nagged. |
| `fux hook-check` | Stop | Runs `check`; in `fix` mode applies mechanical repairs and reports the rest; in `strict` mode exits 2 on blocking findings. |
| `fux hook-recall` | UserPromptSubmit (opt-in) | Reads the prompt; injects the top recalled rules. |

### Skills (call the LLM, ride the current session)

| Command | What |
|---|---|
| `fux plan "<request>"` | Spec-driven: requirements → design → tasks, each a durable Fux entry. See [spec.guide.md](spec.guide.md). |
| `fux adr "<decision>"` | Capture an architecture decision as an `adr` entry. |
| `fux trace "<feature>"` | Walk the merged graph to explain how a feature spans modules ($0 traversal). |

### Environment overrides

| Var | Overrides |
|---|---|
| `CLAUDE_CONFIG_DIR` | `~/.claude` base (engine, global, packs, schema). |
| `FUX_GLOBAL` | Global rules dir (default `~/.claude/fux/global`). |
| `FUX_PACKS` | Packs dir (default `~/.claude/fux/packs`). |
| `FUX_SCHEMA` | `schema.json` path. |
| `FUX_PYTHON` | Interpreter the hook wrappers use when `fux` is not on PATH. |
