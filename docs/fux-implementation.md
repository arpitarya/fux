# Fux — Implementation Status

> Engine **v0.4.0** — the constitutional-app engine. A portable, Claude-aware knowledge engine: one frontmatter
> substrate → derived index, graph, and memory views, with `$0` deterministic
> maintenance. This file tracks **what has shipped** and **what remains**, mapped
> to the design of record in [docs/fux-plan.md](docs/fux-plan.md).

**Legend:** ✅ done · 🟡 partial · ⬜ not started

---

## 1. Snapshot

| Area | Status | Notes |
|---|---|---|
| Core CLI surface (plan §9) | ✅ | 27 commands wired in [fux/cli.py](fux/cli.py) (incl. `seal`, `mine`) |
| Hooks (3 core + 2 optional) | ✅ | SessionStart, PostToolUse, Stop + opt-in UserPromptSubmit & capture |
| Rule schema + frontmatter parser | ✅ | Hand-rolled, stdlib-only ([fux/frontmatter.py](fux/frontmatter.py), [schema.json](schema.json)) |
| Layered resolution (global ⊕ packs ⊕ project) | ✅ | Precedence + conflict detection |
| Graph engine (AST extraction) | ✅ | Python via `ast`; JS/TS/Go/Rust intra- **and cross-file** `calls`; block-comment-aware sanitizer |
| Recall | ✅ | BM25-lite default; opt-in local re-rank **+ RRF hybrid** (lexical⊕semantic⊕graph) |
| Memory governance + capture | ✅ | TTL decay ([fux/governance.py](fux/governance.py)); opt-in capture queue ([fux/capture.py](fux/capture.py)) |
| Verify | ✅ | `check:` invariants + examples (JSON, inline `key=value`, scalar coercion) |
| Quality & health (`lint`/`stats`) | ✅ | Rule-quality lint + weighted health score ([fux/lint.py](fux/lint.py), [fux/stats.py](fux/stats.py)) |
| Enforcement (`gate`) | ✅ | CI / git pre-commit; **tier-aware** exit 2 on blocking ([fux/gate.py](fux/gate.py)) |
| Constitution layer (tiers, integrity, provenance, debate, split, critic) | ✅ | Tiers + `--baseline` + tamper/lock/`ratify` (incl. un-ratified/promoted-tier block) + provenance drift + `/fux debate` + split router + critic loop & report-first coverage gate (Phases 0–5 + 3b, v0.4.0); only the runtime critic is deferred ([fux/constitution.py](fux/constitution.py), [fux/provenance.py](fux/provenance.py)) |
| Agent integration (`mcp`) | ✅ | Stdlib MCP stdio server ([fux/mcpserver.py](fux/mcpserver.py)) |
| Graph UI | ✅ | Filters, focus, details, arrows, agent export ([fux/assets/](fux/assets/)) |
| Skills (`plan`/`adr`/`trace`/`savings`/`distill`) | ✅ | `plan` flagship; `distill` closes the memory loop |
| Decommission tooling (graph coverage, import, parity) | ✅ | `build --full`, `import`/`import-memory`, `fux parity` gate — see §2.20 |
| Decommission old stores in Anton | ⬜ | Tooling shipped; run it against Anton then retire when `fux parity` is READY ([plan §17.9](fux-plan.md)) |

Zero third-party runtime dependencies (stdlib only); requires Python ≥ 3.11.

---

## 2. What has been implemented

### 2.1 CLI surface — ✅ (plan §9)

All commands dispatch through [fux/cli.py](fux/cli.py); full reference in
[docs/cli.md](docs/cli.md).

