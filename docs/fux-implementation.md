# Fux — Implementation Status

> Engine **v0.6.0** — the real merge wall: two required checks (`fux gate` + `ai-review`), ratify-through-PR, and a scheduled branch-protection drift audit (on the v0.5.0 advisory-first critic / v0.4.0 constitutional-app engine). A portable, Claude-aware knowledge engine: one frontmatter
> substrate → derived index, graph, and memory views, with `$0` deterministic
> maintenance. This file tracks **what has shipped** and **what remains**, mapped
> to the design of record in [docs/fux-plan.md](docs/fux-plan.md).

**Legend:** ✅ done · 🟡 partial · ⬜ not started

---

## 1. Snapshot

| Area | Status | Notes |
|---|---|---|
| Core CLI surface (plan §9) | ✅ | 43 public commands wired in [fux/cli.py](fux/cli.py) from one registry ([fux/registry.py](fux/registry.py)); grouped `--help` + `fux help <cmd>` + `fux how` |
| Hooks (3 core + 2 optional) | ✅ | SessionStart, PostToolUse, Stop + opt-in UserPromptSubmit & capture; **fail-open** (a hook error never breaks the session; strict `stop`→2 preserved) |
| Error-handling contract | ✅ | One `FuxError` ([fux/errors.py](fux/errors.py)); CLI `main()` boundary maps exit codes `0/1/2/130`; `FUX_DEBUG=1` for tracebacks + swallowed-hook traces ([tests/test_errors.py](tests/test_errors.py)) |
| Rule schema + frontmatter parser | ✅ | Hand-rolled, stdlib-only ([fux/frontmatter.py](fux/frontmatter.py), [schema.json](schema.json)) |
| Layered resolution (global ⊕ packs ⊕ project) | ✅ | Precedence + conflict detection |
| Graph engine (AST extraction) | ✅ | Python via `ast`; JS/TS/Go/Rust intra- **and cross-file** `calls`; block-comment-aware sanitizer |
| Recall | ✅ | BM25-lite default; opt-in local re-rank **+ RRF hybrid** (lexical⊕semantic⊕graph) |
| Memory governance + capture | ✅ | TTL decay ([fux/governance.py](fux/governance.py)); opt-in capture queue ([fux/capture.py](fux/capture.py)) |
| Verify | ✅ | `check:` invariants + examples (JSON, inline `key=value`, scalar coercion) |
| Quality & health (`lint`/`stats`) | ✅ | Rule-quality lint + weighted health score ([fux/lint.py](fux/lint.py), [fux/stats.py](fux/stats.py)) |
| Enforcement (`gate`) | ✅ | CI / git pre-commit; **tier-aware** exit 2 on blocking ([fux/gate.py](fux/gate.py)) |
| Merge wall (required checks + branch protection) | ✅ | `fux gate` + `ai-review` are **required status checks** on `main` (`enforce_admins`, no force-push); only path in is a gated PR. Source of truth [.github/branch-protection.json](.github/branch-protection.json) + apply/audit scripts; weekly drift-audit Action. `fux ratify` opens the PR itself (§2g). See [docs/constitution-enforcement-handoff.md](docs/constitution-enforcement-handoff.md) |
| Constitution layer (tiers, integrity, provenance, debate, split, critic) | ✅ | Tiers + `--baseline` + tamper/lock/`ratify` (incl. un-ratified/promoted-tier block) + provenance drift + `/fux debate` + split router + critic loop & report-first coverage gate (Phases 0–5 + 3b, v0.4.0); only the runtime critic is deferred ([fux/constitution.py](fux/constitution.py), [fux/provenance.py](fux/provenance.py)) |
| Agent integration (`mcp`) | ✅ | Stdlib MCP stdio server ([fux/mcpserver.py](fux/mcpserver.py)) |
| Graph UI | ✅ | Filters, focus, details, arrows, agent export ([fux/assets/](fux/assets/)) |
| Skills (`plan`/`adr`/`trace`/`savings`/`distill`/`propose-rules`) | ✅ | `plan` flagship; `distill` closes the memory loop; `propose-rules` the authoring loop |
| Skill renderer (`tools/skillgen`) | 🟡 | Build-time, stdlib-only renderer: one fragment set → the `fux` skill's `claude`/`agents`(AGENTS.md)/`copilot` artifacts; `--check` drift-guard in CI + pre-commit. Foundation only — other skills/hosts hand-authored ([docs/skillgen.md](skillgen.md)) |
| Rule Proposer (agents author, humans ratify; [rule-proposer.md](rule-proposer.md)) | ✅ | `fux propose-rules [--retro\|--from]` + `fux candidates [accept\|reject]` → persistent, never-blocking `.fux/CANDIDATES.md`; §4 gate, dedup vs rules+queue, capped; nothing auto-active/constitutional; $0 harness (guard) ([fux/proposer.py](fux/proposer.py), [fux/candidates.py](fux/candidates.py)) |
| Decommission tooling (graph coverage, import) | ✅ | `build --full`, `import`/`import-memory` — see §2.20 |
| Decommission old stores in Anton | ⬜ | Tooling shipped; run it against Anton, then retire the legacy stores once coverage is confirmed ([plan §17.9](fux-plan.md)) |

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
| `fux ratify <id> [--by NAME] [--date ISO] [--debate FILE] [--no-pr]` | ✅ | [fux/cliconstitution.py](fux/cliconstitution.py), [fux/constitution.py](fux/constitution.py); routes through a `constitution/<id>` branch+PR ([fux/gitutil.py](fux/gitutil.py)) |
| `fux capture-decision <id> --route fux\|anton\|elgar [--method M] [--by N] [--from FILE] [--debate FILE] [--yes]` | ✅ | [fux/decisioncapture.py](fux/decisioncapture.py), [fux/cliconstitution.py](fux/cliconstitution.py); routed, content-sealed ADRs in `.fux/decisions/`; money→elgar link-only (ADR 0001) |
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
| `fux pii-scan [paths…]` | ✅ | [fux/piiscan.py](fux/piiscan.py), [fux/clicmds.py](fux/clicmds.py); dante's BLOCK regexes (stdlib), wired into the `fux gate` CI job |
| `fux mcp` | ✅ | [fux/mcpserver.py](fux/mcpserver.py) |
| `fux capture [--list] [--clear]` | ✅ | [fux/capture.py](fux/capture.py) |
| `fux serve [--port N]` | ✅ | [fux/serve.py](fux/serve.py) |
| `fux import <path…>` | ✅ | [fux/importer.py](fux/importer.py) |
| `fux import-memory [--scope]` | ✅ | [fux/importer.py](fux/importer.py) |
| `fux tour` | ✅ | [fux/tour.py](fux/tour.py) |
| `fux query "Q" [--depth N] [--self]` | ✅ | [fux/cligraph.py](fux/cligraph.py), [fux/graphquery.py](fux/graphquery.py) |
| `fux path <a> <b> [--self]` | ✅ | [fux/cligraph.py](fux/cligraph.py) |
| `fux explain <term> [--self]` | ✅ | [fux/cligraph.py](fux/cligraph.py) |
| `fux self-build` · `--self` scope | ✅ | [fux/selfbuild.py](fux/selfbuild.py), [fux/cliutil.py](fux/cliutil.py) (`scope_root`) — pre-built self-knowledge bundle in `data/self/` |
| `fux report` | ✅ | [fux/report.py](fux/report.py) |
| `fux help [<cmd>]` · grouped `--help` | ✅ | [fux/registry.py](fux/registry.py), [fux/clihelp.py](fux/clihelp.py) |
| `fux how "Q" [--top N] [--explain]` | ✅ | [fux/howto.py](fux/howto.py) (reuses [fux/recall.py](fux/recall.py)) |
| `fux ingest <srcs…> [--follow-links] [--connector C --query Q] [--queue]` · `<id> --recheck` | ✅ | skill ([data/skills/ingest](fux/data/skills/ingest/SKILL.md)) + [fux/ingest.py](fux/ingest.py), [fux/ingestqueue.py](fux/ingestqueue.py), [fux/ingestfollow.py](fux/ingestfollow.py), [fux/ingestreduce.py](fux/ingestreduce.py), [fux/ingestconnector.py](fux/ingestconnector.py), [fux/cdp_utils.py](fux/cdp_utils.py) — batch + bounded link-following + connectors + reduce-before-draft; `scrape` is a deprecated alias |
| `fux fetch-rules <source> [--raw]` | ✅ | [fux/cliquery.py](fux/cliquery.py), [fux/fetchrules.py](fux/fetchrules.py) |

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

