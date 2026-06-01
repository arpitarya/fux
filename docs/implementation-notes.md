# Implementation notes — engine v0.1.0

What shipped against [fux-plan.md](fux-plan.md), and where the implementation made
a concrete call on a plan-level "still open" question (§14).

## Decisions taken (the plan's "still open" items)

| Open question (plan §14) | Call made in v0.1.0 | Rationale |
|---|---|---|
| **Optional UserPromptSubmit recall** — v1 or later? | Implemented as `fux hook-recall`, **opt-in** via `fux init --recall` (not wired by default). | Ships the capability without forcing it on every project; the core 3 hooks prove out first, exactly the plan's caution. |
| **Generated `.fux/out/` tracking** — git-track or gitignore? | **Gitignored by default** (`fux init` writes `.fux/.gitignore`). Rebuilt by `fux build` ($0). | Cleaner diffs; build is free. A project that wants zero-rebuild reads can drop the ignore line and commit `out/`. |
| **Skills layer** — `plan` alone or `plan`+`adr`+`trace`? | All three shipped as skill docs; `plan` is the fleshed-out flagship, `adr`/`trace` are lighter. | Plan §16 recommends plan-first; the others are thin and substrate-aware enough to ship alongside without sprawl. |

## Scope of the AST graph backend (plan §7/§13.1)

The graph engine is Fux-owned and `$0`, but v0.1.0 is a **focused** extractor, not
a full re-implementation of graphify's multi-language pipeline:

- **Python** — real symbol + call-edge extraction via the stdlib `ast` module
  (functions, classes, intra-file `calls`).
- **JS/TS, Go, Rust** — declaration-level nodes via lightweight regexes
  (functions/classes), no call edges yet.
- **All languages** — file nodes, plus `governs` edges to rules via `code_refs`,
  and rule↔rule `related`/typed edges.

This is enough to merge code and knowledge nodes into one navigable
`graph.html` (the plan's core claim). Cross-language call-graph parity with
graphify, community detection, and the `query/path/explain` traversals are future
work (plan §13.7 "absorb & migrate").

## Recall (plan §10.11, recall-engine.compare.md)

Phase 1 only: BM25-lite over body + frontmatter-weighted fields
(`id`/`domain`/`aliases`/`keywords`/`related`/`type`). Phase-2 local embedding
re-rank is gated behind `recall_rerank = true` in config and the `[embeddings]`
extra — **not** implemented yet, but the config seam and dependency extra exist so
turning it on later changes no default behaviour. Default path stays `$0`.

## Verify (plan §10.1)

`fux verify` evaluates a rule's `check:` expression in a restricted namespace
(`abs`/`sum`/`min`/`max`/`len`/`round`/`all`/`any`/`math`, no builtins). Data
comes from, in order: the rule's `verify_cmd:` (a shell command printing JSON —
this is the probes/just wiring), `.fux/verify/<id>.json`, or
`.fux/out/verify_context.json`. No data → **skip** (never a false failure). The
`examples:` given→expect pairs are carried and shown but not auto-executed in
v0.1.0 (they document the invariant `check` covers).

## Strictness / auto-fix split (plan §8)

- **Mechanical fixes** (deterministic, in `fix.py`): drop dead `code_refs`, bump
  `updated` on stale rules, regenerate INDEX. Applied in `fix` mode and via
  `fux check --fix`.
- **Semantic drift** (prose no longer matches code): **not** auto-edited. The plan
  calls for emitting a scoped edit prompt to Claude in-session; v0.1.0 surfaces the
  stale finding with the changed path so the `/fux` skill / Stop reminder hands it
  to Claude. Full diff-in-the-prompt is a small follow-up.

## Dependencies

Zero third-party runtime dependencies (stdlib only) — including a hand-rolled
frontmatter parser and schema validator, to honour the "$0, dependency-free"
mandate (plan §3) and keep the tool portable. `tomllib` requires Python ≥3.11.