| Command | Status | Module |
|---|---|---|
| `fux init [--recall]` | ✅ | [fux/clicmds.py](fux/clicmds.py), [fux/initcmd.py](fux/initcmd.py), [fux/scaffold.py](fux/scaffold.py) |
| `fux build [--full]` | ✅ | [fux/build.py](fux/build.py), [fux/graph.py](fux/graph.py) |
| `fux check [--fix] [--baseline-write FILE]` | ✅ | [fux/check.py](fux/check.py), [fux/fix.py](fux/fix.py), [fux/baseline.py](fux/baseline.py) |
| `fux context` | ✅ | [fux/context.py](fux/context.py) |
| `fux recall "Q" [--top N] [--hybrid] [--expand]` | ✅ | [fux/recall.py](fux/recall.py), [fux/hybrid.py](fux/hybrid.py) |
| `fux why <id> [--history]` | ✅ | [fux/cliquery.py](fux/cliquery.py), [fux/explain.py](fux/explain.py) |
| `fux seal [ids] [--all]` | ✅ | [fux/cliquery.py](fux/cliquery.py), [fux/seal.py](fux/seal.py) |
| `fux ratify <id> [--by NAME] [--date ISO] [--debate FILE]` | ✅ | [fux/cliconstitution.py](fux/cliconstitution.py), [fux/constitution.py](fux/constitution.py) |
| `fux critic "<change>"` | ✅ | [fux/cliconstitution.py](fux/cliconstitution.py), [fux/criticloop.py](fux/criticloop.py) |
| `fux mine [--min-sites N]` | ✅ | [fux/cliquery.py](fux/cliquery.py), [fux/mine.py](fux/mine.py) |
| `fux refs <file>` | ✅ | [fux/cliquery.py](fux/cliquery.py) |
| `fux new <type> <id> [--domain D]` | ✅ | [fux/cliquery.py](fux/cliquery.py) |
| `fux coverage` | ✅ | [fux/coverage.py](fux/coverage.py) |
| `fux verify [--fuzz]` | ✅ | [fux/verify.py](fux/verify.py), [fux/vexamples.py](fux/vexamples.py) |
| `fux savings ["Q"] [--reset]` | ✅ | [fux/savings.py](fux/savings.py), [fux/costledger.py](fux/costledger.py) |
| `fux lint [--strict]` | ✅ | [fux/lint.py](fux/lint.py) |
| `fux stats` | ✅ | [fux/stats.py](fux/stats.py) |
| `fux gate [--install] [--strict-lint] [--baseline FILE]` | ✅ | [fux/gate.py](fux/gate.py), [fux/baseline.py](fux/baseline.py) |
| `fux mcp` | ✅ | [fux/mcpserver.py](fux/mcpserver.py) |
| `fux capture [--list] [--clear]` | ✅ | [fux/capture.py](fux/capture.py) |
| `fux serve [--port N]` | ✅ | [fux/serve.py](fux/serve.py) |
| `fux import <path…>` | ✅ | [fux/importer.py](fux/importer.py) |
| `fux import-memory [--scope]` | ✅ | [fux/importer.py](fux/importer.py) |
| `fux parity` | ✅ | [fux/parity.py](fux/parity.py) |
| `fux tour` | ✅ | [fux/tour.py](fux/tour.py) |
| `fux query "Q" [--depth N]` | ✅ | [fux/cligraph.py](fux/cligraph.py), [fux/graphquery.py](fux/graphquery.py) |
| `fux path <a> <b>` | ✅ | [fux/cligraph.py](fux/cligraph.py) |
| `fux explain <term>` | ✅ | [fux/explain.py](fux/explain.py) |
| `fux report` | ✅ | [fux/report.py](fux/report.py) |

### 2.2 Hooks — ✅ (plan §8)

| Hook event | Entrypoint | Status |
|---|---|---|
| SessionStart → inject INDEX | `fux context` | ✅ |
| PostToolUse (Edit\|Write) → drift reminder | `fux hook-touch` ([fux/touch.py](fux/touch.py)) | ✅ |
| Stop → validate before turn ends | `fux hook-check` | ✅ |
| UserPromptSubmit → recall (opt-in) | `fux hook-recall`, wired via `fux init --recall` | ✅ |

Hook shells live in [hooks/](hooks/); I/O contract in [fux/hookio.py](fux/hookio.py),
[fux/hooks.py](fux/hooks.py). Strictness modes `off`/`warn`/`fix`/`strict`
(default `fix`) implemented in [fux/config.py](fux/config.py) + check/fix path.

### 2.3 Schema, model & substrate — ✅ (plan §6)

- Hand-rolled YAML-frontmatter parser, no PyYAML ([fux/frontmatter.py](fux/frontmatter.py), [fux/scalars.py](fux/scalars.py)).
- Schema validation against [schema.json](schema.json) ([fux/schema.py](fux/schema.py)).
- Full rule-type taxonomy (`rule`/`formula`/`glossary`/`invariant`/`adr`/`edge-case`/`convention`/`regulatory`/`runbook`/`narrative`/`memory` + skill types `spec`/`task`).
- Lifecycle/provenance (`status`, `created`, `updated`), typed edges
  (`depends-on`/`supersedes`/`contradicts`/`implements`), `code_refs`.
- Frontmatter writeback for mechanical fixes ([fux/fmwrite.py](fux/fmwrite.py)).

### 2.4 Layered resolution — ✅ (plan §5)

`global ⊕ packs ⊕ project` with project > pack > global precedence and conflict
detection (same `id` or explicit `contradicts:`). Loader + paths in
[fux/loader.py](fux/loader.py), [fux/paths.py](fux/paths.py),
[fux/settings.py](fux/settings.py). Covered by
[tests/test_resolution.py](tests/test_resolution.py).

### 2.5 Index + JSON views — ✅ (plan §7)

`INDEX.md` (Tier-1) and `rules.json` (Tier-3) generated on `fux build`
([fux/index.py](fux/index.py), [fux/build.py](fux/build.py)). Generated `.fux/out/`
is gitignored by default; rebuilt for free.

