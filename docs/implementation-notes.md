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

## Update — multi-language call edges, recall eval, richer examples

A second pass closed the remaining engine 🟡/⬜ items (the phase-7 decommission and
live-project benchmarks stay out of scope — they are operations on Anton/Wagner,
not engine code):

- **Cross-language call-graph parity** — `fux/astextract.py` now emits intra-file
  `calls` edges for JS/TS, Go, and Rust, not just Python. Function bodies are
  resolved by a string/comment-aware **brace matcher** (`_body_span`), call sites
  are matched against same-file declarations, and a shared `CALL_KEYWORDS` set
  (now reused by `graph._xref`) filters control-flow/builtin noise. Covered by
  `tests/test_astextract.py`.
- **Recall eval set** — `tests/test_recall_eval.py` adds a labelled paraphrase
  corpus so the phase-2 re-rank is validated, not just asserted: lexical recall@1
  is 1.0 on the set and the local re-rank is checked not to regress.
- **Verify examples beyond JSON** — `fux/vexamples.py` now executes examples whose
  `given` is an inline `key=value` / `key: value` pair string (with numeric /
  boolean / currency scalar coercion on values and `expect`), in addition to JSON
  objects. Unparseable prose still skips — the "never a false fail" guarantee
  holds. Covered by `tests/test_examples.py`.
- **Measured cost savings** — `fux savings ["query"]` (`fux/savings.py`) makes
  plan §12's ROI table auditable: it counts INDEX / rule-corpus / governed-code
  tokens from real file sizes (≈4 chars/token, applied to both sides) and prints a
  without-Fux vs with-Fux per-lookup comparison plus an aggregate over documented
  topics. Deterministic and `$0`. Covered by `tests/test_savings.py`.

## Update — quality, health, enforcement, agents, and the graph viewer

A developer/agent-experience pass (all `$0`, stdlib-only, tested):

- **`fux lint`** (`fux/lint.py`) — rule *quality* beside `check`'s *structure*:
  `no-why`, `no-code-refs`, `dangling-edge`, `no-provenance`, `stub-body`.
- **`fux stats`** (`fux/stats.py`) — a weighted health score (coverage 40 ·
  verify 30 · authoring 30 − blocking-drift penalty) + corpus/signal breakdown,
  composed from the existing commands.
- **`fux gate`** (`fux/gate.py`) — the out-of-session enforcement surface
  (rebuild → exit 2 on blocking `check`/`verify`); `--install` writes a git
  pre-commit hook. `gitutil.hooks_dir` resolves the hooks path.
- **Cross-file call edges** — `astextract.external_call_sites` attributes each
  call to its enclosing symbol (Python + brace languages); `graph._crossfile_calls`
  resolves callees against the global symbol index into symbol→symbol `calls`
  edges and suppresses the now-redundant file→symbol `references`.
- **`fux mcp`** (`fux/mcpserver.py`) — a hand-rolled MCP stdio server (newline
  JSON-RPC 2.0, **no `mcp` dependency**) exposing the read paths as tools.
- **Graph viewer** (`fux/assets/`) — node + edge-type filters, colour modes
  (type/community/layer/degree), focus/neighbour highlighting, directed arrows, a
  details panel, layout sliders, keyboard shortcuts, and markdown **agent export**
  of a node's neighbourhood or the visible sub-graph.
- **`distill` skill** (`skills/distill/`) — capture a session's durable decisions
  as `memory`/`adr` entries (human-confirmed, scoped); the plan §16 "Defer" item,
  now shipped.

## Update — roadmap §17 (retrieval, capture, governance, dashboard)

The plan §17 engine items, all opt-in and `$0` (defaults unchanged):

- **RRF hybrid recall** (`fux/hybrid.py`) — Reciprocal Rank Fusion (k=60) of BM25 ⊕
  local-semantic (`embed`, $0 trigram fallback) ⊕ graph proximity (BFS from lexical
  anchors). Behind `recall_hybrid` / `fux recall --hybrid`. `fux/bench.py` adds
  `recall@k`/MRR; the eval set (`tests/test_recall_eval.py`) reports lexical
  recall@1 = 1.0 and hybrid recall@3 = 1.0.
- **Opt-in capture** (`fux/capture.py`) — Stop-hook (`capture = true`) records which
  important files changed (governed vs uncovered) via `gitutil.changed_files`, with
  a secret-path filter + SHA-256 dedup, into `.fux/capture/`. Never authors a
  `memory` entry; `distill` consumes the queue. No LLM.
- **Memory governance** (`fux/governance.py`) — `type: memory` decays after
  `memory_ttl_days`; `check` emits `memory-stale`, `context` excludes it. Rules
  never decay.
