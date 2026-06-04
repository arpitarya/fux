# Fux — Implementation Status

> Engine **v0.1.0**. A portable, Claude-aware knowledge engine: one frontmatter
> substrate → derived index, graph, and memory views, with `$0` deterministic
> maintenance. This file tracks **what has shipped** and **what remains**, mapped
> to the design of record in [docs/fux-plan.md](docs/fux-plan.md).

**Legend:** ✅ done · 🟡 partial · ⬜ not started

---

## 1. Snapshot

| Area | Status | Notes |
|---|---|---|
| Core CLI surface (plan §9) | ✅ | 25 commands wired in [fux/cli.py](fux/cli.py) |
| Hooks (3 core + 2 optional) | ✅ | SessionStart, PostToolUse, Stop + opt-in UserPromptSubmit & capture |
| Rule schema + frontmatter parser | ✅ | Hand-rolled, stdlib-only ([fux/frontmatter.py](fux/frontmatter.py), [schema.json](schema.json)) |
| Layered resolution (global ⊕ packs ⊕ project) | ✅ | Precedence + conflict detection |
| Graph engine (AST extraction) | ✅ | Python via `ast`; JS/TS/Go/Rust intra- **and cross-file** `calls`; block-comment-aware sanitizer |
| Recall | ✅ | BM25-lite default; opt-in local re-rank **+ RRF hybrid** (lexical⊕semantic⊕graph) |
| Memory governance + capture | ✅ | TTL decay ([fux/governance.py](fux/governance.py)); opt-in capture queue ([fux/capture.py](fux/capture.py)) |
| Verify | ✅ | `check:` invariants + examples (JSON, inline `key=value`, scalar coercion) |
| Quality & health (`lint`/`stats`) | ✅ | Rule-quality lint + weighted health score ([fux/lint.py](fux/lint.py), [fux/stats.py](fux/stats.py)) |
| Enforcement (`gate`) | ✅ | CI / git pre-commit; exit 2 on blocking ([fux/gate.py](fux/gate.py)) |
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
| `fux check [--fix]` | ✅ | [fux/check.py](fux/check.py), [fux/fix.py](fux/fix.py) |
| `fux context` | ✅ | [fux/context.py](fux/context.py) |
| `fux recall "Q" [--top N] [--hybrid]` | ✅ | [fux/recall.py](fux/recall.py), [fux/hybrid.py](fux/hybrid.py) |
| `fux why <id>` | ✅ | [fux/cliquery.py](fux/cliquery.py) |
| `fux refs <file>` | ✅ | [fux/cliquery.py](fux/cliquery.py) |
| `fux new <type> <id> [--domain D]` | ✅ | [fux/cliquery.py](fux/cliquery.py) |
| `fux coverage` | ✅ | [fux/coverage.py](fux/coverage.py) |
| `fux verify` | ✅ | [fux/verify.py](fux/verify.py), [fux/vexamples.py](fux/vexamples.py) |
| `fux savings ["Q"]` | ✅ | [fux/savings.py](fux/savings.py) |
| `fux lint [--strict]` | ✅ | [fux/lint.py](fux/lint.py) |
| `fux stats` | ✅ | [fux/stats.py](fux/stats.py) |
| `fux gate [--install] [--strict-lint]` | ✅ | [fux/gate.py](fux/gate.py) |
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
applied identically to both sides):

- **Corpus** — active rule count, INDEX (Tier-1) tokens, average rule (Tier-2)
  tokens, and total governed-code tokens across distinct `code_refs` files.
- **Per lookup** (optionally for a query, via `recall`) — *without Fux* (read the
  governed file(s)) vs *with Fux* first-lookup (INDEX once + the rule) and later
  lookups (rule only, INDEX already in context), each with a savings multiplier.
- **Aggregate** — the same averaged over every documented topic (a rule with an
  existing governed file). Missing `code_refs` are excluded from the baseline.

Deterministic, `$0`, no LLM. Covered by [tests/test_savings.py](tests/test_savings.py).

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

Render contract covered by [tests/test_graphhtml.py](tests/test_graphhtml.py).

### 2.16 Skills — ✅ (plan §16)

Registered under `~/.claude/skills/` (installed by [install.sh](install.sh)):
`fux`, `fux-plan` (flagship, spec-driven requirements → design → tasks),
`fux-adr`, `fux-trace`, `fux-savings` (interpret the cost report → a next action),
and `fux-distill` (capture this session's decisions as durable `memory`/`adr`
entries — the memory-replacement loop, human-confirmed). Guides:
[docs/spec.guide.md](docs/spec.guide.md), [docs/rule.guide.md](docs/rule.guide.md).
`plan`/`adr`/`distill` author via the LLM in-session; `trace`/`savings` are pure
`$0`. All ride the current session (no background spend).

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
- [pyproject.toml](pyproject.toml) (v0.1.0, stdlib-only, `[embeddings]` extra),
  [justfile](justfile), global seed in [global/](global/).

### 2.20 Tests — ✅ (80 tests)

[tests/](tests/): resolution, frontmatter, globs, check/fix, recall/build/verify,
embed/rerank, schema/scaffold/init, cross-language + **cross-file** call edges
([test_astextract.py](tests/test_astextract.py), [test_crossfile_calls.py](tests/test_crossfile_calls.py)),
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
([test_parity_import.py](tests/test_parity_import.py)).
Run with `python -m pytest` (Python ≥ 3.11).

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

---

## 5. Key references

- Design of record: [docs/fux-plan.md](docs/fux-plan.md)
- Architecture: [docs/architecture.md](docs/architecture.md)
- CLI reference: [docs/cli.md](docs/cli.md)
- Implementation deltas: [docs/implementation-notes.md](docs/implementation-notes.md)
- Comparisons: [docs/recall-engine.compare.md](docs/recall-engine.compare.md),
  [docs/global-rules-home.compare.md](docs/global-rules-home.compare.md)