### 2.6 Graph — ✅ (plan §7, §13.1)

Implemented ([fux/graph.py](fux/graph.py), [fux/astextract.py](fux/astextract.py),
[fux/graphhtml.py](fux/graphhtml.py), [fux/community.py](fux/community.py),
[fux/graphquery.py](fux/graphquery.py)):

- **Python** — real symbol + intra-file `calls` edges via stdlib `ast`.
- **JS/TS, Go, Rust** — declaration nodes **and intra-file `calls` edges** via
  brace-matched function bodies (string/comment-aware heuristic, shared
  `CALL_KEYWORDS` filter). Covered by [tests/test_astextract.py](tests/test_astextract.py).
- **Optional real ASTs (`[ast]` extra, plan §19a)** — `pip install fux-engine[ast]`
  swaps the heuristic for `tree-sitter` on JS/TS/Go/Rust (`_treesitter`/`_ts_parser`),
  **same node/edge schema**, default still stdlib-only/$0. `graph.build` stamps
  `meta.extractor` and `fux check` flags `extractor-drift` on backend mismatch so the
  graph stays reproducible. Covered by [tests/test_ast_backend.py](tests/test_ast_backend.py).
- File nodes + `governs` (rule→code), `contains` (file→symbol), `references`
  (cross-file/cross-language heuristic) edges; rule↔rule typed edges.
- Deterministic **community detection** (label propagation) + `GRAPH_REPORT.md`
  (god nodes by degree, communities).
- Interactive `graph.html` with search + *color: type ⇄ community* toggle.
- Traversals: `query` / `path` / `explain` / `report`.

### 2.7 Recall — ✅ (plan §10.11)

- **Phase 1 (default, $0):** BM25-lite over body + frontmatter-weighted fields
  ([fux/recall.py](fux/recall.py)).
- **Phase 2 (opt-in):** `recall_rerank = true` enables a local re-rank —
  sentence-transformers if the `[embeddings]` extra is installed, else a `$0`
  char-trigram cosine fallback ([fux/embed.py](fux/embed.py)). Default path
  unchanged.
- **Phase 3 (opt-in, $0):** `recall_hybrid` / `fux recall --hybrid` fuses three
  ranked lists — BM25, local semantic ($0 trigram fallback), and **graph
  proximity** (BFS from lexical anchors) — via **Reciprocal Rank Fusion** (k=60)
  ([fux/hybrid.py](fux/hybrid.py)). Default path unchanged.
- **Validated** against a labelled paraphrase eval set + `recall@k`/MRR metrics
  ([fux/bench.py](fux/bench.py), [tests/test_recall_eval.py](tests/test_recall_eval.py)):
  lexical recall@1 = 1.0, hybrid recall@3 = 1.0; hybrid asserted not to regress.

### 2.8 Verify — ✅ (plan §10.1)

- `check:` invariants evaluated in a restricted namespace (`abs`/`sum`/`min`/`max`/
  `len`/`round`/`all`/`any`/`math` + pure iteration builtins, no `__builtins__`).
- Data resolution order: `verify_cmd:` (shell → JSON) → `.fux/verify/<id>.json` →
  `.fux/out/verify_context.json`. No data ⇒ **skip** (never a false fail).
- `examples:` are executed against `check:` from three input shapes — a JSON
  object, an inline `key=value` / `key: value` pair string, or an already-parsed
  mapping — with numeric/boolean/currency **scalar coercion** on values and
  `expect`. Prose that fits none is skipped, preserving "never a false fail"
  ([fux/vexamples.py](fux/vexamples.py), [tests/test_examples.py](tests/test_examples.py)).

### 2.9 Drift & auto-fix split — ✅ (plan §8)

- **Mechanical fixes** (deterministic, [fux/fix.py](fux/fix.py)): drop dead
  `code_refs`, bump `updated`, regenerate INDEX.
- **Git-aware staleness** + `DRIFT.md` via `git log` on `code_refs`
  ([fux/gitutil.py](fux/gitutil.py), [fux/drift.py](fux/drift.py), [fux/findings.py](fux/findings.py)).
- **Plan-drift** finding: a `task`/`spec` not `done` whose `code_refs` changed.
- **Semantic-drift** prompt: in `fix` mode the Stop hook emits a scoped edit
  prompt **with the actual `git diff`** of changed `code_refs` before applying
  mechanical fixes (not auto-edited).

### 2.10 Coverage, tour, glob — ✅

- `fux coverage` (% important files with a governing rule) honoring **recursive
  `**` globs** ([fux/coverage.py](fux/coverage.py), [fux/globs.py](fux/globs.py)).
- `fux tour` → ordered `ONBOARDING.md` ([fux/tour.py](fux/tour.py)).

### 2.11 Cost-savings estimator — ✅ (plan §12)