Every entrypoint is **fail-open** ([fux/hooks.py](fux/hooks.py)): a caught exception
returns 0 so a broken `.fux/` never breaks the session — the only non-zero exit is the
deliberate strict `stop`→2 (computed in `_stop()`, passed straight through the wrapper).
Swallowed exceptions are silent to the user but printed under `FUX_DEBUG=1` (fail-open ≠
fail-silent). The shell wrappers for the three non-blocking hooks guard `fux_run` with
`|| true`; `stop.sh` deliberately does not, so its exit-2 passes through. See the exit-code
contract in [docs/cli.md](docs/cli.md).

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
- **Optional cage receipt (token-savings, off-by-default).** `hook-recall` injects
  only the relevant rules instead of the whole corpus — a measurable token saving.
  When the optional `cage` ledger is installed, the recall hook files one
  `tool="fux"` receipt: `actual` = the injected payload's tokens, `raw_alternative`
  = the selected rules' **whole source files** loaded raw (the conservative
  distilled-vs-source default), tagged `modeled`, `confidence=0.7`, `meta={"op":
  "hook-recall"}`. It is a **fail-open lazy shim** ([fux/cage_receipt.py](fux/cage_receipt.py)):
  cage is **never** a dependency — `import cage` is wrapped in `try/except` and the
  hook is byte-identical with cage absent. No rule text or PII leaves fux — counts
  only. See cage's [receipt contract](https://github.com/arpitarya/cage).

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
- **Lenses** — Knowledge · Communities · Heat · Path · **Coverage** (warm = code a
  rule touches via `governs`/`related`/`references`/`implements`, cold-grey =
  ungoverned — the governed/ungoverned split at a glance, client-only).
- **Focus** — click to select, double-click to isolate a node's neighbourhood,
  neighbour highlighting on hover, directed **arrowheads** coloured by edge type.
- **Macro LOD** — below `view.k < 0.4` each community collapses to **one blob**
  (area ∝ member count, coloured by community, amber-cored if it holds knowledge)
  behind a faint **convex-hull territory** with a **top-centrality label**;
  individual nodes return on zoom-in. Both faster *and* clearer at overview.
