# Compare docs

**Standing pattern (Arpit's rule):** whenever a decision has multiple viable options,
write a *compare doc* here before building — debate, matrix, grounded references, and
a **proposed verdict** Arpit accepts or overrides. Follow the format of the existing
docs (verdict block → context → options → matrix → analysis → references → additional
things to look into). Each accepted verdict then gets its ADR in [`../adr/`](../adr/).

## Decided (2026-07-20) — accepted verdicts

- [`query-engine.compare.md`](query-engine.compare.md) — ✅ **Staged hybrid, all
  `$0`/no-external-model.** v1 BM25F → v2 add bundled static embeddings fused with RRF
  → v3 agent-facing ask/reply/explain. SPLADE + cross-encoders noted, deferred (out of
  size budget).
- [`query-output.compare.md`](query-output.compare.md) — ✅ **Ranked passages default;
  `--files` locator; `--answer` = extractive synthesis (bundled model + TextRank), no
  external LLM.**
- [`ingest-strategy.compare.md`](ingest-strategy.compare.md) — ✅ **Two-tier `fux
  ingest`** (inferred by default, advanced on demand / agent-triggered), a manifest of
  inferred files, config-driven per-type source dirs.
- [`packaged-model.compare.md`](packaged-model.compare.md) — ✅ **Bundled ≤10 MB static
  embedding model** (Model2Vec/Potion-class, distilled offline, quantized),
  **pure-stdlib inference — numpy resolved: not used**; extractive (not generative)
  synthesis.

Ingest extensions accepted 2026-07-20/21: per-file **traceability frontmatter**,
**library-first API + agent skill**, **link/attachment crawling** (depth-capped,
fenced `--web`), and **CDP rendered-page ingestion** (`render = "cdp"`, hand-rolled
stdlib WebSocket client, user's own Chrome).

- [`cli-surface.compare.md`](cli-surface.compare.md) — ✅ **`fux ask` / `fux find` /
  `fux answer`** (verb per intent; `--json`/`--explain` modifiers). Accepted
  2026-07-21.
- numpy follow-up resolved 2026-07-21: **vendoring numpy is not possible** (C
  extensions, platform-locked binaries — evidence in the packaged-model doc);
  pure-stdlib inference stands.

- [`agent-integration.compare.md`](agent-integration.compare.md) — ✅ **files + hooks
  from one generator** (AGENTS.md canonical + tool-native pointers + Claude/Kiro
  hooks; MCP deferred). Accepted 2026-07-21, plus: **one `SKILL.md` (Agent Skills
  open standard, 32+ tools incl. Copilot/Kiro) instead of per-tool skills** —
  `fux-query` + `fux-ingest` skills ship with the package.
- **`fux setup`** — ✅ single setup command, **interactive wizard + full flag coverage
  + `-y`** (accepted 2026-07-21 as `fux init`, renamed to `fux setup` same day; see
  [`cli-surface.compare.md`](cli-surface.compare.md)).

Sub-decisions **resolved 2026-07-21** (research in
[`query-engine.compare.md`](query-engine.compare.md)): **no bundled reranker** (RRF
only — cross-attention needs ~80 MB-class models, 8× over budget; revisit only if the
Anton eval set shows RRF mis-ordering retrieved passages); **chunking =
structure-aware, heading-based**, 256–512 tokens, heading-path context, code/tables
atomic; **BM25F weights = heading 3.0 / path 2.0 / body 1.0**, k1=1.2, b=0.75 — all
overridable in `fux.toml`.

## Decided (2026-07-23/24) — retrieval-quality forks from the conformance runs

- [`supersession-handling.compare.md`](supersession-handling.compare.md) — ✅
  **Annotate first (v0.25.0); down-rank penalty reopened and SHIPPED (v0.26.0).**
  `status: superseded`/`superseded_by:` parsed, persisted, annotated; then a
  calibrated fusion rank-offset penalty (default 15, safe interval `[11, ∞)`,
  100% of frontmatter-reachable inversions recovered). → ADRs 0013, 0015.
- [`answer-decline-floor.compare.md`](answer-decline-floor.compare.md) — ✅
  **Absolute floor shipped disabled; margin check REFUTED and closed.** No
  `min_confidence` value clears all gates; the runner-up margin was re-measured
  de-confounded and stays empty. Fabrication is a **documented no-model
  boundary**, not an open defect. → ADR 0014.
- [`hybrid-losing-lexical-hits.compare.md`](hybrid-losing-lexical-hits.compare.md)
  — ✅ **ACCEPT — no fusion change (2026-07-24).** The filed "non-monotone
  fusion" finding was a misdiagnosis (RRF is monotone; 160/160 reconcile). Hybrid
  loses a lexical top-5 hit ~4% on realistic corpora, ~offset by gains; a guard
  would displace fused results and protect superseded docs at lexical rank ≤5.
  Graduated to [`../proposals/chunk-level-dense-codes.md`](../proposals/chunk-level-dense-codes.md).

## Open decisions

- Knowledge substrate v2 — ⏳ moved to
  [`../proposals/knowledge-substrate.md`](../proposals/knowledge-substrate.md)
  (2026-07-21, Arpit: one consolidated proposal): SQLite substrate incl. bulk
  `docs_text`, doc-index-IS-the-graph, one kernel / six verb projections,
  **FuxVec** stdlib binary dense search, git tiers + fresh-clone story,
  enterprise inputs, build milestones. Awaiting Arpit; default next phase per
  the enterprise litmus.