`fux savings ["query"]` ([fux/savings.py](fux/savings.py)) turns plan §12's
illustrative table into **measured** numbers from real file sizes (≈4 chars/token,
applied identically to both sides), priced in **tokens *and* dollars** at a
configurable `usd_per_mtok` (default = Claude Opus 4.8's $5/M input rate; the win is
on input tokens, so the input price is the right one — model-agnostic, set per
project):

- **Corpus** — active rule count, INDEX (Tier-1) tokens, average rule (Tier-2)
  tokens, and total governed-code tokens across distinct `code_refs` files.
- **Per lookup** (optionally for a query, via `recall`) — *without Fux* (read the
  governed file(s)) vs *with Fux* first-lookup (INDEX once + the rule) and later
  lookups (rule only, INDEX already in context), each with a savings multiplier.
- **Aggregate** — the same averaged over every documented topic (a rule with an
  existing governed file). Missing `code_refs` are excluded from the baseline.
- **Cumulative ledger** ([fux/costledger.py](fux/costledger.py)) — opt-in
  `cost_tracking` records *every* `fux recall` lookup's measured savings into
  `.fux/cost.json` (lifetime tokens-without/with/saved + recent queries), so the
  project can quote a real running total, not a per-call estimate. The summary also
  amortises the lifetime `tokens_saved` across the observed span (`first`→`last`,
  floored at one day) into a **per-day / per-week / per-month** rate, so the win
  reads as ongoing throughput. Every figure is also shown in **dollars** (shared
  `savings.usd` pricing); the ledger stores only tokens, so a price change re-prices
  history without a rewrite. Only **code-bound** matches count (same "topic"
  restriction). `fux savings` prints it; `--reset` clears.

Deterministic, `$0`, no LLM. Covered by [tests/test_savings.py](tests/test_savings.py),
[tests/test_costledger.py](tests/test_costledger.py).

### 2.12 Quality, health & enforcement — ✅

- **`fux lint`** ([fux/lint.py](fux/lint.py)) — rule *quality*, complementary to
  `check`'s *structure*: flags `no-why`, `no-code-refs` (for code-bound types),
  `dangling-edge` (related/typed edge → unknown rule), `no-provenance`, and
  `stub-body`. Advisory by default; `--strict` exits 1.
- **`fux stats`** ([fux/stats.py](fux/stats.py)) — one-glance health: a weighted
  **score** (coverage 40 · verify 30 · authoring 30, minus blocking-drift
  penalty) with a bar/grade, plus corpus breakdown (type/domain/layer) and every
  signal (coverage, verify, drift, lint, savings, graph shape). Composes the
  existing `$0` commands; adds no new analysis.
- **`fux gate`** ([fux/gate.py](fux/gate.py)) — the out-of-session enforcement
  surface: rebuilds views, then **exit 2** on blocking `check` findings or failed
  `verify` (lint advisory unless `--strict-lint`). `fux gate --install` writes a
  git **pre-commit** hook. The Stop hook catches drift mid-session; the gate
  catches it at commit/CI time.

Covered by [tests/test_lint_stats_gate.py](tests/test_lint_stats_gate.py).

### 2.13 Cross-file call edges — ✅ (plan §13.1)

The graph now extracts **cross-file `calls`** (symbol → symbol), not just
intra-file: [fux/astextract.py](fux/astextract.py) `external_call_sites()` returns
each call attributed to its enclosing symbol (Python via `ast`, JS/TS/Go/Rust via
the brace matcher); [fux/graph.py](fux/graph.py) resolves callees against the
global symbol index and suppresses the now-redundant looser file→symbol
`references`. Covered by [tests/test_crossfile_calls.py](tests/test_crossfile_calls.py).

### 2.14 Agent integration — `fux mcp` — ✅

[fux/mcpserver.py](fux/mcpserver.py) is a hand-rolled **MCP** server over stdio
(newline-delimited JSON-RPC 2.0, **stdlib-only** — no `mcp` dependency). It
publishes the read paths as tools — `fux_recall` / `fux_why` / `fux_refs` /
`fux_coverage` / `fux_savings` / `fux_stats` / `fux_context` — so any agent queries
the substrate directly. Register with `claude mcp add fux -- fux mcp`. Covered by
[tests/test_mcp.py](tests/test_mcp.py).

### 2.15 Graph UI — ✅

The interactive `graph.html` ([fux/assets/graph_template.html](fux/assets/graph_template.html),
[fux/assets/graph_boot.js](fux/assets/graph_boot.js); rendered by
[fux/graphhtml.py](fux/graphhtml.py)) is a self-contained, dependency-free canvas
viewer. Built for both developer review and **agent use**:

- **Filters** — per node-type and per **edge-type** toggles (with counts), all/none.
- **Colour modes** — node type · community · rule layer · degree heat.
- **Focus** — click to select, double-click to isolate a node's neighbourhood,
  neighbour highlighting on hover, directed **arrowheads** coloured by edge type.
