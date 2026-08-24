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
| [r7-size-budget](r7-size-budget.compare.md) | what SHAPE R7's committed-size budget should have, now that the `250 MB @100k` row died with the design point — absolute vs **ratio to the indexed corpus** vs per-document vs clone-time vs retiring R7 | proposed **B — a ratio**, because an absolute has to be re-derived every time the design point moves and that has now happened twice. ⚠ **The NUMBER is deliberately left blank**: the 10k size was already measured, so any threshold picked here would be picked knowing whether the engine passes it | ⏳ awaiting Arpit (2026-08-22) |
| [hook-at-scale](hook-at-scale.compare.md) | what `post-commit` does when the corpus is large — ceiling vs defer vs pre-push vs incremental | **B — the hook defers**: commit cost becomes git's cost (0.34 s at 100k, constant), and it is the only option that reaches the 1 s bound at every size. **Built 2026-08-22** (W-66, all four phases) | ✅ accepted (Arpit, 2026-08-22) |
| [index-format](index-format.compare.md) | tiered JSONL vs MST+BIC wire vs pure scan vs SQLite | **tiered JSONL (T0/T1/T2), git as the Merkle tree** — benches B1–B6 | ✅ accepted (2026-08-09) |
| [storage-architecture](storage-architecture.compare.md) | index-and-refer vs snapshot substrate vs full-copy | **index-and-refer** (size amended by P1-RERUN: full postings) | ✅ accepted (council 2026-08-09) |
| [wire-format](wire-format.compare.md) | one format vs wire/runtime split; codec choice | split; BIC wire — **superseded for the committed plane by index-format; survives inside tier T2** | ⚠ superseded |
| [keyspace-unification](keyspace-unification.compare.md) | six planes vs one MST keyspace vs wavelet self-index | one MST keyspace — **superseded: git itself now provides the Merkle tree (index-format)** | ⚠ superseded |
| [meta-privacy](meta-privacy.compare.md) | plain vs hashed-default vs hashed-only meta; reopened for materialise-first display + its forks | **hashed-by-default** (2026-08-09) + **D — materialise first, then index** (2026-08-21): L2 exception not needed, cache-miss forces a re-fetch, salt not built, `loc`/`id` unchanged (architecture), `code` kept | ✅ accepted (both halves) |
| [cache-policy](cache-policy.compare.md) | LRU vs ARC | **ARC** | ✅ accepted |
| [ingest-mode-naming](ingest-mode-naming.compare.md) | "extracted" vs "enriched" vs "advanced" for the AI tier | **enriched** (proposed) | ⏳ awaiting Arpit |
| [source-exclusion](source-exclusion.compare.md) | exclusion attribute vs exclusion *entry* vs `.fuxignore` vs `.gitignore` vs the dot-prefix convention | **an exclusion entry `!path/glob` in `.fux/sources/dirs`** (proposed); C and D eliminated by measurement | ⏳ awaiting Arpit |
| [pruning-criterion](pruning-criterion.compare.md) | KL vs impact vs term-centric vs combined; the gate metric | prediction **falsified** by the re-run (P1-RERUN); pruning removed from the design — full postings | ❌ closed (M8 experiment only) |
| [record-freshness](record-freshness.compare.md) | Does a committed record need a timestamp so an age bound can be honoured | **D — no age bound** (proposed) | ⏳ awaiting Arpit |
| [refer-fetch-cache](refer-fetch-cache.compare.md) | Should the refer plane cache `url:` fetches locally with a wall-clock TTL, and how, without touching the committed record | **F — gitignored TTL cache, `cached` as a 4th verdict state, 300s default** | ✅ accepted (2026-08-20) |
| [url-refresh-trigger](url-refresh-trigger.compare.md) | what supplies the clock a URL has and a file does not — manual vs the `post-commit` hook vs a local daemon vs a CI schedule vs query-driven detection. **Sibling of `maintenance-trigger`, not a reopen of it**: that fork was for files, where the event already exists | proposed **E always, B narrowly, C-or-D by deployment** — *detector* and *clock* are two roles and only the clock is an either/or; the hook is admissible only for the commit that edits `.fux/sources/urls`; **CI where CI can reach the sources, a daemon where it cannot** (air-gapped is a design input, and there CI does not exist) | ⏳ awaiting Arpit (2026-08-22) |
| [url-fetch-concurrency](url-fetch-concurrency.compare.md) | how to parallelise a contract that is single-URL by design, and where Arpit's cap on parallel refreshes lives — sequential vs a blind pool vs declared capability vs `fetch_many` vs processes | proposed **C — declared capability**, `min(declared, configured)`, default 1 when undeclared. The shipped `cdp.py` is **not** thread-safe (`global _session`) and `http.py` is, so a blind pool is silent corruption in the fetcher the design point needs. **The finding: sequential fetching is not what makes the index deterministic — the trailing sort is** | ⏳ awaiting Arpit (2026-08-22) |
| [maintenance-trigger](maintenance-trigger.compare.md) | git hooks + delta ingest vs CI rebuild vs local watch daemon vs manual | **git hooks + delta ingest** (W-25, as scoped) | ✅ accepted (2026-08-20) |

Convention: `> **Verdict:**` blockquote first, then Context → Options →
Matrix → Consequences → References → Reopen-trigger. Docs here are compact;
if one outgrows a screen, split it into a *For humans* summary section and a
*For AI agents* decision-data section (per OPEN-WORK convention).
