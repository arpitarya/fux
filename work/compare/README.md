# `work/compare/` — live forks, verdict first

**How to use this directory.** One doc per **live fork**: a genuine decision
with real options, an experiment, or an alternative implementation that
actually exists alongside the current one. Every doc carries two things
non-negotiably — a **verdict** and an explicit **reopen-trigger**, the
condition under which the comparison must be redone.

**Fork or idea?** A fork has options on the table now → here. An idea nobody
has decided on → [`../proposals/`](../proposals/README.md). If you cannot tell
which, it is a proposal.

**The reopen-trigger is a condition, not a date.** Write what would have to
become *true* for the comparison to be worth redoing, in terms someone can
check today. A trigger phrased as an event to await never fires.

The verdict block sits at the **top** of every doc — status, the call,
confidence, and the reopen-trigger — so a reader gets the decision without the
debate, and the debate without archaeology. v0.26-era compare docs are archived
at [`archive/v0.26-docs/compare/`](../../archive/v0.26-docs/compare/).

One doc per genuine fork in the v0.30 design. **The verdict block sits at the
top of every doc** — status, the call, confidence, and the reopen-trigger —
so a reader (human or agent) gets the decision without the debate, and the
debate without archaeology. v0.26-era compare docs are archived at
[`archive/v0.26-docs/compare/`](../../archive/v0.26-docs/compare/).