- **Details panel** — metadata pills (domain/layer/status/community/degree) +
  neighbours grouped by edge type, click-through to navigate.
- **Layout controls** — pause/resume, link-distance & charge sliders, fit, reset,
  label toggle; keyboard shortcuts (`/ f r space e Esc l`).
- **Agent export** — *Copy node ⧉* (selected node + connections as markdown) and
  *Copy visible graph ⧉* (the filtered sub-graph as markdown) → paste straight
  into an agent prompt.
- **Performance** — repulsion loop processes each pair once (`i<j`) for O(n²/2)
  work instead of O(n²); `PHYS_STRIDE` skips physics every other frame on graphs
  with >600 nodes so the render thread stays at ≥30 fps regardless of graph size.

Render contract covered by [tests/test_graphhtml.py](tests/test_graphhtml.py).

### 2.16 Skills — ✅ (plan §16)

Registered under `~/.claude/skills/` (installed by [install.sh](install.sh)):
`fux`, `fux-plan` (flagship, spec-driven requirements → design → tasks),
`fux-adr`, `fux-debate` (two-agent free debate → human ratifies a rule, plan §7b),
`fux-trace`, `fux-savings` (interpret the cost report → a next action),
and `fux-distill` (capture this session's decisions as durable `memory`/`adr`
entries — the memory-replacement loop, human-confirmed). Guides:
[docs/spec.guide.md](docs/spec.guide.md), [docs/rule.guide.md](docs/rule.guide.md).
`plan`/`adr`/`debate`/`distill` author via the LLM in-session; `trace`/`savings` are
pure `$0`. All ride the current session (no background spend) — Fux itself never calls
a model, asserted by [tests/test_no_llm_imports.py](tests/test_no_llm_imports.py).

### 2.17 Roadmap §17 — memory, capture, governance, dashboard — ✅

The plan §17 engine items, all `$0` and opt-in (defaults unchanged):

- **RRF hybrid recall** ([fux/hybrid.py](fux/hybrid.py)) — see §2.7.
- **Opt-in capture** ([fux/capture.py](fux/capture.py)) — when `capture = true`, the
  Stop hook records which important files changed this session (governed vs
  uncovered), with a secret-path filter (`.env`/`*.key`/…) and SHA-256 dedup, into
  `.fux/capture/`. **Never** auto-authors a `memory` entry — the `distill` skill
  (human-confirmed) consumes `fux capture --list`. No LLM.
- **Memory governance** ([fux/governance.py](fux/governance.py)) — `type: memory`
  decays after `memory_ttl_days` (default 180): `fux check` emits `memory-stale`
  and `fux context` excludes it from the SessionStart injection (kept on disk).
  Rules never decay.
- **Recall benchmark** ([fux/bench.py](fux/bench.py)) — `recall@k` + MRR over a
  labelled set; the harness that lets Fux quote a real number.
- **Expanded MCP** ([fux/mcpserver.py](fux/mcpserver.py)) — `fux_query`/`fux_trace`
  (graph traversal) + draft-only `fux_new` added to the tool set.
- **`fux serve`** ([fux/serve.py](fux/serve.py)) — a `http.server` dashboard: the
  `stats` health summary + links to `graph.html`/reports.
- **Graph hardening** ([fux/astextract.py](fux/astextract.py)) — `sanitize_lines`,
  a char state machine that blanks string/template literals and `//` + `/* */`
  (multi-line) comments before brace matching, so braces inside them don't skew
  function spans.

Covered by [tests/test_hybrid.py](tests/test_hybrid.py),
[tests/test_capture_governance.py](tests/test_capture_governance.py),
[tests/test_mcp_extra.py](tests/test_mcp_extra.py),
[tests/test_serve_sanitize.py](tests/test_serve_sanitize.py).

### 2.18 Decommission-unblocking parity work — ✅ (plan §17.13–17)

The engine capability needed before Anton's old stores can be safely retired —
each maps to a readiness blocker, all `$0`:

- **Full-repo graph coverage** ([fux/graph.py](fux/graph.py), [fux/config.py](fux/config.py))
  — `graph_globs` decoupled from `important_globs`: `fux build` graphs the broad
  set (so the graph approaches a whole-repo scan, closing the 329/1906 gap),
  `coverage` keeps the narrow target. `fux build --full` graphs every non-ignored
  file (`.fux/`/`.git/` always skipped).
- **`fux import`** ([fux/importer.py](fux/importer.py)) — ingest existing markdown
  files/dirs as `narrative` entries (frontmatter stamped, body preserved); the
  one-pass `docs/` migration. Skips existing without `--force`.
- **Narrative rendering** ([fux/narrative.py](fux/narrative.py)) — `fux build`
  writes `NARRATIVE.md` (TOC + bodies), linked from `fux serve` — §11's "browsable
  view" delivered, so `docs/` has a real destination.
