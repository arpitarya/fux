# Fux vs Graphify — parity matrix & "safe to remove graphify" bar

**Purpose:** decide, on evidence, when Fux covers enough of what you use Graphify
for that Graphify can be uninstalled — *for your use case*, not in the abstract.

## 0. The reframe (read this first)

"Achieve parity, then remove graphify" bakes in an assumption worth challenging:
**that Fux should become Graphify.** It shouldn't. They are not the same product:

- **Graphify** is an LLM-backed *semantic knowledge/memory graph* over **any** media
  — code, docs, PDFs, images, video/audio (Whisper), YouTube — across ~20 AI
  assistants. The graph **is** the product. It ships as a YC-backed tool with
  third-party deps (tree-sitter, NetworkX), needs an API key for headless
  extraction, and its edges are LLM-inferred.
- **Fux** is a `$0`, stdlib-only, **deterministic** engine whose product is
  *governed knowledge-with-why* — rules, seals, a constitution, drift detection.
  The graph is a **view**, not the point. No LLM on any maintenance path (a guard
  test enforces it).

So there are really **two questions**, and only the first is a true parity call:

1. **Code-and-rules graph/query use** (what most engineers use graphify's graph
   for day-to-day): map the repo, query relationships, find god nodes. **Here Fux
   can reach parity and replace graphify.** This matrix scores it.
2. **Semantic media-memory use** (transcribe a video, extract a PDF diagram, build
   a cross-media second brain, drive it from Cursor/Aider/Gemini): **Fux should
   *not* absorb this** — it needs an LLM and third-party deps, which breaks Fux's
   constitution. If you rely on this, keep graphify (or a purpose-built tool);
   don't contort Fux.

**Recommendation:** the removal bar should be scoped to #1. Decide whether your
actual graphify usage is #1 or #2 before chasing parity. If it's mostly #1, the gap
is small and closeable (see §3). If #2 matters, "remove graphify" is the wrong goal.

## 1. Scoring method

Each capability is scored **Fux** and **Graphify** on 0–3 (0 absent · 1 partial ·
2 solid · 3 best-in-class), with a **weight** reflecting how much *you* rely on it
for the #1 use case. "Safe to remove" = Fux ≥ Graphify−1 on every **must-have**
(weight 3) row, and no must-have Fux score is 0. Adjust weights to your reality —
they're an argument, not gospel.

## 2. The matrix

| # | Capability | W | Fux | Graphify | Evidence / note |
|---|---|:-:|:-:|:-:|---|
| **Core graph — the parity battleground** |
| 1 | Multi-language symbol/call extraction | 3 | 2 | 3 | Fux: Python `ast` + brace-heuristic (JS/TS/Go/Rust), tree-sitter via `[ast]`. Graphify: tree-sitter across far more langs. |
| 2 | Cross-file / cross-lang edges | 3 | 2 | 3 | Fux `_crossfile_calls` + `_xref` (references). Graphify richer relation vocab (imports/inherits/embeds/…). |
| 3 | Edge confidence labels | 2 | 3 | 3 | **Both.** Fux stamps EXTRACTED/INFERRED + weight (references=0.25), down-weighted in clustering. `fux/graph.py`. |
| 4 | Community detection | 2 | 2 | 2 | Fux: deterministic label-propagation. Graphify: NetworkX louvain-style. Tie. |
| 5 | Centrality / god nodes | 2 | 2 | 2 | Fux: PageRank + degree (`fux report`). Graphify: god-node analysis. Tie. |
| 6 | Query / path / explain / impact | 3 | 2 | 2 | Fux: `query`/`path`/`explain`/`impact`. Graphify: `query`/`path`/`explain` + query log + work-memory. |
| 7 | Interactive HTML viewer | 2 | 2 | 2 | Fux "Solar Terminal" (Barnes–Hut, culling). Graphify HTML. Both degrade >5k nodes (see scaling handoff). |
| 8 | Machine graph output (JSON) | 2 | 2 | 2 | Both emit `graph.json`. Tie. |
| 9 | Extra exports (SVG/GraphML/Neo4j/Cypher/Mermaid) | 1 | 1 | 3 | **Graphify wins:** SVG, GraphML (Gephi/yEd), Neo4j + FalkorDB push, callflow-HTML. Fux: HTML/JSON/report only. |
| **Scale & freshness** |
| 10 | Incremental / cached rebuild | 3 | 0 | 3 | **Gap.** Fux `graph.build()` re-extracts everything each run. Graphify: versioned per-file AST cache + semantic cache + `affected.py`. → *scaling handoff*. |
| 11 | Large-graph handling (10k–100k) | 3 | 1 | 2 | Both struggle; graphify has minhash dedup + SCIP ingest to offload. Fux has nothing yet. → *scaling handoff*. |
| 12 | Cross-repo / global graph | 2 | 0 | 2 | Graphify `~/.graphify/global-graph.json` + manifest. Fux is per-project. → *org handoff*. |
| **Ingestion / connectors** |
| 13 | Docs / markdown import | 2 | 2 | 2 | Fux `import`/`fetch-rules`. Graphify semantic doc extraction. Tie (different: det vs LLM). |
| 14 | PDF / xlsx / docx | 1 | 1 | 2 | Fux via `ingest` skill (host-agent tokens). Graphify LLM extraction, `[pdf]` extra. |
| 15 | Swagger / OpenAPI | 2 | 2 | 1 | **Fux wins:** first-class `ingest` OpenAPI → per-endpoint draft rules; `source_type: openapi`. |
| 16 | DB introspection | 1 | 0 | 2 | Graphify `pg_introspect`. Fux none. |
| 17 | Jira / Confluence / wiki | 2 | 1 | 2 | Fux: `source_type` enum has `jira`/`confluence` but no connector. Graphify: `google_workspace`, `wiki` export, `mcp_ingest`. → *org handoff*. |
| 18 | Images / video / audio | 1 | 0 | 3 | **Graphify only** (Whisper, yt-dlp). Out of scope for Fux (LLM/deps). Use-case #2. |
| **Agent surface** |
| 19 | Claude Code integration | 3 | 3 | 3 | Fux: hooks + skills + MCP. Graphify: skill + PreToolUse hook. Tie. |
| 20 | Codex / Copilot | 2 | 2 | 2 | Fux `hooks` + skillgen (codex/copilot). Graphify skill files. Tie. |
| 21 | Cursor / Kiro / Gemini / Aider / Amp / OpenCode | 2 | 0 | 3 | **Graphify wins big:** per-platform skill files + installs for ~20 tools. → *multi-assistant handoff*. |
| 22 | VS Code extension | 1 | 0 | 1 | Graphify has a `vscode install` (skill/steering, not a true extension). Fux none. → *multi-assistant handoff*. |
| 23 | MCP server | 2 | 2 | 2 | Both expose stdio MCP. Tie. |
| **The layer graphify does not have** |
| 24 | Rules-with-why / governance | 3 | 3 | 0 | **Fux only.** The whole point — red-pipe notes, `why`, constitution. |
| 25 | Deterministic verify / seal / drift | 3 | 3 | 0 | **Fux only.** AST seal, `check`, `verify --fuzz`, `unsealed`. |
| 26 | `$0` / no-LLM / stdlib-only | 3 | 3 | 0 | **Fux only.** Graphify needs an LLM + tree-sitter/NetworkX. |
| 27 | Cost measurement (`savings`) | 1 | 3 | 1 | Fux prices the token win in dollars. Graphify has a token benchmark. |