| doc | fork | verdict | status |
|-----|------|---------|--------|
| [df-over-the-union](df-over-the-union.compare.md) | should ARCHIVED documents count toward `df` (rarity)? | **A + D — change nothing.** `df` stays computed over the union; the mechanism this was really asking for had already shipped as `archived_weight`. ⚠ Its pointer still says the knob lives in `fux.toml`; `[ranking]` moved wholesale to `.fux/tune.toml` in `v2.0.0-alpha.1` and the old table now errors | ✅ accepted (Arpit, 2026-08-22) — **row added 2026-08-25; the doc had none** |
| [file-type-filter](file-type-filter.compare.md) | which file types are indexed, and where that list lives | **G — a `.fux/sources/types` list**, six-glob built-in default, `!` subtraction, no attributes. Shipped as [ADR-TYPES](../../docs/adr/0031_types-list.md) | ✅ accepted (Arpit, 2026-08-20) — **row added 2026-08-25** |
| [graph-plane-format](graph-plane-format.compare.md) | the graph plane's on-disk layout — keep `graph.json`, or go node-major + seekable | **A — keep it.** *"No work is done here now"*; B is deferred to a 50k target, and ⚠ **that target is above CLAUDE.md §Litmus's measurement ceiling**, so the trigger cannot be measured as written | ✅ accepted (Arpit, 2026-08-21) — **row added 2026-08-25** |
| [record-shape-migration](record-shape-migration.compare.md) | four forks on the committed record's shape — schema id, `flen` vs `wlen`, per-field extrema, analyzer version | **all four B, and all four shipped** in `v2.0.0-alpha.0`: `fux.index.v2`, body-first `TF_FIELDS` with trailing zeros omitted (**-36.7 %** on tf vectors), per-field `mx`/`mnw` (`ENTRY_SIZE` 40 -> 62), analyzer v2. ⚠ Its phase table still describes **Phase 7's committed vectors**, built then deleted | ✅ accepted — **row added 2026-08-25; the doc had none** |
| [cross-encoder-reopen](cross-encoder-reopen.compare.md) | does ADR-RERANK veto 1 reopen, now that the *"enrichment already covers it"* premise is dead — **reopen** vs **confirm on a rewritten reason** | **recommend CONFIRM.** The canonical BM25+CE `+4.2 nDCG` is a **2021** number never re-run for a small cross-encoder; gains concentrate where the first stage is **weak** and nearly vanish where it is strong (SciFact `.658 -> .676`); rerankers fall **below** retriever-only in ~half of measured configurations; the metadata alternative has **+32 pts** on versioned technical documentation. ⚠ The honest counter is negation, where cross-encoders are the **only** sub-LLM class above random | ✅ **RULED (Arpit, 2026-08-25, on delegation)** — condition 1 **vacated**, condition 2 **restated** as score-level drift vs the corpus adjacent-gap floor; **refusal stands**. ⚠ The doc's own §6 recommendation was NOT taken |
| [blind-authorship-rule](blind-authorship-rule.compare.md) | does the measurement discipline gain a blind-authorship rule, and **in what words** | **ACCEPTED, in the rewritten form of §5** — every measured run is `blind` or `informed`; an informed run is **reclassified, never banned**, and never supplies a delta (TREC's manual/automatic split, since 1994); a delta below the set's resolution is *no detected change*. **The wording drafted 2026-08-24 was refused** — wrong in four ways CONSORT 2025 and ARRIVE 2.0 name precisely, and silent on power and controls. ⚠ **Two of six parts are apparatus and did NOT take effect** ([W-81](../open/W-81-the-sealed-set-and-the-two-controls.md)). Also carries **three corrections to fux's own filed evidence** | ✅ accepted (Arpit, 2026-08-25) |
| [hook-at-scale](hook-at-scale.compare.md) | what `post-commit` does when the corpus is large — ceiling vs defer vs pre-push vs incremental | **B — the hook defers**: commit cost becomes git's cost (0.34 s at 100k, constant), and it is the only option that reaches the 1 s bound at every size. **Built 2026-08-22** (W-66, all four phases) | ✅ accepted (Arpit, 2026-08-22) |
| [index-format](index-format.compare.md) | tiered JSONL vs MST+BIC wire vs pure scan vs SQLite | **tiered JSONL (T0/T1/T2), git as the Merkle tree** — benches B1–B6 | ✅ accepted (2026-08-09) |
| [storage-architecture](storage-architecture.compare.md) | index-and-refer vs snapshot substrate vs full-copy | **index-and-refer** (size amended by P1-RERUN: full postings) | ✅ accepted (council 2026-08-09) |
| [meta-privacy](meta-privacy.compare.md) | plain vs hashed-default vs hashed-only meta; reopened for materialise-first display + its forks | **hashed-by-default** (2026-08-09) + **D — materialise first, then index** (2026-08-21): L2 exception not needed, cache-miss forces a re-fetch, salt not built, `loc`/`id` unchanged (architecture), `code` kept | ✅ accepted (both halves) |
| [cache-policy](cache-policy.compare.md) | LRU vs ARC | **ARC** | ✅ accepted |
| [ingest-mode-naming](ingest-mode-naming.compare.md) | "extracted" vs "enriched" vs "advanced" for the AI tier | **enriched** (proposed) | ✅ accepted (Arpit, 2026-08-19) — **row corrected 2026-08-25, it had read "awaiting" for six days.** ADR-EXTRACTED and ADR-ENRICHED are both `accepted`; `ingest/run.py` writes `"mode": "extracted"` |
| [source-exclusion](source-exclusion.compare.md) | exclusion attribute vs exclusion *entry* vs `.fuxignore` vs `.gitignore` vs the dot-prefix convention | **an exclusion entry `!path/glob` in `.fux/sources/dirs`** (proposed); C and D eliminated by measurement | ✅ accepted (Arpit, 2026-08-20, verdict E) — **row corrected 2026-08-25.** `ingest/sourcelist.py` implements the `!` exclusion entry, `!!` refused, no attributes |
| [record-freshness](record-freshness.compare.md) | Does a committed record need a timestamp so an age bound can be honoured | **D — no age bound** (proposed) | ⚠ **accepted (Arpit, 2026-08-20, D) — BUT ITS PREMISE IS DEAD.** The verdict rests on *"no committed field is temporal"*; every record now carries `mtime`, a git commit timestamp. **Standing but unargued**, and that is [W-77](../open/W-77-record-reconciliation.md) ruling 1 — Arpit's. Row corrected 2026-08-25 |
| [refer-fetch-cache](refer-fetch-cache.compare.md) | Should the refer plane cache `url:` fetches locally with a wall-clock TTL, and how, without touching the committed record | **F — gitignored TTL cache, `cached` as a 4th verdict state, 300s default** | ✅ accepted (2026-08-20) |
| [url-refresh-trigger](url-refresh-trigger.compare.md) | what supplies the clock a URL has and a file does not — manual vs the `post-commit` hook vs a local daemon vs a CI schedule vs query-driven detection. **Sibling of `maintenance-trigger`, not a reopen of it**: that fork was for files, where the event already exists | proposed **E always, B narrowly, C-or-D by deployment** — *detector* and *clock* are two roles and only the clock is an either/or; the hook is admissible only for the commit that edits `.fux/sources/urls`; **CI where CI can reach the sources, a daemon where it cannot** (air-gapped is a design input, and there CI does not exist) | ⏳ awaiting Arpit (2026-08-22) |
| [url-fetch-concurrency](url-fetch-concurrency.compare.md) | how to parallelise a contract that is single-URL by design, and where Arpit's cap on parallel refreshes lives — sequential vs a blind pool vs declared capability vs `fetch_many` vs processes | proposed **C — declared capability**, `min(declared, configured)`, default 1 when undeclared. The shipped `cdp.py` is **not** thread-safe (`global _session`) and `http.py` is, so a blind pool is silent corruption in the fetcher the design point needs. **The finding: sequential fetching is not what makes the index deterministic — the trailing sort is** | ⏳ awaiting Arpit (2026-08-22) |
| [maintenance-trigger](maintenance-trigger.compare.md) | git hooks + delta ingest vs CI rebuild vs local watch daemon vs manual | **git hooks + delta ingest** (W-25, as scoped) | ✅ accepted (2026-08-20) |

Convention: `> **Verdict:**` blockquote first, then Context → Options →
Matrix → Consequences → References → Reopen-trigger. Docs here are compact;
if one outgrows a screen, split it into a *For humans* summary section and a
*For AI agents* decision-data section (per OPEN-WORK convention).