- **`fux import-memory`** ([fux/importer.py](fux/importer.py)) — mirror Claude's
  home-dir `memory/*.md` into `.fux/memory/<scope>/`, normalising `subtype`/`scope`.
- **`fux parity`** ([fux/parity.py](fux/parity.py)) — the measurable gate: coverage
  of **current** source files by the graph (not a node-count match against a
  possibly stale `graphify-out/`, which it flags), `docs/` not yet `narrative`
  (excluding `conventions`/`guardrails` + `parity_stay`), home-memory not yet
  imported (the home-dir slug fix handles `_`→`-`), `READY`/`NOT READY`, exit 1.

Covered by [tests/test_parity_import.py](tests/test_parity_import.py).

### 2.19 Packaging & install — ✅

- [install.sh](install.sh) installs **editable** (`pip -e`) → `~/.claude/fux/{engine,global,packs,hooks}` + skills.
- [pyproject.toml](pyproject.toml) (v0.4.0, stdlib-only; `[embeddings]`/`[ast]`/`[pdf]`/`[critic]` extras),
  [justfile](justfile), global seed in [global/](global/).

### 2.20 Tests — ✅ (204 tests)

[tests/](tests/): resolution, frontmatter, globs, check/fix, recall/build/verify,
embed/rerank, schema/scaffold/init, cross-language + **cross-file** call edges
([test_astextract.py](tests/test_astextract.py), [test_crossfile_calls.py](tests/test_crossfile_calls.py)),
the optional **tree-sitter backend + extractor provenance** ([test_ast_backend.py](tests/test_ast_backend.py)),
extended verify examples ([test_examples.py](tests/test_examples.py)), the
**recall eval set + recall@k/MRR** ([test_recall_eval.py](tests/test_recall_eval.py)),
**RRF hybrid** ([test_hybrid.py](tests/test_hybrid.py)), the cost-savings estimator
([test_savings.py](tests/test_savings.py)), lint/stats/gate
([test_lint_stats_gate.py](tests/test_lint_stats_gate.py)), **capture + governance**
([test_capture_governance.py](tests/test_capture_governance.py)), the MCP server +
expanded tools ([test_mcp.py](tests/test_mcp.py), [test_mcp_extra.py](tests/test_mcp_extra.py)),
the graph-HTML render + **serve/sanitizer**
([test_graphhtml.py](tests/test_graphhtml.py), [test_serve_sanitize.py](tests/test_serve_sanitize.py)),
and **graph coverage / import / narrative / parity**
([test_parity_import.py](tests/test_parity_import.py)), plus the beyond-roadmap
work: **PageRank centrality** ([test_centrality.py](tests/test_centrality.py)),
**AST seals + history** ([test_seal.py](tests/test_seal.py)), **BM25F + query
expansion** ([test_bm25f_expand.py](tests/test_bm25f_expand.py)), **knapsack context
packing** ([test_pack.py](tests/test_pack.py)), **usage-weighted decay + overlap
lint** ([test_verify_hardening.py](tests/test_verify_hardening.py)), and **fuzzing +
rule mining** ([test_fuzz_mine.py](tests/test_fuzz_mine.py)), and the **constitution
layer — tier blocking + §5b migration guard** ([test_constitution_tier.py](tests/test_constitution_tier.py))
and **tamper-evidence + ratification + lock** ([test_constitution_integrity.py](tests/test_constitution_integrity.py)),
the **deterministic/judgment split + backfill guide** ([test_critic_split.py](tests/test_critic_split.py)),
the **critique→act loop + report-first coverage gate** ([test_critic_loop.py](tests/test_critic_loop.py)),
plus the **no-LLM-on-the-maintenance-path guard** ([test_no_llm_imports.py](tests/test_no_llm_imports.py)).
Run with `python -m pytest` (Python ≥ 3.11).

### 2.21 Constitution layer — ✅ (plan §6 "Constitution layer", Phases 0–5 + 3b, v0.4.0)

The tiered-governance + integrity substrate from plan §6. **Shipped (Phases 0–2):**

- **`tier`** schema field (`constitutional`/`standard`/`advisory`, default `standard`)
  — additive and optional; every existing rule stays valid unchanged ([schema.json](schema.json)).
- **Tier-aware blocking** ([fux/findings.py](fux/findings.py) `blocking(findings, mode)`):
  constitutional findings block in **any** `mode` (so `unsealed` blocks the apex),
  standard only under `strict`, advisory never; `tampered` always blocks. `fux gate` reads
  the project `mode`; `fux check` output is canonically sorted (kind, rule_id, message).
- **§5b migration guard** ([fux/baseline.py](fux/baseline.py)) — `fux check
  --baseline-write <file>` snapshots findings; `fux gate --baseline <file>` fails only on
  findings *new* since the snapshot (a transient upgrade check, **not** a regression
  subsystem). Proven a no-op on fux's own `.fux/` rules.
