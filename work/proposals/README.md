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
[W-58](../open/W-58-no-recorded-ingest-time.md).*

**Filed 2026-08-22:**

* [Agent policy for `--hybrid`](agent-hybrid-policy.md) - parked idea, not a build item. `--hybrid`'s output has the same misreadability shape ADR-AGENT-POLICY was built to fix for archived marks (measured off-by-default, RRF scores not comparable to BM25F, a reachability trap on "No confident matches") but none of the four agent-policy renderings mention it. Names three shapes for adding it (extend the existing verbatim block / a separate ranking-path policy / fold into the hybrid-default decision) without picking one. **Graduates when either fires: `--hybrid`'s measured status changes (ADR-ASK's own veto — coupled to `ranking-tuning.md`'s trigger), or a real misread is observed** — an agent trusting hybrid's ranking or scores unprompted, the same evidence bar ADR-AGENT-POLICY itself required.

* [`.fux/tune.toml`, and per-source priority](tune-file-and-source-priority.md) - Arpit's design request, researched. A tunables file separate from `fux.toml` (**boundary rule:** *does changing this value change a byte in `.fux/index/`? yes → it is not a tune key*), written by `fux setup`, **never rewritten by fux** (the fetcher precedent — and `tomllib` cannot write anyway). Per-source preference is **multiplicative, query-time only** (LUCENE-6819 is the argument), keyed in config rather than on the source line because **the line declares the fact and the config declares the weight**, resolved by **longest match** rather than first match because fux's source lists are loader-sorted and have no first. Found the blocker both features hit: **W-73**. Graduates on fork 9 — *may a source weight exceed 1.0?*

* [Ranking tuning, and the utility that would do it](ranking-tuning.md) - research note. **Twelve ranking constants, one of them configurable**, and the literature's verdict that tuning k1/b buys ~nothing (Anserini's 5-fold CV recovers the default to four decimals on 250 topics). Names two constraints the repo already carries and nobody wrote down: `derive/build.py` **requires integer field weights** for the accelerator's u32 `mx`, and BM25F's weight/k1 scale degeneracy must be pinned or a byte-deterministic tuner cannot reproduce itself. Argues the **instrument** (evaluate + gate) is the product and the **optimiser** is not, and that judgment supply — not search — is the binding constraint. **Graduates at ≥ 50 committed judgments plus a ranking decision waiting on them**; the hybrid default is the candidate that trips it first.

* [T2 segments](t2-segments.md) - **was ADR-T2-SEGMENTS (0037) until Arpit moved it here the same day.** The record that **T2 is not built**, decided by measurement: [R9](../regression/2026-08-22-r9-t2-at-10k/VERDICT.md) answered worst-case queries in **12.46 ms against a 150 ms bar**, twelve times inside it, so the third storage tier buys nothing at the design point. **Nothing was ever built** — no `tpack`, no BIC codec, no `tier` knob in `src/`. Its old veto is now a **graduation trigger**, and the difference matters: *a veto is checked, a trigger is remembered*. **Graduates if a measured warm p95 exceeds 150 ms** — a number, never a corpus size. ⚠ Two frozen files still cite it as an ADR and always will; see its head.


**Filed 2026-08-09 for the v0.30 architecture:**

* [MCP as the adapter endgame](mcp-adapters.md) - one protocol instead of per-app adapters; org's own auth. Graduates on the first MCP-gateway design partner or a fourth adapter request.
* [Knowledge CI](knowledge-ci.md) - PRs fail when the index is stale; decisions the diff contradicts surface as cited review comments. Graduates after M6 dogfoods green two weeks.
* [Wavelet-tree self-index](wavelet-self-index.md) - research note preserving the rejected option C of the keyspace compare; reopens only on a law change or a P5 bottleneck.
* [Query-log-informed pruning](query-log-pruning.md) - "query views" were the strongest strategy in the pruning literature (+44–127 %); a per-repo agent query log is an asset Fux gets for free. Graduates post-M7, once real usage exists. Carries a privacy decision (committed vs local).

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
