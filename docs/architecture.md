# Fux — Architecture

The engine is pure-Python, stdlib-only (zero third-party deps), dogfooding its own
`files ≤100 lines` rule. Each module is small and single-purpose.

## Global install layout (plan §4)

```
~/.claude/skills/fux/SKILL.md      /fux entry (+ fux-plan, fux-adr, fux-trace)
~/.claude/fux/engine/              symlink to this repo (the CLI)
~/.claude/fux/global/              cross-project best practices — its own git repo
~/.claude/fux/packs/*/             opt-in shareable domain packs
~/.claude/fux/hooks/*.sh           hook wrappers (fux binary, or python -m fux)
~/.claude/fux/schema.json          rule-frontmatter schema
```

## Per-project footprint (`fux init`)

```
.fux/rules/*.md        source rules/formulas/adr/… (one entry per file)
.fux/glossary/*.md     glossary terms
.fux/memory/shared/    committed memory; memory/personal/ is gitignored
.fux/config.toml       strictness, packs, important/ignore globs
.fux/verify/<id>.json  optional invariant verification data
.fux/out/              GENERATED — INDEX.md, rules.json, graph.{json,html}, DRIFT.md, ONBOARDING.md
.claude/settings.json  hooks wired (SessionStart, PostToolUse, Stop)
```

`.fux/out/` is gitignored by default (rebuilt by `fux build`, $0). A project can
track it for zero-rebuild reads — see [implementation-notes.md](implementation-notes.md).

## Module map (`fux/`)

| Layer | Module | Responsibility |
|---|---|---|
| **Substrate** | `frontmatter.py` | YAML-subset parse (split fm/body) |
| | `fmwrite.py` | serialize fm back (fix-mode writeback) |
| | `model.py` | `Rule` / `RuleSet`, types, title extraction |
| | `schema.py` | validate frontmatter against `schema.json` (no jsonschema) |
| **Resolution** | `paths.py` | global/packs/schema paths; `Footprint` |
| | `config.py` | `.fux/config.toml` (tomllib), strictness, defaults |
| | `loader.py` | load dirs; resolve project ⊕ packs ⊕ global by precedence |
| **Derived views** | `index.py` | INDEX.md + rules.json |
| | `astextract.py` | per-language symbol/edge extraction (the code-graph engine) |
| | `graph.py` | merge code nodes + knowledge nodes → graph dict |
| | `graphhtml.py` + `assets/` | self-contained interactive HTML |
| | `build.py` | orchestrate all derived views |
| **Maintenance** | `check.py` + `findings.py` | schema/dead-ref/staleness/conflict + DRIFT.md |
| | `fix.py` | mechanical $0 repairs |
| | `verify.py` | run invariant `check:` assertions |
| | `coverage.py` | documented-logic coverage |
| | `gitutil.py` | git staleness helpers |
| **Lookup** | `recall.py` | BM25-lite lexical retrieval |
| | `explain.py` | `why` + `refs` |
| | `touch.py` | changed file → affected rules (session-aware) |
| | `tour.py` | ONBOARDING.md |
| | `scaffold.py` | `fux new` from templates |
| **Adoption** | `initcmd.py` | scaffold footprint |
| | `settings.py` | wire hooks into `.claude/settings.json` (idempotent) |
| | `context.py` | SessionStart INDEX injection |
| | `hooks.py` | hook entrypoints (stdin event JSON → guidance) |
| **Surface** | `cli.py` + `clicmds.py` | argparse dispatch + human handlers |

## Data flow

```
author .fux/rules/*.md ──► loader.resolve ──► RuleSet
                                             ├─► index.render_{index,json}
                                             ├─► graph.build (⊕ astextract over code) ─► graphhtml
                                             ├─► check (schema/refs/git/conflict) ─► DRIFT.md
                                             └─► recall / why / refs / coverage / verify / tour
```

The graph merges two node families: **code** (`code-file`, `function`, `class`
from AST) and **knowledge** (`rule`, `formula`, … from frontmatter), joined by
`code_refs` (`governs` edges) and `related`/typed `edges` (rule↔rule). This is
how the structural code graph and the business-rules layer become one view
(plan §11).