- **Governance overlay** — rules whose **AST seal has drifted** pulse red;
  **constitutional**-tier rules wear a crown. Both read off `drift`/`tier` fields
  stamped into `graph.json` (§2.15a) — deterministic, sourced from `seal`/`check`.
- **Details panel** — metadata pills (domain/layer/status/community/degree, plus
  `♚ constitutional` / `⚠ drifted`) + neighbours grouped by edge type, click-through.
- **Agent export** — *Copy node ⧉* / *Copy visible graph ⧉* / *Copy governed
  subgraph ⧉* as markdown → paste straight into an agent prompt.
- **Performance** — a hand-rolled **Barnes–Hut quadtree** (O(n log n), θ≈0.8)
  replaces the old O(n²) pair loop; the draw path adds **viewport culling**,
  **pre-rendered amber glow sprites** + a two-pass governs-thread stroke (no
  per-frame `shadowBlur`/gradients), a cached visible-node list, and an **offscreen
  static-substrate cache** blitted when idle. On the largest available graph
  (~2,356 nodes / 14,744 edges) median frame time dropped **~38 ms → ~5 ms**
  active and **~1.9 ms** idle, with no visual regression. Still zero deps, offline.

The new `graph.json` rule-node fields are documented in §2.15a. *(Deferred: Horizon 3
git-history playback — animating rules + `governs` threads over commits.)*

Render contract + drift/tier stamping covered by
[tests/test_graphhtml.py](tests/test_graphhtml.py) and
[tests/test_graph_drift.py](tests/test_graph_drift.py).

### 2.15a Graph drift/tier stamp — ✅

`graph.build` ([fux/graph.py](fux/graph.py)) stamps every **rule node** with two
extra fields the viewer's governance overlay reads, both **$0 / deterministic / no
model**:

| Field | Type | Source |
|---|---|---|
| `tier` | `"constitutional" \| "standard" \| "advisory"` | verbatim `r.fm.get("tier", "standard")` — the constitutional crown follows ratification, nothing derived |
| `drift` | `true \| false` | `true` iff the rule has a stored `seal:` **and** `seal.current(root, r)` differs from it (governed code changed *structure* since affirmed) — the **same signal** as `fux check`'s `unsealed` finding ([fux/check.py](fux/check.py) `_seal` / [fux/seal.py](fux/seal.py)). A rule with no seal or no resolvable code is `drift: false` — nothing affirmed to drift from. |

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

### 2.18 Decommission-unblocking work — ✅ (plan §17.13–17)

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
  home-dir `memory/*.md` into `.fux/memory/<scope>/`, normalising `subtype`/`scope`
  (the home-dir slug fix handles `_`→`-`).

Covered by [tests/test_parity_import.py](tests/test_parity_import.py).

### 2.19 Packaging & install — ✅

- [install.sh](install.sh) installs **editable** (`pip -e`) → `~/.claude/fux/{engine,global,packs,hooks}` + skills.
- [pyproject.toml](pyproject.toml) (v0.6.0, stdlib-only; `[embeddings]`/`[ast]`/`[pdf]`/`[critic]` extras),
  [justfile](justfile), global seed in [global/](global/).
- `[tool.setuptools.packages.find]` carries an explicit `exclude = ["tools*"]` so the
  build-time `tools/skillgen/` renderer never ships in the wheel/sdist (tested).

### 2.20 Tests — ✅ (364 tests)

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
and **tamper-evidence + ratification + lock + supersession** ([test_constitution_integrity.py](tests/test_constitution_integrity.py)),
the **status view — recent debates + violations-by-severity** ([test_constitution_status.py](tests/test_constitution_status.py)),
the **deterministic/judgment split + backfill guide** ([test_critic_split.py](tests/test_critic_split.py)),
the **critique→act loop + advisory-first critic + report-first coverage gate**
([test_critic_loop.py](tests/test_critic_loop.py)),
the **ratify → branch+PR routing guards** ([test_ratify_pr_routing.py](tests/test_ratify_pr_routing.py)),
the **CLI help registry + `fux how` self-docs + CDP precedence + ingest provenance/recheck**
([test_howto_help_ingest.py](tests/test_howto_help_ingest.py)), the **batch +
linked-document ingestion — queue/dedup, bounded follow-links, reduce-before-draft,
Swagger drift** ([test_ingest_batch.py](tests/test_ingest_batch.py)),
plus the **no-LLM-and-no-network-and-no-doc/vision-lib-on-the-maintenance-path guard**
([test_no_llm_imports.py](tests/test_no_llm_imports.py)), and the **skill renderer —
byte-determinism, `--check` pass/fail, per-host anchors, no-unfilled-slot, runtime-import
boundary + wheel/sdist exclusion** ([test_skillgen.py](tests/test_skillgen.py)), and the
**error-handling contract — CLI exit codes (`FuxError`→1, Ctrl-C→130, unexpected→1 with
traceback only under `FUX_DEBUG`), per-hook fail-open, strict `stop`→2 preserved, and the
`FUX_DEBUG` swallowed-exception trace** ([test_errors.py](tests/test_errors.py)).
Run with `python -m pytest` (Python ≥ 3.11). Current: **364 passed, 2 skipped**.

