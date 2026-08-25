# `work/proposals/` — parked ideas

**How to use this directory.** Ideas worth keeping that are **not being built
now** and **not yet decided**. Same rigor as a compare doc — context, sketch,
grounded references — but for future work rather than an active fork.

**A live fork gets [`../compare/`](../compare/README.md); a not-yet-decided
idea gets a proposal here.** Nothing in this directory is a commitment;
everything in it is findable.

Every proposal names its **graduation trigger**: the condition under which it
stops being parked. Without one it is a wish, and it will sit here forever.

Ideas worth keeping that are **not being built now**. Same rigor as a compare doc
(context, sketch, grounded references) but for future work rather than an active
fork. Per OKF, every proposal carries frontmatter:

```yaml
---
type: Proposal
title: <idea>
description: <one line>
status: proposed        # proposed | graduated | rejected
timestamp: <ISO 8601>
---
```

Lifecycle: `proposed` → picked up → **graduates** into a compare doc (if there's a
fork) or a plan entry (if not), and this file's status is updated with a link. Fully
implemented proposals move to [`../archive/`](../../archive/README.md). Nothing here is a
commitment; everything here is findable.

# Index

**Filed and graduated 2026-08-21 — PRIORITY.md P7:**


**Filed 2026-08-10 — from the agent-search-API landscape research:**

* [Agent search-API landscape](agent-search-landscape.md) - research note, not a build item: Parallel/Perplexity/Exa/Brave independently arrived at three index-and-refer decisions, and the corpus they *cannot* reach names Fux's wedge. The evidence base the next two cite.
*Both of the 2026-08-10 refer-plane proposals **graduated and were archived on
2026-08-20**, when M4's core landed — their live successor is
[ADR-REFER](../../docs/adr/0030_refer-plane.md), which is still `proposed`
because R4 has not run. One of the two shipped with its central knob
deliberately refused; the reasoning is in the record and the open question is
[W-58](../../archive/open/W-58-no-recorded-ingest-time.md).*

**Filed 2026-08-22:**


* [`.fux/tune.toml`, and per-source priority](tune-file-and-source-priority.md) - **GRADUATED 2026-08-22 → [ADR-TUNE](../../docs/adr/0038_tuning.md)**; kept for the survey and the forks as they were put. Arpit's design request, researched. A tunables file separate from `fux.toml` (**boundary rule:** *does changing this value change a byte in `.fux/index/`? yes → it is not a tune key*), written by `fux setup`, **never rewritten by fux** (the fetcher precedent — and `tomllib` cannot write anyway). Per-source preference is **multiplicative, query-time only** (LUCENE-6819 is the argument), keyed in config rather than on the source line because **the line declares the fact and the config declares the weight**, resolved by **longest match** rather than first match because fux's source lists are loader-sorted and have no first. Found the blocker both features hit: **W-73**. Graduates on fork 9 — *may a source weight exceed 1.0?*

* [Ranking tuning, and the utility that would do it](ranking-tuning.md) - research note. **Twelve ranking constants, one of them configurable**, and the literature's verdict that tuning k1/b buys ~nothing (Anserini's 5-fold CV recovers the default to four decimals on 250 topics). Names two constraints the repo already carries and nobody wrote down: `derive/build.py` **requires integer field weights** for the accelerator's u32 `mx`, and BM25F's weight/k1 scale degeneracy must be pinned or a byte-deterministic tuner cannot reproduce itself. Argues the **instrument** (evaluate + gate) is the product and the **optimiser** is not, and that judgment supply — not search — is the binding constraint. **Graduates at ≥ 50 committed judgments plus a ranking decision waiting on them**; ⚠ **that trigger named the hybrid default, and the dense lane was deleted 2026-08-25 — it can never fire as written**. ⚠ **Substantially overtaken 2026-08-25.** ADR-TUNE shipped on 2026-08-24, so *"one of them configurable"* is false — `.fux/tune.toml` now exposes `k1`, `b`, five field weights and fourteen more keys. The integer-field-weight constraint it names was **dissolved by W-73** (`mx` is a raw per-field count; weights are applied at query time). Its *"one item with a decision waiting on it"* was the **hybrid default**, and that lane is deleted. ⚠ It also proposes the verb name `fux tune`, **which ADR-TUNE has since taken for something else**.

