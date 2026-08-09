# Fux roadmap — implementation spec (debate-hardened)

**Supersedes the flat treatment of** handoff-01..04. Those remain the detailed
per-item specs; this document is the **master implementation plan** after an
adversarial pass on all four. It re-scopes, splits, re-prioritizes, and names the
one question that gates each build. Read this first; drop into the individual
handoffs for full field-level detail.

## 0. The headline the debate forced

The four items are **not equal in value or risk**, and sequencing them as peers was
the mistake. Ranked by real ROI *today*:

| Rank | Item | Why | Build now? |
|---|---|---|---|
| 1 | **03a Viewer LOD / ego-graph** | The actual 23k-node pain is browser rendering. No determinism risk. | **Yes** |
| 2 | **03b Incremental cache** | Real pain *if* the profiler proves extraction dominates. | **Only after profiling** |
| 3 | **01 Parity command** | Enables the graphify-removal decision — *if* you have a real query log. | **Only if log exists** |
| 4 | **04a Connectors (Jira/Confluence)** | Mostly a skill fragment + MCP; OpenAPI already done. | Small; do when needed |
| 5 | **02 Multi-assistant** | Speculative unless you use those assistants. | Scope to what you use |
| 6 | **04b Cross-repo global graph** | Org-scale navigation; speculative without a multi-repo need today. | Defer until the need is real |

**One gate to answer before anything:** three of these six are contingent
(profiler result, graphify-log existence, which assistants you use, multi-repo
need). Answer §7 first; it deletes 2–3 of these from the plan outright.

---

## 1. Item 03 — Graph scale (SPLIT into 03a / 03b / 03c)

Detailed spec: `docs/handoff-03-graph-scale.md`. The debate splits it into three
independently-shippable PRs and reorders them.

**Debate verdict.** Strongest item, but bundled three features as one and buried the
crux. The crux: **determinism (byte-identical `graph.json`) is in tension with
incrementality** — `community.detect()` (label propagation) and `graphquery.pagerank()`
are *global* passes over all edges. If you re-extract only changed files but must still
run clustering + PageRank globally to stay deterministic, the cache saves extraction
time but **not** the clustering/centrality time — which may be the dominant cost at
23k nodes. So the incremental cache is not obviously the fix; the profiler must decide.

**03a — Viewer LOD + ego-graph (ship first, no determinism risk).**
- Goal: the `graph.html` viewer never renders 23k nodes at once. Default to
  community-collapsed above a threshold; make an **ego-graph** (1–2 hops around a
  focused rule/file, driven by `fux query`/`explain`) the primary interaction.
- Touches only `fux/assets/graph_boot.js` + `graph_template.html`. Zero engine/
  determinism impact. Highest UX-per-risk of the whole roadmap.
- DoD: large `graph.html` loads collapsed and stays smooth; ego-expansion works.

**03b — Incremental extraction cache (contingent on the profiler).**
- **Do not build until `fux build --profile` on a real 23k-node repo proves that
  *extraction* (not clustering/PageRank) is the dominant cost.** If clustering
  dominates, this PR is deferred/redesigned, not built.