- **Tamper-evidence + ratification** ([fux/constitution.py](fux/constitution.py)) — a
  ratified constitutional rule carries `ratification.content_seal` (hash of normalized body
  + governing fm) and is recorded in a committed `.fux/constitution.lock`. `fux check`'s
  `check_tamper` (recompute vs stamp) + `check_lock` (stamp vs lock) raise an always-
  blocking `tampered` on any in-place edit, add, or delete. `fux ratify <id>` (deterministic,
  no LLM) is the **only** path that stamps ratification, freezes the code seal, and writes
  the lock. A `tier: constitutional` rule that carries **no** `ratification.content_seal` —
  added directly, or promoted by a `tier:` frontmatter edit — is itself an always-blocking
  `tampered` finding, so the apex tier cannot be entered or promoted-into outside `fux ratify`.
  Non-constitutional rules are untouched.
- **Provenance drift** ([fux/provenance.py](fux/provenance.py)) — `fux ratify --debate <file>`
  pins the transcript at `.fux/debates/<id>.md` and stamps its raw-bytes hash into
  `ratification.debate_hash`; `check_provenance` re-hashes that file on every `fux check` and
  raises an always-blocking `tampered` when it drifts (or goes missing), **constitutional rules
  only**. A transcript is corrected by re-ratification, never by editing the file. ($0, stdlib.)
- **Status view** ([fux/constatus.py](fux/constatus.py)) — `fux constitution` renders the apex on
  one screen: each constitutional rule, ratified/un-ratified, what it governs, ratifier + debate
  hash with a live transcript-drift check, and current blocking violations. Read-only, $0, reuses
  the same `check` the gate runs; exits 2 if the apex has blocking findings.
- **Debate engine** ([fux/data/skills/debate/SKILL.md](fux/data/skills/debate/SKILL.md)) —
  the `/fux debate "<rule>"` skill drives the **host** session to spawn two no-assigned-side
  sub-agents (blind first pass → reveal → anti-sycophancy gates → human escalation on
  non-convergence). Fux's only code is the harness: `fux ratify --debate <transcript>` hashes
  it into `ratification.debate_hash`. Fux spends nothing — guarded by
  [tests/test_no_llm_imports.py](tests/test_no_llm_imports.py) (no maintenance-path module
  imports an LLM client; default install is model-free).
- **Deterministic/judgment split** ([fux/critic.py](fux/critic.py)) — `principle` +
  `enforcement` schema fields (both optional → existing rules stay valid/untagged). The
  router enforces the split *structurally*: `for_ai` returns judgment principles only (a
  `deterministic` one can never reach the AI pass), `for_deterministic` returns deterministic
  only (a `judgment` one is never faked deterministic). `fux check` emits an advisory
  `untagged-candidate` for project rules that look like principles but are untagged — a
  backfill guide that never blocks (even on the apex).
- **Critic loop** ([fux/criticloop.py](fux/criticloop.py)) — `critique()` runs one pass at the
  action boundary: gather principles via recall → **deterministic pass first** (`check:`/seal,
  a fail blocks, no LLM) → judgment principles to a `judge` seam. The seam is the **host
  agent** (`$0`, via [the critic skill](fux/data/skills/critic/SKILL.md)) by default, or the
  opt-in headless backend [fux/criticllm.py](fux/criticllm.py) — the **only** model-importing
  module, lazy + behind the `[critic]` extra, never on the maintenance path. `fux critic
  "<change>"` runs the deterministic pass + lists pending judgment principles + records to
  `.fux/out/critic.jsonl`. `fux gate` **reports** (never blocks) ungoverned `important_globs`
  paths — the report-first coverage gate. (`cmd_ratify`/`cmd_critic` now live in
  [fux/cliconstitution.py](fux/cliconstitution.py), shrinking `clicmds.py`.)
- **Bootstrap rule** [`con-amendment`](../.fux/rules/con-amendment.md) — the amendment
  article (Phase 0), `tier: constitutional`; ratify it with `fux ratify con-amendment`.

**Next (deferred):** the runtime critic (§5 step 3) — expose `critique` as a callable in
front of an app's live money/PII paths. Covered by
[tests/test_constitution_tier.py](tests/test_constitution_tier.py),
[tests/test_constitution_integrity.py](tests/test_constitution_integrity.py),
[tests/test_critic_split.py](tests/test_critic_split.py),
[tests/test_critic_loop.py](tests/test_critic_loop.py),
[tests/test_no_llm_imports.py](tests/test_no_llm_imports.py).

---

## 3. Rollout status (plan §13)

