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

## Open decisions

- *(none — every fork and sub-decision is resolved; next is the v1 build spec)*
