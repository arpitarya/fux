# Implementation notes — engine v0.1.0

What shipped against [fux-plan.md](fux-plan.md), and where the implementation made
a concrete call on a plan-level "still open" question (§14).

## Update — gaps closed after the first cut

The following partial items from the first cut are now implemented:

- **Graph traversals** — `fux query` / `path` / `explain` / `report`, plus
  deterministic **community detection** (label propagation), a `GRAPH_REPORT.md`
  (god nodes + communities), cross-file/cross-language **`references`** edges, and
  a colour-by-community toggle in `graph.html`.
- **Recall phase-2** — `recall_rerank = true` enables a local re-rank:
  sentence-transformers if the `[embeddings]` extra is installed, otherwise a
  **$0 char-trigram cosine** fallback (still local, no API). Default path
  unchanged.
- **`verify` examples** — examples whose `given` is JSON are executed against the
  rule's `check:`; NL examples are skipped (never a false fail).
- **Plan-drift** — `fux check` emits a distinct `plan-drift` finding for a
  `task`/`spec` that is not `done` while its `code_refs` changed.
- **Semantic-drift scoped prompt** — in `fix` mode the Stop hook now emits the
  tightly-scoped edit prompt **with the actual `git diff`** of the changed
  `code_refs` before applying mechanical fixes (plan §8).

Also fixed: glob matching now honours recursive `**` (`fux/globs.py`) — `fnmatch`
treated `a/**/*.py` as non-recursive and missed files directly under `a/`, which
made `coverage` under-count. `install.sh` now installs **editable** (`pip -e`) so
repo edits live-reflect in the `fux` binary. `verify`'s safe namespace gained the
pure iteration builtins (`zip`, `range`, `enumerate`, …).

## Rollout status (plan §13)

- **Phases 1–3** (engine, hooks, global seed) — done; installed to `~/.claude/fux`,
  `/fux`+`fux-plan`/`-adr`/`-trace` skills registered.
- **Phase 4 — Anton pilot** — done: 4 rules grounded in `aggregator.py`
  (`inr-normalization`, `portfolio-valuation`, `day-pnl`, `holdings-sum-equals-total`),
  scoped to the brokers domain. `fux build/check/coverage/why/refs/recall/query` all
  exercised on real code.
- **Phase 5 — verification** — done: the `holdings-sum-equals-total` invariant is
  wired to `probes/fux_totals_probe.py` and verifies green; `just fux-check` recipe
  added to Anton.
- **Phase 6 — Wagner** — done: `fux init` in Wagner, one real rule
  (`api-key-hashing`), global best-practices inherited — portability confirmed.
- **Phase 7 — absorb & migrate** — *additive only*: Anton's cross-session memory
  imported as `type: memory` (`scope: shared`) and an `anton-overview` `type:
  narrative` entry authored. **Decommission deferred**: `graphify-out/`, the
  home-dir `memory/`, and `docs/` are left in place until parity is verified and
  explicitly retired.

Still future work: full multi-language *call-graph* parity with graphify (we have
declaration nodes + heuristic cross-file references, Python call edges), and the
phase-7 decommission once parity is signed off.

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