| Phase | Status |
|---|---|
| 1–3 — engine, hooks, global seed | ✅ done; installed to `~/.claude/fux` |
| 4 — Anton pilot (4 rules grounded in `aggregator.py`) | ✅ done |
| 5 — verification (invariant wired to a probe, `just fux-check`) | ✅ done |
| 6 — Wagner (portability + global inheritance) | ✅ done |
| 7 — absorb & migrate | 🟡 additive done (memory + narrative imported); **decommission deferred** |

---

## 4. Remaining / future work

The full roadmap lives in **[fux-plan.md §17](fux-plan.md)**. The **engine items
(§17.1–6, 8) are now shipped** — RRF hybrid recall, opt-in capture, memory
governance, the recall benchmark, expanded MCP, `fux serve`, and the
block-comment-aware sanitizer (see §2.7 and §2.17 above).

What remains is **operational, not engine code in this repo** — the decommission
*tooling* now exists (§2.18), so these are runs against Anton, not engine gaps:

- ⬜ **Anton brokers pilot** — ground real broker rules in
  `backend/app/modules/brokers/`, wire `verify`/`gate` into `probes/` + `just`,
  measure with `coverage`/`savings`.
- ⬜ **Run the decommission** — in Anton: `fux build --full` → `fux import docs/`
  → `fux import-memory`, watching `fux parity` until READY, then retire
  `graphify-out/` + the migrated `docs/`.

Planned (engine, see [fux-plan.md §17.10–12](fux-plan.md)):

- ⬜ **PyPI packaging** — bundle `schema.json`/`hooks`/`global`/`skills` as package
  data, add a `fux setup` command, and a Trusted-Publishing release workflow →
  `pipx install fux-engine && fux setup`.

Possible follow-ups (not blocking): cross-**file** call edges for more languages;
auto-suggest `supersedes:` on memory contradiction.
- ⬜ **Graph hardening** — block-comment / multiline-template awareness in the brace
  matcher; cross-file call edges for more languages.

### Beyond roadmap — SOTA & frontier ([fux-plan.md §17, items 18–27](fux-plan.md))

Pushes past the planned scope; all `$0`, deterministic, stdlib-only. **Shipped (8 of
10 sub-areas):**

- ✅ **18 Retrieval to SOTA** — true per-field BM25F ([recall.py](../fux/recall.py)),
  opt-in deterministic query expansion (`recall_expand`/`--expand`), eval grown to 24
  queries + hard negatives + a regression gate ([test_recall_eval.py](../tests/test_recall_eval.py)):
  recall@1 0.875 / recall@3 1.0 / MRR 0.931.
- ✅ **19 Graph to exact** — ✅ deterministic **PageRank centrality**
  ([graphquery.py](../fux/graphquery.py)) on every node + a `GRAPH_REPORT.md`
  "Chokepoints" section; ✅ optional **`[ast]` tree-sitter extra**
  ([astextract.py](../fux/astextract.py) `_treesitter`/`_ts_parser`) — real ASTs for
  JS/TS/Go/Rust when installed, identical node/edge schema, default still stdlib-only.
  Reproducibility kept honest: `graph.build` stamps `meta.extractor`
  (`backend_fingerprint()`) and `fux check` raises a non-blocking `extractor-drift`
  finding on backend mismatch ([test_ast_backend.py](../tests/test_ast_backend.py)).
- ✅ **20 Verification hardening** — `fux verify --fuzz` div-by-zero boundary fuzzing
  ([vexamples.py](../fux/vexamples.py)), `overlap-unlinked` lint ([lint.py](../fux/lint.py)),
  usage-weighted decay (`usage_tracking`, [usage.py](../fux/usage.py) → [governance.py](../fux/governance.py)).
- ✅ **22 Proof-carrying rules (AST seals)** — [seal.py](../fux/seal.py), `seal:` field,
  `fux seal`, advisory `unsealed` finding.
- ✅ **23 Rule mining** — `fux mine` ([mine.py](../fux/mine.py)), magic-number first cut.
- ✅ **24 Knowledge archaeology** — `fux why <id> --history` ([explain.py](../fux/explain.py)).
- ✅ **25 Optimal context packing** — 0/1 knapsack ([pack.py](../fux/pack.py)) gated on
  `context_budget_tokens`.

**Deferred (need a non-`$0` / runtime surface, kept ⬜):** 21 automated value proof
(live agent runs), 26 self-densifying graph (MCP-runtime traversal logging), 27
federated mesh (**undecided — may never ship**).

---

## 5. Key references

- Complete example-driven guide: [docs/guide.md](docs/guide.md)
- Design of record: [docs/fux-plan.md](docs/fux-plan.md)
- Architecture: [docs/architecture.md](docs/architecture.md)
- CLI reference: [docs/cli.md](docs/cli.md)
- Implementation deltas: [docs/implementation-notes.md](docs/implementation-notes.md)
- Comparisons: [docs/recall-engine.compare.md](docs/recall-engine.compare.md),
  [docs/global-rules-home.compare.md](docs/global-rules-home.compare.md)