- If built: per-file cache keyed by `sha256(bytes)+extractor fingerprint`, versioned
  dir, stale sweep (graphify's `cache.py` pattern); `affected`-style recompute reusing
  `impact`'s traversal; `--force`/`--full` bypass.
- **Hard invariant:** cached/incremental build == full build, **byte-identical** —
  ship the proving test. On any inconsistency, fall back to full rebuild.

**03c — SCIP/LSIF ingest (opt-in extra, defer).**
- Correctly deferred. Only if 03a/03b don't hit budget, or for genuinely huge/polyglot
  repos. Behind a `[scip]`/`[ast]`-style extra; index is user-generated, never by Fux.

**Sequence:** 03a → profile → (03b if justified) → 03c if still needed.

---

## 2. Item 01 — Parity command (`fux parity`)

Detailed spec: `docs/handoff-01-parity-command.md`.

**Debate verdict.** Right idea, weak oracle, hard dependency. Three corrections:

1. **The oracle is honest coverage, not correctness.** Scoring "fux returned a
   non-empty result for this logged query" measures *coverage*, not whether the answer
   was *right* — a tool returning junk for every query scores 100%. The command must
   label its number "coverage, not correctness," apply a relevance floor (result must
   overlap the query's corpus), and never imply semantic parity.
2. **Kill the vanity sub-score.** "Two sub-scores" is right in shape, but the *fux-only
   capability count* does nothing for the **removal** decision — that decision hinges
   solely on graph-parity for the queries you actually run. Demote fux-only to a
   one-line footnote (reassurance), don't compute it as a headline metric.
3. **Gate the whole build on the log.** Without a real
   `~/.cache/graphify-queries.log`, this degrades to scoring a static manifest — which
   is just the parity matrix you already have. **If you don't have a rich graphify
   query log, don't build the command; use the matrix.** (§7 Q2.)

**Right-sized DoD (only if log exists):** `fux parity --from-log` replays the log,
reports per-query hit/miss with a relevance floor, tags media/video queries as
out-of-scope, prints one coverage % + a gap list, `--json` for the removal checklist.
`$0`, stdlib, graphify invoked only as an optional subprocess.

---

## 3. Item 02 — Multi-assistant

Detailed spec: `docs/handoff-02-multi-assistant.md`.

**Debate verdict.** Lowest ROI; half-speculative. Building Kiro / Copilot-VS-Code
steering *on spec* is the OSS breadth trap — for platforms without payload hooks it
degrades to a static AGENTS.md nudge a user could hand-write in two minutes, and its
value is zero unless *you* use that assistant. Correction:

- **Name your real assistants first (§7 Q3).** Scope the build to exactly those.
  Likely reality: Claude Code (already wired) + maybe Cursor. If so, 02 collapses to
  "verify Claude Code + add Cursor," and Kiro/Copilot-VS-Code are **deferred**, not built.
- Keep the **architecture** as-is (extend `skillgen` `platforms.toml` + fragments;
  extend `fux hooks` flags) — that's correct and contains config-drift blast radius.
  Just don't render surfaces nobody uses.
- Cowork + true VS Code extension stay gated as open questions (already correct).

**Right-sized DoD:** for each assistant *you actually use*, `fux hooks install
--<surface>` writes native steering + any supported hook, query-first, generated (not
hand-authored), `--check`-guarded. Everything else deferred with a one-line reason.

---

## 4. Item 04 — Org connectors + global graph (SPLIT into 04a / 04b)

Detailed spec: `docs/handoff-04-org-connectors.md`. The debate splits this hard —
these are two unrelated features stapled together.

**Debate verdict.**

**04a — Connectors (Jira / Confluence / Swagger), right-sized DOWN.**
- The engine barely changes — "connectors ride the skill" means the work is a skill
  fragment + provenance fields + (preferably) an existing MCP for auth. **OpenAPI
  already works.** Jira/Confluence are ~a day each, not a subsystem. The handoff
  overstated the engineering; treat 04a as small.
- **Fix the silent-staleness trust gap.** Ingested governance "why" (a rule sourced
  from a Confluence policy page) rots when the page changes, but `--recheck` is behind
  the `[scrape]` extra and off the `check` path — so a stale, wrong "why" sits there
  looking authoritative. That's worse than no rule. **Ingested governance content must
  carry a *visible* staleness signal** (e.g. a lint/`check` advisory that a
  `source_type: jira|confluence` rule hasn't been re-checked in N days), not a purely
  opt-in one. This is the one real design change in 04a.
- DoD: Jira/Confluence ingest → draft rules with provenance; read-only; nothing
  auto-activates; visible staleness advisory for source-backed governance rules.

**04b — Cross-repo global graph (separate handoff, gated).**
- Unrelated to connectors — it's org-scale *navigation*, merging per-repo `graph.json`
  into `~/.fux/global-graph.json` (graphify's `global_graph.py` shape). **Gate on §7
  Q4:** do you have a multi-repo need *today*? If not, defer — it's speculative.
- DoD (when justified): deterministic merge + manifest, corrupt-manifest backup, a
  query path across the union. `$0`.

---

## 5. Cross-cutting non-negotiables (all items)

Unchanged and binding on every PR:

- `$0`, stdlib-only, deterministic; **no LLM on any maintenance path** (fetch/extract
  ride the host-agent skill, never `build`/`check`).
- Determinism is sacred where graph output is touched (03): byte-identical `graph.json`.
- Draft-only ingestion; nothing auto-active, nothing auto-constitutional (04).
- Generated skill artifacts, never hand-authored; `skillgen --check` guards it (02).
- No new required runtime deps; network/heavy paths behind opt-in extras.
- Docs are part of done (plan + implementation + cli + README + whats-new per each
  handoff's §9.5); CLAUDE.md/AGENTS.md edits **proposed**, never silently applied.

## 6. Corrected build sequence

1. **03a viewer LOD/ego-graph** — do now; lowest risk, highest UX ROI.
2. **Profile** (`fux build --profile`, 23k repo) — decides 03b's fate.
3. **03b incremental cache** — only if the profiler justifies it.
4. **01 parity** — only if you have a graphify query log (§7 Q2).
5. **04a connectors** — small; when you actually need Jira/Confluence ingest.
6. **02 multi-assistant** — scoped to the assistants you name (§7 Q3).
7. **04b global graph** / **03c SCIP** — deferred until a real need appears.

Each is its own branch → PR → human-gated merge (per
`docs/prompt-00-orchestrator.md`; the wall forbids reviewer == author).

## 7. Gate questions — answer these before any code (they delete work)

1. **03b:** on your real 23k-node repo, does `fux build --profile` show *extraction* or
   *clustering/PageRank* as the dominant cost? (If clustering — don't build the cache as
   designed.)
2. **01:** do you have a rich `~/.cache/graphify-queries.log` from real graphify use?
   (If no — skip the parity command; the matrix is enough.)
3. **02:** which assistants do you *actually* use beyond Claude Code? (Build only those.)
4. **04b:** do you have ≥2 repos where cross-repo navigation matters *today*? (If no —
   defer the global graph.)

Answering these honestly likely removes 2–3 items from the near-term plan — which is the
point. The debate's net: **do 03a now, profile, and let the answers above decide the
rest** rather than building all four.