* [T2 segments](t2-segments.md) - **was ADR-T2-SEGMENTS (0037) until Arpit moved it here the same day.** The record that **T2 is not built**, decided by measurement: [R9](../regression/2026-08-22-r9-t2-at-10k/VERDICT.md) answered worst-case queries in **12.46 ms against a 150 ms bar**, twelve times inside it, so the third storage tier buys nothing at the design point. **Nothing was ever built** — no `tpack`, no BIC codec, no `tier` knob in `src/`. Its old veto is now a **graduation trigger**, and the difference matters: *a veto is checked, a trigger is remembered*. **Graduates if a measured warm p95 exceeds 150 ms** — a number, never a corpus size. ⚠ Two frozen files still cite it as an ADR and always will; see its head.


* [URL freshness](url-freshness.md) - Arpit's question: *"repo documents can be re-indexed on every commit — but what about the URLs?"* **A file change is an event; a URL change is not**, and that asymmetry is the whole problem. Two reframes do most of the work: *answer* freshness is already shipped (the refer plane compares shas), so **a stale `url:` record costs recall, not correctness**; and a **detector** and a **clock** are different roles, which collapses most of the apparent options. Proposes a nearly-free detector (the refer plane records a `url:` doc dirty when the shas disagree — `dirty.py` and `run(only_urls=…)` both already exist), an **optional fifth fetcher function** `validate(url) -> str | None` whose batching rides `connect()` rather than a batch signature, a clock, a bounded parallel refresh, and the reporting that should ship whatever else does not. Two forks split out to [`../compare/url-refresh-trigger`](../compare/url-refresh-trigger.compare.md) and [`../compare/url-fetch-concurrency`](../compare/url-fetch-concurrency.compare.md); tracked as [W-75](../open/W-75-url-freshness.md). **Graduates on a number, not a corpus size: the fraction of a `fux update` sweep that re-fetched a document whose sanitized sha was unchanged — ≥ 80 % and the contract amendment argues itself; ≤ ~40 % and the contract stays at four functions.**

* [How answer quality is measured](measuring-answer-quality.md) - Arpit's question, researched: *"what is the percentage that it is going to give me correct answer?"* **A single accuracy number is not a property of fux** — it is a property of (engine, corpus, query mix), and of the four gates it decomposes into fux owns two. Proposes a **versioned `mix.toml`** (`P(q)` becomes a declared prior instead of an implicit uniform one), a **four-gate funnel** whose middle gate `recall@k` is the honest headline and the ceiling ADR-ANSWER already promises, **correct-per-1k-bytes** as the comparison unit, **cost-weighted error** so a fabricated citation stops counting the same as an honest decline, and **calibration**. Grounded in two live runs that passed their number and failed their claim (P1-GATE, the budget sweep). ⚠ **Not a re-filing of the withdrawn W-62.** Tracked as [W-74](../open/W-74-answer-quality-measurement-contract.md). **Graduates when a corpus exists to run it against and a decision is waiting on a quality number** — or sooner and partially, the moment any quality figure is about to be published externally.

**Filed 2026-08-09 for the v0.30 architecture:**

* [MCP as the adapter endgame](mcp-adapters.md) - one protocol instead of per-app adapters; org's own auth. Graduates on the first MCP-gateway design partner or a fourth adapter request.
* [Knowledge CI](knowledge-ci.md) - PRs fail when the index is stale; decisions the diff contradicts surface as cited review comments. Graduates after M6 dogfoods green two weeks.
* [Wavelet-tree self-index](wavelet-self-index.md) - research note preserving the rejected option C of the keyspace compare; reopens only on a law change or a P5 bottleneck.