## 3. Verdict — where you stand today

For **use case #1 (code+rules graph/query)**, the *only* must-have (W3) rows where
Fux trails Graphify by more than one point are:

- **#10 incremental/cached rebuild (Fux 0 vs 3)** — the real blocker. At your 23k
  nodes this is felt as "fux has a hard time." Closeable → *graph-scale handoff*.
- **#21 broad multi-assistant surface (Fux 0 vs 3)** — only matters if you drive
  fux from Cursor/Kiro/Gemini/etc. If you live in Claude Code, this is W0 for you.

Everything else on the must-have list is a tie or a Fux win (governance rows 24–26
are Fux-only and are *why* you'd keep fux over graphify at all).

**So: you are ~2 fixes away from removing graphify for use case #1** — land the
incremental graph (#10/#11) and, if you use non-Claude assistants, the
multi-assistant surface (#21/#22). You do **not** need feature-17/18/9/16 to remove
graphify unless you specifically use those.

**You are *not* close, and should not try, to replace graphify for use case #2**
(media/video/second-brain across 20 tools) — that's a different product and it
would cost Fux its constitution.

## 4. The removal checklist (make it binary)

Uninstall graphify once ALL of these are true *for the way you actually work*:

- [ ] Fux graph rebuild on your 23k-node repo is incremental and completes in the
      time budget you'll tolerate (target from scaling handoff, e.g. <10s warm).
- [ ] Every graphify query you actually run has a `fux` equivalent you've verified
      on the same repo (this is what the runnable `fux parity` command proves —
      see the parity-command handoff).
- [ ] If you use non-Claude assistants: fux is installed and query-first-wired on
      each one you use (multi-assistant handoff).
- [ ] You've confirmed you do **not** depend on graphify's media/video/global-graph
      /GraphML/Neo4j paths — or you've accepted keeping a separate tool for those.
- [ ] The `fux parity` command reports ≥ your chosen threshold (e.g. 90%) coverage
      of your logged graphify queries, run head-to-head.

## 5. Feeds into

- Runnable scoring → **handoff-01-parity-command** (`fux parity` head-to-head).
- Row 10/11 → **handoff-03-graph-scale** (incremental + LOD + SCIP).
- Row 12/16/17 → **handoff-04-org-connectors**.
- Row 21/22 → **handoff-02-multi-assistant**.
- Rows 9/18 and Obsidian → **graphify-obsidian-inspiration** (what to borrow vs leave).
