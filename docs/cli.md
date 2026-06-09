# Fux CLI reference

Every command is deterministic and `$0` — no LLM calls (plan §9). Run them from
anywhere inside a project that has a `.fux/` footprint (the engine walks up to
find it), except `fux init` which scaffolds one in the current directory.

> For worked examples and explanations of every capability (with real output), see
> the **[complete guide → docs/guide.md](guide.md)**.

| Command | What it does | Cost |
|---|---|---|
| `fux init [--recall]` | Scaffold `.fux/` footprint, wire the 3 core hooks into `.claude/settings.json`, and drop Claude/Codex/Copilot pointers (`CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`). `--recall` also wires the optional UserPromptSubmit recall hook. | $0 |
| `fux build [--full]` | Regenerate `INDEX.md` + `rules.json` + graph + `NARRATIVE.md`. Graphs files matching `graph_globs` (broader than `important_globs`); `--full` graphs every non-ignored file. | $0 |
| `fux check [--fix]` | Validate schema, dead `code_refs`, git-staleness, and conflicts; write `DRIFT.md`. Also raises a non-blocking `extractor-drift` advisory when `graph.json` was built with a different graph backend than is installed locally (the optional `[ast]` tree-sitter extra). `--fix` applies mechanical repairs (drop dead refs, bump `updated`). Exit 2 under `strict` mode with blocking findings. | $0 |
| `fux context` | Emit the compact Tier-1 INDEX (global ⊕ packs ⊕ project) — the SessionStart injection. | $0 |
| `fux recall "Q" [--top N] [--hybrid] [--expand]` | **BM25F** lexical retrieval (per-field length-normalised). `--hybrid` RRF-fuses lexical ⊕ local-semantic ⊕ graph proximity; `--expand` widens the query with glossary synonyms + 1-hop `related` neighbours. All `$0`. | $0 |
| `fux why <id> [--history]` | Explain a rule: rationale + linked code + edges + invariant + body. `--history` shows how the *why* evolved (git log over the rule file, `--follow`). | $0 |
| `fux seal [ids…] [--all]` | Bind rules to a normalized-AST fingerprint of their `code_refs` (proof-carrying rules). `fux check` then flags `unsealed` when the governed code changes *structure*; re-affirm by re-running `seal`. | $0 |
| `fux refs <file>` | Reverse lookup — which rules govern this file. | $0 |
| `fux new <type> <id> [--domain D]` | Scaffold a schema-valid stub from a template into the right directory for its type. | $0 |
| `fux coverage` | % of "important" code files (config globs) with at least one governing rule; lists the uncovered. | $0 |
| `fux verify [--fuzz]` | Run invariant `check:` assertions against verification data (`verify_cmd:` / `.fux/verify/<id>.json`). Skips when no data. `--fuzz` perturbs numeric example inputs to boundaries and flags unguarded div-by-zero. | $0 |
| `fux savings ["Q"] [--top N] [--reset]` | Estimate the token-cost win — measured from real file sizes (≈4 chars/token): INDEX + rule corpus + governed-code totals, and a without-Fux vs with-Fux per-lookup comparison (pass a query to cost a specific lookup). With `cost_tracking = true`, also prints the **cumulative** savings ledger (`.fux/cost.json`); `--reset` clears it. | $0 |
| `fux lint [--strict]` | Rule *quality* (complements `check`'s structure): `no-why`, `no-code-refs`, `dangling-edge`, `no-provenance`, `stub-body`. Advisory; `--strict` exits 1. | $0 |
| `fux stats` | Knowledge-health dashboard: weighted score (coverage 40 · verify 30 · authoring 30 − drift) + corpus breakdown + every signal. | $0 |
| `fux mine [--min-sites N]` | Surface *candidate* rules latent in the code (first miner: magic numbers repeated across ≥N sites) as drafts to confirm — never auto-authored. | $0 |
| `fux gate [--install] [--strict-lint]` | CI / git pre-commit enforcement: rebuild views, then exit 2 on blocking `check`/`verify`. `--install` writes the pre-commit hook. | $0 |
| `fux mcp` | Serve the read paths + `query`/`trace`/draft-`new` to agents over MCP (stdio JSON-RPC, stdlib-only). | $0 |
| `fux capture [--list] [--clear]` | Session observation queue (changed files, governed vs uncovered) that `fux distill` consumes. Wired into the Stop hook when `capture = true`. | $0 |
| `fux serve [--port N]` | Local `http.server` dashboard: the `stats` health summary + links to `graph.html`/reports. | $0 |
| `fux import <path…> [--type T] [--domain D] [--force]` | Ingest existing markdown files/dirs as `narrative` (default) entries — the one-pass `docs/` migration. | $0 |
| `fux import-memory [--scope shared\|personal] [--force]` | Mirror Claude's home-dir `memory/*.md` for this project into `.fux/memory/<scope>/`. | $0 |
| `fux parity` | Decommission readiness: coverage of current source files by the graph, `docs/` not yet `narrative` (minus `conventions`/`guardrails`/`parity_stay`), home-memory not yet imported; flags a stale `graphify-out/`. Exit 1 until READY. | $0 |
| `fux tour` | Emit an ordered `ONBOARDING.md` reading path from the rules. | $0 |
| `fux query "Q" [--depth N]` | Anchor on rules matching Q, then traverse the merged graph N hops (the graphify-replacement query). | $0 |
| `fux path <a> <b>` | Shortest path between two graph nodes (rules, files, or symbols). | $0 |
| `fux explain <term>` | A graph node + its community + neighbours. | $0 |
| `fux impact <file>` | Downstream blast radius of changing a file: invariants to re-verify, governing rules whose *why* may go stale, and dependent caller files (precise `calls` split from loose `references`). | $0 |
| `fux components [--kind ...] [--scope P] [--json]` | The design-system registry + data-binding catalog: UI components with their prop fields, data hooks (`use*`), and DTO shapes — so a generated component composes from real primitives and binds to real data (the §18.3 Orff-runtime prerequisite). `--json` for machine/Orff use. | $0 |
| `fux validate-spec <file> [--json]` | The mount-time guardrail (§18.3.3): validate a generated declarative UISpec against the registry — rejects unknown components, undeclared props, and unknown data hooks. Exit 2 on violations. | $0 |
| `fux feedback [--record FILE]` | The generation learning loop (§18.4): summarise on-the-fly compose outcomes (acceptance rate + top rejection reasons); `--record -` appends one outcome from JSON on stdin. | $0 |
| `fux report` | Write `GRAPH_REPORT.md` — god nodes (degree) + **chokepoints (PageRank centrality)** + community structure. | $0 |

`fux build` also writes `GRAPH_REPORT.md` and tags every graph node with a
**community** index (deterministic label propagation); `graph.html` has a
*colour: type ⇄ community* toggle. The graph carries `governs` (rule→code),
`contains` (file→symbol), `calls` (intra-file — Python via `ast`, JS/TS/Go/Rust
via a brace-matched heuristic), and `references` (cross-file/cross-language)
edges.

### Internal hook entrypoints

Wired by `fux init`, not for direct use:

| Command | Hook event | Behaviour |
|---|---|---|
| `fux context` | SessionStart | Prints the INDEX to stdout (injected as context). |
| `fux hook-touch` | PostToolUse (Edit\|Write) | Reads the event JSON; if an edited code file is governed by a rule not edited this session, prints a reminder. Marks edited rule files so they are not nagged. |
| `fux hook-check` | Stop | Runs `check`; in `fix` mode applies mechanical repairs and reports the rest; in `strict` mode exits 2 on blocking findings. |
| `fux hook-recall` | UserPromptSubmit (opt-in) | Reads the prompt; injects the top recalled rules. |

### Skills (workflows that ride the current session)

`plan`/`adr` call the LLM in-session (no background spend); `trace`/`savings` are
pure `$0` traversal/measurement.

| Command | What |
|---|---|
| `fux plan "<request>"` | Spec-driven: requirements → design → tasks, each a durable Fux entry. See [spec.guide.md](spec.guide.md). |
| `fux adr "<decision>"` | Capture an architecture decision as an `adr` entry. |
| `fux trace "<feature>"` | Walk the merged graph to explain how a feature spans modules ($0 traversal). |
| `fux savings ["<question>"]` | Interpret the measured token-cost report and turn it into a next action ($0). |
| `fux distill ["<focus>"]` | Capture this session's durable decisions as `memory`/`adr` entries — human-confirmed, scoped. |

### MCP server (`fux mcp`)

A stdlib-only Model Context Protocol server over stdio (newline-delimited JSON-RPC
2.0). Run it from inside a project and register it with an MCP client:

```bash
claude mcp add fux -- fux mcp          # exposes recall/why/refs/coverage/savings/stats/context
```

Tools published: `fux_recall`, `fux_why`, `fux_refs`, `fux_coverage`,
`fux_savings`, `fux_stats`, `fux_context`, `fux_query`, `fux_trace`, and
draft-only `fux_new` — each deterministic, `$0`, no LLM.

### Environment overrides

| Var | Overrides |
|---|---|
| `CLAUDE_CONFIG_DIR` | `~/.claude` base (engine, global, packs, schema). |
| `FUX_GLOBAL` | Global rules dir (default `~/.claude/fux/global`). |
| `FUX_PACKS` | Packs dir (default `~/.claude/fux/packs`). |
| `FUX_SCHEMA` | `schema.json` path. |
| `FUX_PYTHON` | Interpreter the hook wrappers use when `fux` is not on PATH. |

### Optional extras

All off by default — Fux is `$0` and stdlib-only without them. None is ever required,
and none calls an LLM.

| Extra | Install | What it adds |
|---|---|---|
| `embeddings` | `pip install fux-engine[embeddings]` | Local sentence-transformers re-rank for `recall` (gated on `recall_rerank`); falls back to a $0 char-trigram cosine when absent. |
| `ast` | `pip install fux-engine[ast]` | Real **tree-sitter** ASTs for JS/TS/Go/Rust graph extraction instead of the brace heuristic — same node/edge schema, more accuracy. `fux build` records the active backend in `graph.json` `meta.extractor`; `fux check` flags `extractor-drift` if a committed graph was built with a different backend, so the graph stays reproducible across machines. |
| `pdf` | `pip install fux-engine[pdf]` | `.pdf` text extraction for `fux fetch-rules`. |