**Carried over — architecture-agnostic survivors:**

All three survivors are architecture-agnostic and, if anything, *strengthened*
by the v0.30 index-and-refer rebuild (the MST keyspace gives knowledge-diff and
the audit trail their substrate natively — see [the ADR register](../../docs/adr/README.md) M8+):

* [Research-to-Spec](research-to-spec.md) - evidence-backed specs; every claim cites the corpus at a commit.
* [Knowledge diff & time-travel](knowledge-diff.md) - `fux diff`/`fux log`; ask questions of past knowledge. Natural fit for the one-root-hash keyspace.
* [Audit evidence trail](audit-evidence-trail.md) - deterministic cited answers as an auditable chain; seed of the deferred Plane. The ledger's sha@index + fresh-sha citations are its raw material.

**v0.26-era proposals** (tied to the archived substrate engine) moved to
[`archive/v0.26/proposals/`](../../archive/v0.26/proposals/):
knowledge-substrate (the SQLite substrate — superseded by the index-and-refer
architecture), chunk-level-dense-codes, hybrid-degrades-at-scale (✅ resolved
2026-07-22 as a corpus artifact). Earlier implemented proposals remain in
[`../archive/`](../../archive/README.md) as before.

*(The fourth idea from the 2026-07-21 ideation — the **product-memory corpus**,
Arpit's own seed — graduated into the v0.26 plan; its successor concept lives on
as the committed index + ledger of the current architecture.)*

**Graduated and archived 2026-08-22** — moved out of this directory once their
change was live, per this file's own lifecycle (*implemented proposals move to
`archive/`*):

* [Consumer intent policy](../../archive/proposals/consumer-intent-policy.md) — became
  [ADR-AGENT-POLICY](../../docs/adr/0035_agent-policy.md), accepted **and built**:
  `fux setup` installs the four renderings and they live at
  [`src/fux/templates/agents/`](../../src/fux/templates/agents/). Its
  `consumer-policy/` drafts directory went with it — the files had already moved
  to the wheel, leaving only a pointer.
* [Put the process on a diet](../../archive/proposals/process-diet.md) — graduated
  same-session 2026-08-21 (PRIORITY P7); the `Cost:` line is gone from the
  WORKLOG format and the change is live in the process itself.

**Filed 2026-08-24 — W-76 implementation, blocked on ratification:**

* [50 candidate goldens for the playground](playground-goldens-draft.md) - **GRADUATED 2026-08-24 -> installed, and the run is filed at [`../regression/2026-08-24-rerank-and-goldens/`](../regression/2026-08-24-rerank-and-goldens/). Baseline 28/50; the reranker 32; enrichment 38; both together 41.** Arpit waived the human-author rule (*"all is on you"*) and the deviation is recorded in the playground's own `goldens/README.md` so the set can never be mistaken for the lost human-graded one. Of the nine predicted `known_failure`s, five were right and four wrong. Original filing follows -- **the playground has graded nothing since W-56 destroyed `queries.jsonl` on 2026-08-20**, and its README refuses to let the engine invent replacements: *"a playground whose goldens were invented by the engine under test is worse than no playground."* An agent that drafts goldens **and installs them** re-derives that failure one level up, so these 50 are drafted and not installed. Written by reading the ten documents before any `fux` command ran; three phrasings contaminated by an earlier sanity run are named and excluded. Bands the set by **phenomenon rather than by id**, which is what lets **W-57** be re-scoped off the four dead ids it still names. Carries the distinction that makes the whole thing workable: `q`/`doc`/`max_rank` are claims about the *corpus* and must precede the engine, `known_failure` is a claim about the *engine* and may legitimately be recorded from a run — so §1 asks for the set to be installed with the nine predicted `known_failure`s **stripped**, run once, and the flags re-added only where it actually failed. **Graduates when Arpit ratifies** (whole, or line by line).