**Exhaustive end-to-end harness — `fux-lab` (external sibling repo).** Beyond the
unit suite, an offline `$0` harness lives in a separate `fux-lab/` repo (polyglot
fixture + stdlib-only `run_lab.py`). It drives **every** command in
[fux/registry.py](registry.py) — a registry-generated coverage manifest proves
**44/44 accounted for** (`fux-lab/test_coverage.py`) so exhaustiveness can't
silently rot — diffs machine output against committed goldens, springs
worktree-isolated traps (each must fire its finding), runs negative guards (each
must stay quiet), proves `$0` with the network disabled, exercises the error
contract, and writes a ranked `FINDINGS.md`. It **reports** engine bugs and never
edits the engine to make a finding green. Its first sweep (93 checks) surfaced two
real findings — **both since fixed** and re-verified by the harness (0 findings):

1. **Error-contract gap** *(fixed)* — `fux why <unknown-id>` printed `fux: no rule
   '…'` to *stdout* and exited 1; it now raises `FuxError` ([cliquery.py](cliquery.py)
   `cmd_why`) → terse `error: …` on *stderr* ([test_errors.py](tests/test_errors.py)).
2. **Seal-stability false positive** *(fixed)* — the frontmatter writer emitted a
   *string* `"true"` as bare `true`, which the reader re-parsed as a bool, changing
   a ratified rule's `content_seal` and raising a false `tampered`. The writer now
   quotes any string whose bare form would re-parse as a non-string
   ([fmwrite.py](fmwrite.py) `_scalar`, [test_frontmatter.py](tests/test_frontmatter.py)).

### 2.20a Command registry + `fux how` + scrape — ✅ (handoff A–D)

The web-rules / self-docs / CLI-help bundle, all `$0`/stdlib/deterministic:

- **D · One command registry** ([fux/registry.py](fux/registry.py)) — name · group
  (authoring · verification · governance · runtime) · one-line desc · copy-paste
  example · related, one per public command. [fux/clihelp.py](fux/clihelp.py) renders
  the grouped `fux --help`, the per-command `fux help <cmd>` / `fux <cmd> --help`
  (desc + usage + example + related), and the `docs/cli.md` registry table — a test
  asserts the doc block equals `clihelp.render_cli_md_block()` so help/docs can't drift,
  and another asserts the registry equals the CLI dispatch surface.
- **C · `fux how`** ([fux/howto.py](fux/howto.py)) — builds a synthetic corpus from the
  registry + a few self-doc snippets and runs the **existing BM25F recall**
  ([fux/recall.py](fux/recall.py)) over it; returns a short explanation **plus the exact
  command** for the task. Deterministic + byte-stable; `--explain` emits a fenced prompt
  the *host agent* answers (its tokens), never an engine call.
- **B · CDP endpoint** ([fux/cdp_utils.py](fux/cdp_utils.py), ≤50 lines) — pure-string
  resolution by precedence: `--cdp-port`/`--cdp-host` flags → `FUX_CDP_PORT`/`FUX_CDP_HOST`
  env → `cdp_port`/`cdp_host` in config → default `127.0.0.1:9299`. No socket on the engine
  side; config defaults + template entry in [fux/config.py](fux/config.py).
- **A · Scrape** — a **skill** ([data/skills/scrape/SKILL.md](fux/data/skills/scrape/SKILL.md)),
  wired into `fux setup`/`install.sh` + the `/fux` index: the agent fetches (HTTP → CDP),
  classifies trust (docs→`convention`; own→`rule`/`glossary`; market→`rule`;
  regulatory/tax/compliance→`regulatory`, DRAFT-VERIFY, mandatory human ratify), and drafts
  `status: draft` rules with new additive optional schema fields `source`/`fetched`/
  `source_hash` ([schema.json](schema.json)). The only network-touching engine path is the
  opt-in `fux scrape <id> --recheck` ([fux/scrape.py](fux/scrape.py), behind the `[scrape]`
  extra, lazily importing [fux/fetchrules.py](fux/fetchrules.py)) which re-fetches a source,
  recomputes the canonical hash, and raises a non-blocking `source-drift` finding — **never
  on the default `fux check` path**.
- **Guard** ([tests/test_no_llm_imports.py](tests/test_no_llm_imports.py)) extended: no LLM
  **and no network** import is reachable from check/gate/verify/seal/recall/howto (+
  registry/clihelp/cdp_utils); only `fetchrules`/`scrape` may name a network client, both
  lazily imported; the default install is model-free **and offline** (subprocess check).

### 2.20b Ingest from files (URL → multi-source) — ✅ (ingest-files-handoff.md, PR2)

Generalizes 2.20a's URL-only scraper into a multi-source ingester. Single concern:
the *extract* step branches on source type; classify → draft → govern is the
PR1 pipeline, reused as-is.

- **Rename.** `/fux scrape <url>` → `/fux ingest <url|file>`
  ([fux/cli.py](fux/cli.py), [fux/cliquery.py](fux/cliquery.py),
  [fux/ingest.py](fux/ingest.py) — was `fux/scrape.py`). `scrape` stays wired as a
  **deprecated alias** (`cmd_scrape_deprecated`) for one release: same behaviour,
  prints a one-line deprecation note to stderr.