- **Expanded MCP** (`fux/mcpserver.py`) — `fux_query`/`fux_trace`/draft-`fux_new`.
- **`fux serve`** (`fux/serve.py`) — `http.server` dashboard (stats + view links).
- **Sanitizer hardening** (`fux/astextract.sanitize_lines`) — a char state machine
  blanking strings/templates and `//` + multi-line `/* */` comments before brace
  matching, replacing the old per-line regex.

## Update — decommission-unblocking parity work (§17.13–17)

The 2026-06-04 readiness check found the decommission blocked by missing engine
capability (Fux couldn't *match* the stores it replaces), so retiring would lose
data. Built the tooling that makes "parity signed off" measurable, all `$0`:

- **`graph_globs`** (`fux/config.py`, `fux/graph.py`) — decoupled from
  `important_globs`; `fux build` graphs the broad set, `fux build --full` graphs
  every non-ignored file (`.fux/`/`.git/` skipped). Closes the 329-vs-1906 gap.
- **`fux import` / `import-memory`** (`fux/importer.py`) — ingest existing markdown
  as `narrative` entries and home-dir memory as `memory` entries (frontmatter
  stamped, bodies preserved, skip-existing).
- **Narrative rendering** (`fux/narrative.py`) — `NARRATIVE.md` on build, linked
  from `fux serve`.
- **`fux parity`** (`fux/parity.py`) — graph coverage vs `graphify-out/graph.json`,
  unmigrated `docs/` (minus STAY-listed conventions/guardrails), unimported memory;
  `READY`/`NOT READY` verdict, exit 1 until ready. The gate for §17.9.

Still future work: cross-**file** call edges for non-Python languages (today:
intra-file calls + heuristic cross-file references), block-comment / multiline
template-literal awareness in the brace matcher, and the phase-7 decommission
once parity is signed off.

## Update — beyond-roadmap SOTA & frontier (§17.18–25)

Pushed past the planned scope; all `$0`, deterministic, stdlib-only. Eight of ten
sub-areas shipped (106 tests):

- **Retrieval to SOTA** (§17.18) — the default scorer is now **true per-field BM25F**
  (`fux/recall.py` `_bm25f`: each field length-normalised before a single
  saturation), superseding the "BM25-lite" bag-of-fields. Opt-in **query expansion**
  (`recall_expand` / `--expand`) widens the query with glossary synonyms + 1-hop
  `related` neighbours. The eval (`tests/test_recall_eval.py`) grew to 24 queries with
  hard negatives + a `test_recall_regression_gate` (recall@1 0.875 / recall@3 1.0 /
  MRR 0.931). Supersedes the "BM25-lite" note in the Recall section below.
- **Graph centrality** (§17.19b) — deterministic **PageRank** (`fux/graphquery.py`
  `pagerank`/`chokepoints`) stored as `centrality` on every node and surfaced in a
  `GRAPH_REPORT.md` "Chokepoints" section.
- **Optional tree-sitter backend** (§17.19a) — the `[ast]` extra
  (`pip install fux-engine[ast]`) swaps the regex/brace heuristic for real ASTs on
  JS/TS/Go/Rust (`fux/astextract.py` `_treesitter`/`_ts_parser`, built on the stable
  `tree_sitter.Parser` + a grammar pack's `get_language`). Emits the **same node/edge
  schema** as the heuristic — only accuracy changes (e.g. Go structs now surface as
  `class` nodes). The default stays stdlib-only/$0; tree-sitter is never required.
  Reproducibility is kept honest by design: `graph.build` records `meta.extractor`
  (`backend_fingerprint()` — backend + grammar versions) and `fux check` raises a
  **non-blocking `extractor-drift`** finding when a committed graph was built with a
  different backend than the one installed locally. Richer import/type edges are
  intentionally **not** added to the stored substrate (reserved for the report layer)
  so the graph never diverges by more than the heuristic already does.
- **Verification hardening** (§17.20) — `fux verify --fuzz` boundary-perturbs numeric
  example inputs and flags unguarded **div-by-zero** (`fux/vexamples.py`
  `fuzz_examples`, only `ZeroDivisionError` is treated as a clean signal); an
  `overlap-unlinked` lint (`fux/lint.py` `_overlaps`) catches two unlinked rules over
  the same code span; opt-in `usage_tracking` (`fux/usage.py`) feeds **usage-weighted
  decay** in `fux/governance.py` (a memory served within the TTL window stays alive).
- **Proof-carrying rules / AST seals** (§17.22) — `fux/seal.py` fingerprints the
  normalized-AST *skeleton* of a rule's `code_refs` (names/literals folded); `fux seal`
  stamps a `seal:` field; `fux check` emits an advisory `unsealed` finding when the
  governed code changes structure. Whitespace/comment/rename edits don't break it.
- **Rule mining** (§17.23) — `fux mine` (`fux/mine.py`) surfaces magic numbers
  repeated across ≥N sites as draft `convention` candidates (never auto-authored).
- **Knowledge archaeology** (§17.24) — `fux why <id> --history` (`fux/explain.py`
  `render_history` over `gitutil.file_history`, `--follow`).
- **Optimal context packing** (§17.25) — a real 0/1 knapsack DP (`fux/pack.py`) gated
  on `context_budget_tokens` (default 0 ⇒ inject everything), wired into `fux/context.py`.

Deferred (need a non-`$0` or runtime surface): automated A/B value proof (21, needs
live agent runs), the self-densifying graph (26, needs MCP-runtime traversal logging),
and the federated mesh (27, **undecided**).
Also fixed a pre-existing `tomllib` duplicate-key failure in `tests/test_parity_import.py`.

## Decisions taken (the plan's "still open" items)

| Open question (plan §14) | Call made in v0.1.0 | Rationale |
|---|---|---|
| **Optional UserPromptSubmit recall** — v1 or later? | Implemented as `fux hook-recall`, **opt-in** via `fux init --recall` (not wired by default). | Ships the capability without forcing it on every project; the core 3 hooks prove out first, exactly the plan's caution. |
| **Generated `.fux/out/` tracking** — git-track or gitignore? | **Gitignored by default** (`fux init` writes `.fux/.gitignore`). Rebuilt by `fux build` ($0). | Cleaner diffs; build is free. A project that wants zero-rebuild reads can drop the ignore line and commit `out/`. |
| **Skills layer** — `plan` alone or `plan`+`adr`+`trace`? | All three shipped as skill docs; `plan` is the fleshed-out flagship, `adr`/`trace` are lighter. | Plan §16 recommends plan-first; the others are thin and substrate-aware enough to ship alongside without sprawl. |

## Scope of the AST graph backend (plan §7/§13.1)

The graph engine is Fux-owned and `$0`. v0.1.0 extracts symbols **and intra-file
call edges across languages**, though it remains a focused extractor, not a full
re-implementation of graphify's multi-language pipeline:

- **Python** — real symbol + call-edge extraction via the stdlib `ast` module
  (functions, classes, intra-file `calls`).
- **JS/TS, Go, Rust** — declaration nodes via regex **plus intra-file `calls`
  edges** via a brace-matched, string/comment-aware heuristic (`_body_span`). With
  the optional `[ast]` extra installed (plan §19a) these languages are extracted with
  **real tree-sitter ASTs** instead, at the same node/edge schema.
- **All languages** — file nodes, `governs` edges to rules via `code_refs`,
  heuristic cross-file `references` edges, rule↔rule `related`/typed edges,
  community detection, and the `query/path/explain` traversals.

Remaining gap vs graphify: cross-**file** call edges for the non-Python languages
(today: intra-file calls + heuristic cross-file references).

## Recall (plan §10.11, recall-engine.compare.md)

Phase 1 (default): BM25-lite over body + frontmatter-weighted fields
(`id`/`domain`/`aliases`/`keywords`/`related`/`type`). Phase-2 local embedding
re-rank is **implemented** and gated behind `recall_rerank = true` in config:
sentence-transformers when the `[embeddings]` extra is installed, else a `$0`
char-trigram cosine fallback. Default path stays `$0` and unchanged; the re-rank
is validated against a labelled paraphrase eval set (`tests/test_recall_eval.py`)
so it can be promoted with evidence.

## Verify (plan §10.1)

`fux verify` evaluates a rule's `check:` expression in a restricted namespace
(`abs`/`sum`/`min`/`max`/`len`/`round`/`all`/`any`/`math` + pure iteration
builtins, no `__builtins__`). Data comes from, in order: the rule's `verify_cmd:`
(a shell command printing JSON — this is the probes/just wiring),
`.fux/verify/<id>.json`, or `.fux/out/verify_context.json`. No data → **skip**
(never a false failure).

The `examples:` given→expect pairs are now **auto-executed** against `check:`.
`given` is accepted as a JSON object, an inline `key=value` / `key: value` pair
string, or an already-parsed mapping; values and `expect` are scalar-coerced
(numbers, booleans, comma/currency-stripped numerics). Prose that fits none of
these is skipped, so the "never a false fail" guarantee is preserved.

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