- **Five extract branches, all agent-side** ([data/skills/ingest/SKILL.md](fux/data/skills/ingest/SKILL.md),
  was `data/skills/scrape/SKILL.md`): URL (HTTP → CDP, unchanged from PR1), PDF (the
  agent's `pdf` skill), Excel/CSV (its `xlsx` skill), TXT/Markdown (read directly),
  image (native vision/OCR). The engine adds no PDF/Excel/OCR/vision dependency for
  any of this — extraction is always the host agent's tokens.
- **Schema** ([schema.json](fux/data/schema.json)) — additive optional `source_type`
  enum (`url|pdf|xlsx|txt|image`); existing rules with no `source_type` still validate.
- **Image/OCR trust caution** (handoff §4) — [fux/lint.py](fux/lint.py)
  `_verify_source_candidates` deterministically scans **every** rule (drafts included,
  since they never reach `rs.active()`) for `source_type: image` combined with
  `type: regulatory` or a money pattern in the body, and raises the new `verify-source`
  finding (added to [fux/findings.py](fux/findings.py) `KINDS`) — advisory, never
  blocks (`fux gate --strict-lint` can still escalate it like any lint finding).
- **`--recheck` extended to files** — [fux/ingest.py](fux/ingest.py) `recheck()` already
  called `fetchrules.fetch_text(source)`, which branches on URL vs local path; no
  engine change needed — file bytes are read (with `errors="replace"` for non-text
  files) and hashed the same deterministic way, so a changed local file raises
  `source-drift` exactly like a changed page.
- **Guard extended** ([tests/test_no_llm_imports.py](tests/test_no_llm_imports.py)) —
  `DOC_LIB` regex (`pypdf`/`PyPDF2`/`pdfplumber`/`fitz`/`openpyxl`/`xlrd`/`pandas`/
  `pytesseract`/`PIL`/`cv2`/`easyocr`) must not be reachable from the maintenance path
  or anywhere outside `fetchrules.py` (the one sanctioned, lazily-imported `[pdf]` edge
  for the unrelated `fux fetch-rules` URL/PDF path) — proving `fux ingest`'s file
  branches stay entirely agent-side.
- **Tests** ([test_howto_help_ingest.py](tests/test_howto_help_ingest.py), was
  `test_howto_help_scrape.py`) — a draft per source type carries `source_type` +
  provenance; an image-derived money/regulatory draft is flagged `verify-source`
  (and a non-image one is not); `--recheck` fires `source-drift` on a changed local
  file and stays silent when unchanged; the deprecated `scrape` alias still dispatches
  and warns; `fux how` now answers "scrape a website into rules" → `ingest`.

### 2.20c Batch + linked-document ingestion — ✅ (batch-ingest-handoff.md, PR3, v0.11.0)

Adds (a) *many* sources at once and (b) opt-in following of a page to the documents
it links — both bounded, both producing a **draft review queue**, nothing auto-active.
Builds on 2.20b's single-source pipeline; the agent fetches/crawls/parses, the engine
governs. Three new `$0`, stdlib-only engine modules:

- **Draft review queue** ([fux/ingestqueue.py](fux/ingestqueue.py)) — writes/reads the
  Markdown manifest at `.fux/ingest/queue.md` (one row per item: `source` /
  `source_type` / `status: draft|failed` / trust flag / draft id / `source_hash` /
  reason), deduped by `source_hash`; `expand_sources` expands globs deterministically
  (sorted) + dedups the input list; `classify_type` maps an extension/URL to the
  enum. `fux ingest --queue` renders it. Partial-failure-tolerant by construction —
  a `failed` row coexists with drafts.
- **Bounded depth-1 link discovery** ([fux/ingestfollow.py](fux/ingestfollow.py)) — the
  agent fetches the page HTML; `discover()` applies the fence: same-origin by default
  (`--cross-origin` widens), an extension allow-list (`ALLOW_EXT`; never
  executables/scripts/archives), a `--max` cap (raises `FollowError` —
  refuse-with-message, no silent truncate), depth-1 (it inspects one page, never
  recurses). `is_direct_file()` lets a direct file/spec URL skip discovery. Uses only
  `urllib.parse` (URL-string math, no socket).
- **Reduce-before-draft** ([fux/ingestreduce.py](fux/ingestreduce.py)) — operates on
  the agent's *extracted text* only (never a binary): per-type structure slicing
  (prose → headings + tables + rule passages; `xlsx` → schema + sample rows + formulas,
  **never the full grid**; `json/yaml/openapi` → contract keys, not example values),
  a rule-signal pre-filter reusing `recall._tokens`, boilerplate/page-number strip,
  and `changed_sections()` for incremental re-ingest. `reduce(..., full=True)` bypasses
  it; reports tokens before→after and files the saving via `cage_receipt` (fail-open).
- **CLI** ([fux/cli.py](fux/cli.py), [fux/cliquery.py](fux/cliquery.py)) — `ingest`
  (and the `scrape` alias) take N positional `targets` + `--follow-links`,
  `--cross-origin`, `--max N`, `--yes`, `--queue`, `--full`. `cmd_ingest` does the
  deterministic parts ($0): `--queue` renders the manifest, `--recheck` re-verifies a
  source, and with targets it prints the expanded/deduped source list + the skill
  pointer (drafting itself stays the agent's tokens).
- **Schema** ([schema.json](fux/data/schema.json)) — `source_type` enum extended
  additively with `docx`, `json`, `yaml`, `openapi` (now
  `url|pdf|xlsx|docx|txt|image|json|yaml|openapi`).
- **Skill** ([data/skills/ingest/SKILL.md](fux/data/skills/ingest/SKILL.md)) —
  multi-source loop, `--follow-links` discovery procedure, new extract branches
  (Word, JSON/YAML, **Swagger/OpenAPI** → per-endpoint/param/auth/deprecation rules
  with `--recheck` contract drift), reduce-before-draft step, and the queue-write step.
- **Guard** ([tests/test_no_llm_imports.py](tests/test_no_llm_imports.py),
  [test_ingest_batch.py](tests/test_ingest_batch.py)) — the `NETWORK` regex now bans
  `urllib.request`/`urllib.error` (not the socket-free `urllib.parse`); a dedicated
  test proves the three new modules import no parser/network/LLM library and stay
  offline/model-free on import.
- **Tests** ([test_ingest_batch.py](tests/test_ingest_batch.py), 36 cases) — batch
  glob-expand/dedup, mixed draft|failed queue + partial-failure tolerance + dedup by
  `source_hash`; follow-links depth-1/same-origin/allow-list/cap/direct-file-skip +
  cross-origin widening; reduce cuts tokens / `--full` bypass / xlsx never sends the
  full grid / contract slice / incremental changed-sections; Swagger contract drift via
  `--recheck`; trust flags round-trip with nothing auto-active.

### 2.20d Self-build + `--self` scope — ✅ (scrape-howto-cli-handoff.md §C/§4b, v0.12.0)

"fux explains fux" from fux's *real* code, not prose. The remaining piece of §C
after the v0.9.0 `fux how`/registry work:

- **Self-knowledge bundle** ([fux/selfbuild.py](fux/selfbuild.py)) — `fux self-build`
  runs fux's *own* `$0`, AST-only graph extraction (`graph.build` over `fux/**/*.py`)
  + resolves fux's `.fux/rules`, and writes a **pre-built footprint mirror** to
  `data/self/.fux/{out/graph.json, out/rules.json, out/INDEX.md, rules/, config.toml}`,
  shipped in the wheel. Hermetic (`use_global = false` — fux's rules only) and
  `meta.extractor` pinned to `python`/`stdlib-ast`, so it regenerates **byte-identically**
  from source regardless of whether the `[ast]` extra is installed.
- **`--self` scope** ([fux/cliutil.py](fux/cliutil.py) `scope_root`/`self_root`) — a
  pure root-swap: `query`/`path`/`explain`/`recall` ([fux/cligraph.py](fux/cligraph.py),
  [fux/cliquery.py](fux/cliquery.py)) read the bundle instead of the project, reusing
  every existing loader. Works in any repo with **no project `.fux/`**; `fux how` gains
  a self-doc pointer to it.
- **Packaging** ([pyproject.toml](pyproject.toml), [.gitignore](.gitignore)) — the
  bundle is committed (the `**/.fux/out/` ignore is negated for `data/self/`) and added
  to `package-data` so `--self` works on a plain `pip install`.
- **Tests** ([tests/test_selfbuild.py](tests/test_selfbuild.py)) — byte-identical
  regeneration; the committed bundle is **fresh** vs a rebuild (CI gate — a stale bundle
  fails); the config is hermetic; `explain --self`/`recall --self` answer from a temp dir
  with no footprint; the guard test ([test_no_llm_imports.py](tests/test_no_llm_imports.py))
  now covers `selfbuild` as `$0`/offline/model-free.

### 2.20e Decision capture — ✅ (decision-capture-handoff.md, v0.13.0)

Every concluded `/fux debate` or decision-council becomes a routed, tamper-evident
ADR. The *debating* is the host agent's tokens; the **capture** — format, seal, route
— is pure `$0`/deterministic harness.

- **Capture + routing** ([fux/decisioncapture.py](fux/decisioncapture.py), ≤100) —
  `build_adr` formats the verdict (`decision`/`why`/`crux`/`strongest_dissent`/
  `what_would_reverse`); `capture` seals it with `ratification.content_seal` (reusing
  [fux/constitution.py](fux/constitution.py)'s hash) + the transcript's `debate_hash`
  ([fux/provenance.py](fux/provenance.py)), and **routes by content**: `fux`/`anton`
  → full sealed ADR in `.fux/decisions/`; `elgar` (money) → a **link-only** record
  (`elgar_ref: elgar://decision/<id>`, no body).
- **Money firewall** (ADR 0001) — `capture-decision --route elgar` **refuses without
  `--yes`** (a money route is never silent), and `check_firewall` flags any fux-side
  elgar record that isn't link-only (residual body after heading + stub → breach),
  independent of the seal. A new always-blocking **`firewall`** finding kind
  ([fux/findings.py](fux/findings.py)) hard-blocks in any mode, like `tampered`.
- **Verification** ([fux/check.py](fux/check.py)) — `check_seals` raises `tampered` for
  any captured ADR whose `content_seal` no longer matches (ADRs are immutable);
  `check_firewall` enforces the link-only rule on every run.
- **Wiring** — `.fux/decisions/` added as a loader source dir
  ([fux/loader.py](fux/loader.py), [fux/paths.py](fux/paths.py)); schema gains
  `decided_by`/`method`/`route`/`elgar_ref` (additive); `capture-decision` in the
  registry + CLI ([fux/cliconstitution.py](fux/cliconstitution.py)); the debate skill
  ([data/skills/debate/SKILL.md](fux/data/skills/debate/SKILL.md)) captures on
  conclusion and requires money confirm.
- **Tests** ([tests/test_decision_capture.py](tests/test_decision_capture.py)) — fux
  route writes a full sealed ADR; money route is link-only (no body, only the link);
  editing a captured ADR trips `tampered`; a sealed-but-not-link-only elgar record trips
  a hard-blocking `firewall`; the guard test covers `decisioncapture` as `$0`/offline.

### 2.20f Connector ingestion — ✅ (batch-ingest-handoff.md §7, PR4, v0.14.0)

Jira/Confluence/GitHub as a connector source class. The **agent** pulls structured,
server-side-filtered data via MCP/API (the fallback ladder lives in the skill); **fux
never builds a client or calls an API** — the engine is only the deterministic, `$0`
fence + the same reduce → draft → review-queue → govern pipeline.

- **Guardrail** ([fux/ingestconnector.py](fux/ingestconnector.py), ≤60) — `plan()`
  validates `connector ∈ {github,jira,confluence}`, **refuses an unbounded query**
  (empty / `*` / `all` / `everything` → `ConnectorError`; explicit server-side filter
  mandatory), enforces the cap, carries a `--since` delta cursor, and marks every item
  **low-trust** (`trust: candidate` — a ticket/wiki/PR is not a spec). Imports nothing
  network/LLM.
- **CLI** ([fux/cli.py](fux/cli.py), [fux/cliquery.py](fux/cliquery.py)) — `fux ingest`
  gains `--connector`, `--query`, `--since`; `cmd_ingest`'s connector branch validates +
  prints the bounded plan + skill pointer (the agent pulls & drafts into the queue).
- **Schema** ([schema.json](fux/data/schema.json)) — `source_type` += `jira`/
  `confluence`/`github` (additive).
- **Skill** ([data/skills/ingest/SKILL.md](fux/data/skills/ingest/SKILL.md)) — the
  efficiency stack (server-side filter → `--since` delta → structure-slice → reduce/dedup,
  **GitHub first**), the fallback ladder (MCP → REST+PAT → export/`git clone` → CDP-JSON
  → DOM; probes last), and the low-trust queue-write step.
- **Tests** ([tests/test_ingest_connector.py](tests/test_ingest_connector.py)) — bounded
  query accepted; unbounded/empty/`*`/`all` refused; unknown connector + `max<1` rejected;
  `--since` carried; the CLI branch returns 0 on valid / 1 on unbounded; the guard test
  covers `ingestconnector` as `$0`/offline.

### 2.20g PII content gate probe — ✅ (constitution-enforcement / backlog item 5, v0.15.0)

Closes the residual gap: a stray PAN/Aadhaar in a non-plan `.py`/`.md` was only caught
by a local hook (bypassable via `--no-verify`, absent from CI). dante's BLOCK-tier
regexes, ported to a hand-rolled **stdlib** probe (no pip dependency on dante), wired
into the required `fux gate` CI job.

- **Probe** ([fux/piiscan.py](fux/piiscan.py), ≤100) — `BLOCK_PATTERNS` mirror dante's
  PAN / Aadhaar / account-id regexes; `scan_text`/`scan_file`/`scan` return
  `(path, line, kind, snippet)` hits in deterministic order. Plan/spec/handoff/decision
  docs are **exempt by path** (`is_exempt`); any line opts out with an inline `pii-allow`
  marker. Imports only `re` — no LLM, no network.
- **CLI** ([fux/clicmds.py](fux/clicmds.py), [fux/cli.py](fux/cli.py)) — `fux pii-scan
  [paths…]` scans the given paths or all git-tracked `.py`/`.md`
  ([fux/gitutil.py](fux/gitutil.py) `tracked_files`) and **exits 2** on a hit (blocks the
  gate), 0 clean.
- **Wall** ([.github/workflows/ci.yml](.github/workflows/ci.yml)) — `fux pii-scan` is a
  step in the `fux gate` job, so a hard identifier blocks the merge in CI, not just
  locally.
- **Tests** ([tests/test_pii_scan.py](tests/test_pii_scan.py)) — each identifier
  detected; clean text passes; the `pii-allow` marker + path exemption skip a line/file;
  the CLI exits 2 on a hit / 0 clean; the guard test covers `piiscan` as `$0`/offline.
  (The test's own example identifiers carry `pii-allow` markers so the gate doesn't flag
  the test file.)

### 2.20h Skill renderer (`tools/skillgen`) — 🟡 (renderer foundation)

The per-host skill artifacts were hand-authored per surface and drifted independently.
A build-time, stdlib-only renderer now emits them from one human-edited fragment set,
guarded against drift by `--check`. **Foundation scope:** the flagship `fux` skill only,
to three hosts; the other 10 skills and more hosts are follow-on packets. Full design in
[docs/skillgen.md](skillgen.md).

- **Renderer** ([tools/skillgen/gen.py](tools/skillgen/gen.py), ~210 lines, stdlib-only —
  `argparse`/`re`/`sys`/`tomllib`) — a self-contained renderer (no shared module with any
  other repo). `load_platforms` → `Platform` records; `_render_core` fills the
  body template's `@@FRONTMATTER@@`/`@@POINTER_FILE@@` slots (raises on any surviving
  `@@SLOT@@`); `check` byte-diffs the render against the committed artifacts **and** the
  blessed `expected/` snapshots; `bless` refreshes them. Deterministic: LF-normalized, one
  trailing newline, no clocks/random. **Never imported by the `fux` package at runtime.**
- **Manifest + fragments** ([tools/skillgen/platforms.toml](tools/skillgen/platforms.toml),
  `fragments/core/{core,copilot}.md`) — `claude` + `agents` share `core/core.md` (the
  breadth proof: one edit updates both, differing only by the always-on pointer file
  `CLAUDE.md` vs `AGENTS.md`); `copilot` renders its own `agent: ask` body. Each host's
  `description` (the firing trigger) is preserved **verbatim**.
- **Rendered artifacts** — `claude` → [fux/data/skills/fux/SKILL.md](fux/data/skills/fux/SKILL.md)
  (existing path, unmoved), `agents` → `fux/data/skills/agents/SKILL.md` (new, generic
  `~/.agents/skills` target), `copilot` → `fux/data/copilot/prompts/fux.prompt.md`
  (regenerated). **codex** is served by the `claude` artifact verbatim (copied by
  `fux setup`), so it is not a separate render target.
- **Drift wall** — `python -m tools.skillgen --check` runs in CI
  ([.github/workflows/ci.yml](.github/workflows/ci.yml) `skillgen-check` job) and a local
  pre-commit hook ([.pre-commit-config.yaml](.pre-commit-config.yaml)); the wheel/sdist
  `tools*` exclusion is tested.

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
  hash with a live transcript-drift check, the **recent debate transcripts** (newest first by
  mtime), and all current **violations grouped by severity** (blocking vs advisory). Read-only,
  $0, reuses the same `check` the gate runs; exits 2 if the apex has blocking findings.
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
  `.fux/out/critic.jsonl`. **Advisory-first (§7d, F1):** judgment fails are *suggestions*
  (`CriticResult.suggestions`) and do not block; only deterministic fails block by default.
  `critic_block_judgment` in `.fux/config.toml` (`true` or a list of ids) escalates a trusted
  judgment principle to blocking. `fux gate` **reports** (never blocks) ungoverned
  `important_globs` paths — the report-first coverage gate. (`cmd_ratify`/`cmd_critic` now live
  in [fux/cliconstitution.py](fux/cliconstitution.py), shrinking `clicmds.py`.)
- **Bootstrap rule** [`con-amendment`](../.fux/rules/con-amendment.md) — the founding amendment
  article (Phase 0), `tier: constitutional`, ratified with its genesis debate. **Now superseded
  by** [`con-amendment-v2`](../.fux/rules/con-amendment-v2.md) (F3) — the constitution's first
  amendment, landed by supersession (new id, `edges.supersedes: [con-amendment]`, predecessor
  deprecated + re-sealed, fresh debate) rather than in-place edit, dogfooding the rule. v2 adds the
  **"is this constitutional?" authoring test** (money/PII/audit/trust **and** never-changes), which
  `/fux debate` surfaces for `tier: constitutional` proposals. Both stay in
  `.fux/constitution.lock`; v1 remains on the record as immutable, sealed, deprecated evidence.

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
  → `fux import-memory`, confirm coverage of current files, then retire the legacy
  code-graph output + the migrated `docs/`.

Planned (engine, see [fux-plan.md §17.10–12](fux-plan.md)):

- ⬜ **PyPI packaging** — bundle `schema.json`/`hooks`/`global`/`skills` as package
  data, add a `fux setup` command, and a Trusted-Publishing release workflow →
  `pipx install fux-engine && fux setup`.

**Constitution layer — tracked Phase-2 follow-up (from the founding `con-amendment` debate's
disclosed implementation debt; one enforcement now has live evidence):**

- ⬜ **`supersedes:` edge check (HIGH — live evidence).** The engine should reject re-stamping a
  constitutional rule whose *body* changed without a declared supersession, and validate that a
  successor declares `edges.supersedes: [<old-id>]` **and** is itself `tier: constitutional`.
  *Why now:* the [`con-amendment` → `con-amendment-v2`](../.fux/rules/con-amendment-v2.md)
  amendment (F3) was landed by supersession **manually** — the human upheld the discipline the
  engine cannot yet enforce. Until this check exists, `fux ratify` would also accept an in-place
  body edit re-stamped under the same id (the laundering path). This is the concrete reason the
  check is the priority of the four.
- ⬜ **Predecessor → `deprecated` at ratification** of a successor (today done by hand + a
  re-ratify of the predecessor to re-seal its deprecated frontmatter — `status` is not in
  `_VOLATILE`, so deprecating a ratified rule changes its `content_seal` and must be re-stamped).
- ⬜ **Minimum-transcript-content check** (≥2 distinct reviewer positions, ≥1 sustained objection,
  a recorded tie-break) — today `debate_hash` accepts any recorded bytes.
- ⬜ **Constitutional-successor tier check** — a successor to a constitutional rule must itself be
  `tier: constitutional` + ratified, else supersession is a downgrade-laundering path.

These four land as a later supersession (`con-amendment-v3`) once built — single-concern, the way
v2 carried only the authoring heuristic.

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
