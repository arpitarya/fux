# `archive/` — the one archive, and where each thing went

**Rule (Arpit, 2026-08-10, restated 2026-08-18): there is exactly ONE archive
directory, and it is this one, at the repo root.** Nothing under `docs/` or
`work/` is an archive. Anything that gets archived is moved here.

**How to use this file.** This README is the **map**. Every archived doc gets a
row naming its **live successor**, so a reader who lands here is sent forward
rather than left at a dead end.

Enforced by `tests/test_archive_law.py`, which fails when a directory named
`archive` appears anywhere but here.

---

## Archive is not evidence

**A doc in here may be *named*. It may never be *cited as backing a live
claim*.**

The reason is mechanical, not ceremonial: nothing guarantees an archived file
was not edited or overwritten after it was retired. An archived doc is a record
that something *was* decided, not proof of what is true now.

- A record's **Reference** section may say "superseded by X" and name an
  archived doc. It may not ground a decision in one — the ADR register
  ([`../docs/adr/README.md`](../docs/adr/README.md)) says so, and the template
  repeats it at the point of use.
- When you find a live doc citing an archived one, **repoint it at the live
  successor**. Do not simply delete the link: a deleted link leaves the claim
  ungrounded, which is worse, because nobody can see that anything is missing.
- If a claim's only support is an archived doc, it needs new grounding — code,
  a live doc, or a measured run under
  [`../work/regression/`](../work/regression/README.md).

Entries here are frozen and reference-only. **Relative links inside them
reflect the tree as it was** and are not repaired; a frozen document is never
edited, which is the property that makes its contents trustworthy.

---

## Layout — the archive mirrors the live tree

A retired artifact goes to `archive/<the-directory-it-came-from>/`. `work/adr/`
retires into `archive/adr/`, `work/handoff/` into `archive/handoff/`, and so on
for `compare/` and `proposals/` when their turn comes. Old *builds* keep their
version-named directories.

```
archive/
  README.md              this map
  adr/                   superseded decision records — old number -> successor NAME
  handoff/               executed handoff + prompt pairs of the current build
  open/                  closed work items — the detail file, once its row left the queue
  v0.1/                  build: the first one, pre-reset #1
  v0.26/                 build: the v0.19-0.26 substrate engine, runnable
  v0.26-docs/            build: that engine's frozen doc set
  v0.26-implemented/     build: that line's executed artifacts
  v0.30-rev1-planning/   the rebuild's research phase, frozen
```

## Superseded decision records

[`adr/`](adr/README.md) — each row maps a retired **number** to its live
successor **name**. Numbers survive only here; live prose cites names.

**The whole v0.30 record set retired here on 2026-08-18** — five records, in
one change, on Arpit's instruction. `work/adr/` no longer exists; the live
records are in [`docs/adr/`](../docs/adr/README.md) and the archive's map names
a successor for every one.

## `handoff/` — the retired handoff directory

**The whole directory was retired on 2026-08-18**, on Arpit's instruction, and
moved here as-is. It holds two different kinds of thing, and the difference
matters:

**Executed pairs** — implemented, with the record that closed them. These have
live successors and are safe to be named from anywhere.

| artifact | shipped | live successor |
|---|---|---|
| [`v0.30.0-m1-t0-slice-handoff.md`](handoff/v0.30.0-m1-t0-slice-handoff.md) · [prompt](handoff/v0.30.0-m1-t0-slice-prompt.md) | 2026-08-10 | [ADR-RECORD](../docs/adr/0010_index-record.md) |
| [`v0.31.0-fux-dir-layout-handoff.md`](handoff/v0.31.0-fux-dir-layout-handoff.md) · [prompt](handoff/v0.31.0-fux-dir-layout-prompt.md) | 2026-08-11 | [ADR-DOTFUX](../docs/adr/0003_fux-directory.md) |
| [`v0.31.0-fux-playground-extraction-handoff.md`](handoff/v0.31.0-fux-playground-extraction-handoff.md) · [prompt](handoff/v0.31.0-fux-playground-extraction-prompt.md) | 2026-08-12 | [SETUP-PLAYGROUND](../work/setup/fux-playground.md) |
| [`v0.32.0-open-items-handoff.md`](handoff/v0.32.0-open-items-handoff.md) · [prompt](handoff/v0.32.0-open-items-prompt.md) | Phases 0 and 1 closed 2026-08-12 | [`work/IMPLEMENTATION.md`](../work/IMPLEMENTATION.md) — the M2 and R2-close rows |

**Retired while still unresolved — no live successor.** These were archived by
instruction, not by completion. **Nothing may cite them as grounding**; the
open items they relate to have to carry their own content from here on.

| artifact | what it was | the open item that outlived it |
|---|---|---|
| [`v0.32.0-ratification-package.md`](handoff/v0.32.0-ratification-package.md) | the five Lane B decisions packaged for one sitting | [W-31](open/W-31-ratify-adr-0010-0011.md) · [W-33](open/W-33-adr-numbering-contradiction.md) · [W-44](open/W-44-archived-content-signalling.md) — **each states its own decision now**. W-30 and W-32 closed 2026-08-19; their files are in [`open/`](open/) |
| [`v0.30.0-claude-md.diff`](handoff/v0.30.0-claude-md.diff) · [`v0.30.0-m1-claude-md-build-test.diff`](handoff/v0.30.0-m1-claude-md-build-test.diff) · [`v0.31.0-claude-md-layout.diff`](handoff/v0.31.0-claude-md-layout.diff) | prepared `CLAUDE.md` diffs awaiting review | [W-32](open/W-32-claude-md-adoption.md) — **closed 2026-08-19, the rewrite adopted**; the diffs were already history and remain so |
| [`v0.32.0-adr-numbering.diff`](handoff/v0.32.0-adr-numbering.diff) | the numbering-contradiction fix | [W-33](open/W-33-adr-numbering-contradiction.md) — **superseded**: the contradiction was resolved directly on 2026-08-18 |
| [`v0.33.0-m4-refer-plane-handoff.md`](handoff/v0.33.0-m4-refer-plane-handoff.md) · [prompt](handoff/v0.33.0-m4-refer-plane-prompt.md) | the M4 build spec, written but never executed | [W-24](../work/open/W-24-m4-refer-plane.md) — **M4 has no live spec.** Whoever starts it writes a fresh one; this pair may be read for ideas but not cited |

**Handoffs are no longer a live directory.** A spec for open work belongs in
that item's detail file under [`work/open/`](../work/open/README.md).

## `open/` — closed work items

A work item's detail file retires here when its row leaves
[`work/OPEN-WORK.md`](../work/OPEN-WORK.md). **The row is still deleted, never
ticked** — the length of the queue stays the signal of what is pending — but
the file that argued the decision is kept, because the reasoning that produced
a call is worth more than the call alone.

**These are not evidence.** The durable record of a closed item is its ADR plus
the [`WORKLOG`](../work/WORKLOG.md) entry; a file here may be named, never
cited. Several also contain claims that were *wrong* — which is part of why
they are worth keeping.

| item | closed | outcome and live successor |
|---|---|---|
| [`W-30-ratify-adr-0001.md`](open/W-30-ratify-adr-0001.md) | 2026-08-19 | Arpit ratified the ingest-mode naming → [ADR-EXTRACTED](../docs/adr/0016_extracted-mode.md) · [ADR-ENRICHED](../docs/adr/0017_enriched-mode.md), both accepted. The file's own "**Non-blocking**" note was **wrong**: `mode` is a committed wire-format value, so the *reversal* cost rises with every index written |
| [`W-32-claude-md-adoption.md`](open/W-32-claude-md-adoption.md) | 2026-08-19 | Arpit adopted the M0a rewrite → the live [`CLAUDE.md`](../CLAUDE.md), PROPOSED header deleted. The file's "Correction (2026-08-12): there is no `CLAUDE.md.proposed`" was **wrong as history** — the file existed at `bed2186` and was implemented into `CLAUDE.md` at `3892c55`; `git log --follow` cannot see a delete-plus-overwrite, so a *verified* claim rested on evidence that could not show it |

| [`W-31-ratify-adr-0010-0011.md`](open/W-31-ratify-adr-0010-0011.md) | 2026-08-19 | Arpit ratified all three as-is → [ADR-DOTFUX](../docs/adr/0003_fux-directory.md) · [ADR-URL-INGEST](../docs/adr/0008_url-ingest.md) · [ADR-CONFIG](../docs/adr/0014_config.md), and confirmed `.fux/README.md` is generated at **ingest** time. Two of its three DoD items had already been satisfied by unrelated changes; the third named the wrong section of `CHANGELOG.md` |

| [`W-33-adr-numbering-contradiction.md`](open/W-33-adr-numbering-contradiction.md) | 2026-08-19 | Arpit confirmed the convention: **`docs/adr/` is the live set and starts at 0001; the records under `archive/` are archived.** Every mechanical item had already been satisfied by other changes. Its live consequence — four items reserving numbers that accepted records already held — was swept to **names** in the same change |

| [`W-47`](open/W-47-hashed-meta-blocks-accelerator.md) · [`W-49`](open/W-49-url-fragment-truncation.md) · [`W-50`](open/W-50-url-fetch-mechanism.md) · [`W-51`](open/W-51-fetcher-template-not-shipped.md) · [`W-53`](open/W-53-dirs-file.md) | 2026-08-19 | **Merged, not completed**, into [`W-54`](open/W-54-sources-rewrite.md) on Arpit's call. All five rewrite one parser and one generated set, and each carried a hazard saying *land it with the others* — five definitions of done for one change. **They are still five defects**; their analysis lives here and W-54 is the work order |

| [`W-54-sources-rewrite.md`](open/W-54-sources-rewrite.md) | 2026-08-19 | **Completed.** All five merged defects closed in five commits, each with its records. Live successors: the code is [`ingest/sourcelist.py`](../src/fux/ingest/sourcelist.py) · [`setup.py`](../src/fux/setup.py) · [`sources.py`](../src/fux/sources.py) · [`templates/`](../src/fux/templates/); the decisions are [ADR-URL-LIST](../docs/adr/0018_url-list.md) · [ADR-DIR-LIST](../docs/adr/0022_dir-list.md) · [ADR-FETCHER](../docs/adr/0019_fetcher.md) · [ADR-HTTP-FETCHER](../docs/adr/0021_http-fetcher.md) · [ADR-INDEX-LIFECYCLE](../docs/adr/0009_index-lifecycle.md) decision 9; the evidence is [`2026-08-19-w54`](../work/regression/2026-08-19-w54/report.md). **One section was overruled by a record**: §5 describes a verb that fetches, and ADR-CLI's captured surface makes `--refresh-urls` the only networked path (L4) — `fux url` records and never fetches |

| [`W-46-hybrid-missing-model-crash.md`](open/W-46-hybrid-missing-model-crash.md) | 2026-08-20 | **Completed.** Live successor: the `None` guard in [`query/hybrid.py`](../src/fux/query/hybrid.py) and its two tests in [`tests/derive/test_dense_and_hybrid.py`](../tests/derive/test_dense_and_hybrid.py); the decision is [ADR-CLI](../docs/adr/0002_cli-surface.md). **One deviation from its definition of done**: the regression test landed beside the other hybrid tests rather than in `tests/query/`, because duplicating the corpus fixture into a second directory costs more than the path documents |

| [`W-48-query-output-contract.md`](open/W-48-query-output-contract.md) | 2026-08-20 | **Completed — two of three fixed, the third decided.** Live successors: `cmd_ask` and `cmd_answer` in [`query/__init__.py`](../src/fux/query/__init__.py), pinned by [`tests_e2e/test_verbs.py`](../tests_e2e/test_verbs.py); the decisions are [ADR-ASK](../docs/adr/0004_ask.md) and [ADR-ANSWER](../docs/adr/0006_answer.md). Item 3 — `find`'s prose no-match line — was **left alone deliberately** and is now pinned by a test, so the call is visible rather than remembered |

| [`W-23-m3-graph-lane.md`](open/W-23-m3-graph-lane.md) | 2026-08-20 | **Completed — with two of its definition-of-done items carried forward rather than claimed.** Live successors: the code is [`src/fux/graph/`](../src/fux/graph/); the decision is [ADR-GRAPH](../docs/adr/0029_graph.md); the eval is [`tests_e2e/test_relational.py`](../tests_e2e/test_relational.py) with its corpus at [`tests_e2e/eval/`](../tests_e2e/eval/). **What it did not deliver**, both now [W-57](open/W-57-graph-lane-acceptance.md): the playground acceptance targets `q005`/`q009`/`q011`/`q015` are unmeasured because `fux-playground` does not exist on this machine ([W-56](../work/open/W-56-sibling-environments-missing.md)), and community determinism is verified on one machine rather than the two it asked for |

| [`proposals/caller-set-freshness-policy.md`](proposals/caller-set-freshness-policy.md) | 2026-08-20 | **Implemented, with its central knob refused.** Live successor: [ADR-REFER](../docs/adr/0030_refer-plane.md) decisions 4-8 and [`src/fux/refer/freshness.py`](../src/fux/refer/freshness.py). The caller-owned policy and the `never` sentinel shipped; **`max_age_seconds` did not** — the committed record carries no ingest time, so the bound could not have been honoured, and a knob that lies is worse than a missing one. Content verification replaced it. The open question it leaves is [W-58](../work/open/W-58-no-recorded-ingest-time.md) |

| [`proposals/token-budget-retrieval.md`](proposals/token-budget-retrieval.md) | 2026-08-20 | **Implemented.** Live successor: [ADR-REFER](../docs/adr/0030_refer-plane.md) decisions 10-13 and [`src/fux/refer/assemble.py`](../src/fux/refer/assemble.py). Byte budget primary, `k` secondary, deterministic ties, per-document cap — plus a floor the proposal did not anticipate, because greedy score-per-byte is systematically biased toward short passages |

| [`W-24`'s two graduating proposals](proposals/) | — | Both successors sit in a record that is **`proposed`, not accepted**: R4 has not run ([W-59](open/W-59-refer-plane-measurement.md)). Named here so a reader does not take archival as ratification |

| [`W-45-source-exclusion.md`](open/W-45-source-exclusion.md) | 2026-08-20 | **Completed — verdict E built.** Live successors: [ADR-DIR-LIST](../docs/adr/0022_dir-list.md) decisions 2a-2c, and the `!` grammar in [`ingest/sourcelist.py`](../src/fux/ingest/sourcelist.py) with `_excluded_by` in [`ingest/gitdir.py`](../src/fux/ingest/gitdir.py). The verdict **overrode the record's own anticipation** — an exclusion is an *entry*, not the attribute ADR-DIR-LIST expected. The measurement that killed the dot-prefix alternative (2 of 7 runs followed it) is in [`source-exclusion.compare.md`](../work/compare/source-exclusion.compare.md), which is live |

| [`W-55-no-file-type-filter.md`](open/W-55-no-file-type-filter.md) | 2026-08-20 | **Completed — verdict G built.** Live successor: [ADR-TYPES](../docs/adr/0031_types-list.md), and `DEFAULT_TYPES` / `read_types` in [`ingest/gitdir.py`](../src/fux/ingest/gitdir.py). Landed **in the same change as W-45** because both change one file format. ⚠ **the ranking half is unmeasured and this repo was deliberately not re-ingested** — that step rides with [W-52](open/W-52-df-over-the-union.md) |

| [`W-56-sibling-environments-missing.md`](open/W-56-sibling-environments-missing.md) | 2026-08-20 | **Completed — both environments rebuilt, and both now under git, which neither was before.** Live successors: [SETUP-LAB](../work/setup/fux-lab.md) and [SETUP-PLAYGROUND](../work/setup/fux-playground.md), each carrying a *rebuilt* section naming what could not be restored. **The goldens were deliberately not rebuilt** and that obligation moved to [W-57](open/W-57-graph-lane-acceptance.md), which was re-scoped in the same change because its named query ids belonged to the lost set. Every prior baseline and corpus is unrecoverable; the M2 report is annotated rather than edited |
| [`W-57-graph-lane-acceptance.md`](open/W-57-graph-lane-acceptance.md) | 2026-08-22 | **Completed — both halves, with two departures recorded rather than smoothed over.** Live successors: [ADR-GRAPH](../docs/adr/0029_graph.md) veto conditions **1 and 3**, both discharged, and [the run](../work/regression/2026-08-22-graph-acceptance/report.md). The phenomena scored **24/24** — but on a **substitute corpus** (a new 66-document `graph-acceptance` environment in fux-lab), because fux-playground's human goldens were lost on 2026-08-20 and may never be rebuilt; and **its goldens were agent-authored** from construction ground truth, against this item's own "no agent should do it", at Arpit's direct instruction. Determinism closed on a **second machine and a second architecture** (x86-64 Linux vs arm64 macOS), which is more than veto 1 asked for |
| [`W-44-archived-content-signalling.md`](open/W-44-archived-content-signalling.md) | 2026-08-22 | **Completed — open since 2026-08-12, the longest-running item in the queue.** Live successors: [ADR-ARCHIVED-CONTENT](../docs/adr/0037_archived-content.md) (all seven decisions built), the instrument at [`tools/archived-signal-eval/`](../tools/archived-signal-eval/PRE-REGISTRATION.md), and [W44-SIGNAL](../work/regression/2026-08-22-archived-signal/VERDICT.md) (**WARRANTED**, 32.00 pts vs a 25 pt bar). **The gate came down twice**: the instrument was frozen first, then Arpit lifted decision 5's gate by instruction. The file's original five-query probe is **superseded and was not reproducible** — it ran against paths the 2026-08-18 restructure removed |
| [`W-59-refer-plane-measurement.md`](open/W-59-refer-plane-measurement.md) | 2026-08-22 | **Completed — all three measurement obligations.** R4 PASS (2026-08-20), ARC-vs-LRU ruled by Arpit, and the budget sweep run. The sweep's result **did not fit its own FLAT/NOT-FLAT rule** and was reported that way rather than forced into a branch; the defect it found became [W-72](open/W-72-refer-per-doc-cap-single-candidate.md). Live successor: [ADR-REFER](../docs/adr/0030_refer-plane.md) veto condition 2 |
| [`W-69-prediction-register-check.md`](open/W-69-prediction-register-check.md) | 2026-08-22 | **Completed.** Live successors: [`tests/test_prediction_register.py`](../tests/test_prediction_register.py) and [ADR-RS](../docs/adr/0036_predictions.md), which moved ⏳ proposed → ✅ **accepted** because this check *was* its acceptance gate. Building it forced a refinement the item did not anticipate: the first non-`R` verdict arrived the same day, so `IMPLEMENTATION.md` grew a **feature-gate** register and the check reads both |
| [`W-72-refer-per-doc-cap-single-candidate.md`](open/W-72-refer-per-doc-cap-single-candidate.md) | 2026-08-22 | **Completed the day it was filed.** Live successor: [ADR-REFER](../docs/adr/0030_refer-plane.md) veto condition 2, now recording the fix. **Filed as W-70 and renumbered to W-72** on the same day — `W-70` was already claimed by a file committed in `e11ca74`, and a contested id is not reused |
| [`W-73-weighted-scores-vs-pruning-bound.md`](open/W-73-weighted-scores-vs-pruning-bound.md) | 2026-08-24 | **Built 2026-08-23, released in `v2.0.0-alpha.0`.** Live successors: [ADR-T1-ACCELERATOR](../docs/adr/0011_accelerator.md) and [ADR-RANKING](../docs/adr/0012_ranking.md) — the differential law now holds at **every** configured weight, not only at `1.0`. Evidence: [the fork-3 run](../work/regression/2026-08-23-fork3-per-field-bound/report.md) (per-field extrema measured **free**, +0.0% blocks scanned) and [`IMPLEMENTATION.md`](../work/IMPLEMENTATION.md)'s W-73 row. ⚠ **The file's own opening statement is now false** — it argues the law holds only at `1.0`, which is the defect it went on to fix |
| [`W-76-amended-architecture.md`](open/W-76-amended-architecture.md) | 2026-08-24 | **All nine phases built 2026-08-23/24, released in `v2.0.0-alpha.0`.** Live successors: [ADR-INDEX-LIFECYCLE](../docs/adr/0009_index-lifecycle.md) · [ADR-RECORD](../docs/adr/0010_index-record.md) · [ADR-TUNE](../docs/adr/0038_tuning.md) · [ADR-MCP](../docs/adr/0039_mcp.md) · [ADR-ENRICH](../docs/adr/0040_enrich.md) · [ADR-RERANK](../docs/adr/0041_rerank.md). Evidence: [the rerank/goldens run](../work/regression/2026-08-24-rerank-and-goldens/report.md) and [`IMPLEMENTATION.md`](../work/IMPLEMENTATION.md)'s W-76 row. ⚠ The spec names a **cross-encoder for Phase 6 that was refused** — `onnxruntime` is not byte-identical across architectures; the built reranker is stdlib arithmetic |
| [`W-76-DECISIONS.md`](open/W-76-DECISIONS.md) | 2026-08-24 | **D1-D30, every call taken in Arpit's absence during W-76.** Retired with its item. Live successor for any decision that became binding: the record it landed in, above. Kept because the reasoning is worth more than the ruling alone — and because four of the thirty are still owed a ratification, tracked by [W-77](../work/open/W-77-record-reconciliation.md) |
| [`W-62-measure-against-the-outside-world.md`](open/W-62-measure-against-the-outside-world.md) | 2026-08-22 | **WITHDRAWN by Arpit, not completed** — *"the whole w sixty two, remove it, cancel it out. That's on me."* Part 3 (the public README) **was** completed and is the only live successor: two false statements of fact fixed. Parts 1 and 2 — the three-way comparison and five external installs — are **cancelled and personally owned by Arpit**, and no agent should re-file them. ⚠ **The question is not answered**: whether Fux wins on private organisational documents is still untested. **Id retired, not reused** |
| [`W-52-df-over-the-union.md`](open/W-52-df-over-the-union.md) | 2026-08-22 | **Closed by deciding not to change anything — A + D.** Live successors: [ADR-ARCHIVED-CONTENT](../docs/adr/0037_archived-content.md) decision 4 (now a ratified decision rather than a deferral) and [the compare doc](../work/compare/df-over-the-union.compare.md). **Its own options table is superseded**: it listed A/B/C, and the answer was a **D that did not exist when it was written** (`archived_weight`, shipped 2026-08-22). Two of its DoD boxes are unticked on purpose — the two-corpus gate was the price of *changing* `df`, not of declining to |

| [`W-25-m5-maintenance.md`](open/W-25-m5-maintenance.md) | 2026-08-20 | **Completed — the build; both gates unrun.** Live successors: [`src/fux/maintain/`](../src/fux/maintain/) and `assert_meta_policy` in [`store/writer.py`](../src/fux/store/writer.py); the decision is [ADR-MAINTENANCE](../docs/adr/0032_hooks.md), **`proposed` not accepted** because R5 and R6 have not run. Its DoD's measurement half is [W-61](open/W-61-maintenance-measurement.md). The mechanism was Arpit's call in [`maintenance-trigger.compare.md`](../work/compare/maintenance-trigger.compare.md); what the record decided is everything that verdict left open, including the `post-commit`-not-`pre-commit` argument |
| [`W-61-maintenance-measurement.md`](open/W-61-maintenance-measurement.md) | 2026-08-22 | **Closed — both gates ruled, neither by a passing re-measurement.** Live successors: the decisions are [ADR-MAINTENANCE](../docs/adr/0032_hooks.md) (**accepted**, decisions 1a/1b — the hook defers) and [ADR-MERGE-DRIVER](../docs/adr/0033_merge-driver.md) (**accepted** on Arpit's §3.1 reading of R6); the fork's verdict is [`hook-at-scale.compare.md`](../work/compare/hook-at-scale.compare.md); the build is [W-66](../work/open/W-66-deferred-hook.md) and the instrument repair [W-67](../work/open/W-67-r6-instrument-repair.md). The measurements themselves are unarchived and stay citable: [R5-HOOK](../work/regression/2026-08-20-r5-hook-latency/VERDICT.md) and [R6-MERGE](../work/regression/2026-08-20-r6-merge-driver/VERDICT.md), the latter carrying the 2026-08-22 adjudication addendum |
| [`W-66-deferred-hook.md`](open/W-66-deferred-hook.md) | 2026-08-22 | **Closed — filed and built the same day, all four phases.** Live successors: [`src/fux/maintain/dirty.py`](../src/fux/maintain/dirty.py) and [`runner.py`](../src/fux/maintain/runner.py), `doctor.py`'s background-runner check, `query/__init__.py::_declare_pending`, and `fux ingest --stop`. Decisions are [ADR-MAINTENANCE](../docs/adr/0032_hooks.md) **1a–1d**, with [ADR-CLI](../docs/adr/0002_cli-surface.md), [ADR-INGEST](../docs/adr/0007_ingest.md) and [ADR-DOTFUX](../docs/adr/0003_fux-directory.md) amended in the same changes — Law zero across four records. The fork it implements is [`hook-at-scale.compare.md`](../work/compare/hook-at-scale.compare.md) |
| [`W-67-r6-instrument-repair.md`](open/W-67-r6-instrument-repair.md) | 2026-08-22 | **Closed — the instrument was repaired and R6 re-run, PASS.** Live successor: the new run at [`2026-08-22-r6-rerun`](../work/regression/2026-08-22-r6-rerun/VERDICT.md), whose tier 1 hash-selects a shared shard and is therefore informative. **Neither the 2026-08-20 pre-registration nor the original R6-MERGE verdict was edited** — a new registration and a new verdict, which is the discipline the item existed to honour. [ADR-MERGE-DRIVER](../docs/adr/0033_merge-driver.md) now rests on a clean pass rather than on a reading |
| [`W-65-design-point-reconciliation.md`](open/W-65-design-point-reconciliation.md) | 2026-08-22 | **Closed — the record set reconciled to the 10 000-document design point**, 14 documents relabelled rather than deleted, since an argument that holds at 10⁶ usually still holds at 10⁴. **The paper was fenced out of this item deliberately** and belongs to W-26, which measured and closed it the same day. Frozen pre-registrations and filed verdicts were left untouched, as the item's own two hard rules required |
| [`W-26-m6-scale-t2.md`](open/W-26-m6-scale-t2.md) | 2026-08-22 | **Closed — M6's first question answered by measurement, and the answer was NOT to build.** Live successor: [ADR-T2-SEGMENTS](../docs/adr/0037_t2-segments.md), the record of a tier deliberately not built, with a reopen condition that is **a number, not a size**. [R9](../work/regression/2026-08-22-r9-t2-at-10k/VERDICT.md) passed at **12.46 ms against R3's own 150 ms bar, reused verbatim** rather than restated. The paper's §5–§6 were rewritten from projection to measurement at 10 000. ⚠ **Its last box was not met — it was dissolved**: Arpit retired **R7** on 2026-08-22 rather than re-deriving its budget, so the requirement ceased to exist. The item's own design allowed "no" as a legitimate close, and that is what happened |
| [`W-38-m8-deferred.md`](open/W-38-m8-deferred.md) | 2026-08-22 | **Dropped, not completed** — removed from the queue on Arpit's instruction; nothing in M8's deferred set was built or decided against. **Its standing law survives** in [ADR-POSTINGS](../docs/adr/0013_postings.md) §Consequences: pruning work is forbidden outside a dedicated item, because [P1-RERUN](../work/regression/2026-08-09-pruning-rerun/VERDICT.md) measured a **35.9-point recall loss** and that is what put *full postings, permanently* into the record. The parked idea itself lives on as [`query-log-pruning.md`](../work/proposals/query-log-pruning.md) |

| [`W-63-source-verbs.md`](open/W-63-source-verbs.md) | 2026-08-21 | **Completed — built, captured and released in `v0.35.0`.** Live successors: [`src/fux/sources.py`](../src/fux/sources.py) (the three verbs and the writer for all three lists) and the reconciliation + edge-revalidation in [`src/fux/ingest/run.py`](../src/fux/ingest/run.py). The decisions are [ADR-CLI](../docs/adr/0002_cli-surface.md) **1a-1e**, [ADR-INGEST](../docs/adr/0007_ingest.md) **9-10** and [ADR-DIR-LIST](../docs/adr/0022_dir-list.md) **2d-2e, 3a**; six further records were amended in the same change for the L4 sweep. The surface is captured at [`2026-08-21-source-verbs`](../work/regression/2026-08-21-source-verbs/report.md), and the four defects that capture found — three of them in W-63 itself — are in its [ANALYSIS](../work/regression/2026-08-21-source-verbs/ANALYSIS.md). **Both open calls were taken on the defaults this file pre-authorised**: `fux url` deleted outright, `ingest --refresh-urls` hidden for one release. **One DoD line was deliberately not met** and says so — the checklist wanted `--refresh-urls` gone, and the file's own open question said to keep it a release |
| [`W-64-progress-plane.md`](open/W-64-progress-plane.md) | 2026-08-21 | **Completed — built, captured and recorded.** Live successor: [`src/fux/progress.py`](../src/fux/progress.py), plus the `progress=None` seams on `ingest.run()` and `derive.build()`; the decision is [ADR-CLI](../docs/adr/0002_cli-surface.md) **decision 9**, with ADR-INGEST, ADR-T1-ACCELERATOR and ADR-MAINTENANCE amended in the same change per Law zero. The invariant — stdout byte-identical with the bar on or off — is asserted per write verb in `tests_e2e/test_progress_surface.py`; the surface is captured at [`2026-08-21-progress-plane`](../work/regression/2026-08-21-progress-plane/report.md). **The hook question was decided on its stated default** (show it, `FUX_NO_PROGRESS=0`). **That fork landed on B on 2026-08-22**, so the one-line reversal is now live work and belongs to [W-66](../work/open/W-66-deferred-hook.md): a deferring `post-commit` returns in ~0.2 s and a bar that flashes that briefly is noise. **Repaint cost at 100 000 documents is unmeasured** and belongs to [W-26](../work/open/W-26-m6-scale-t2.md) |

| [`W-60-refer-fetch-cache.md`](open/W-60-refer-fetch-cache.md) | 2026-08-20 | **Completed — verdict F built.** Live successors: [`refer/fetchcache.py`](../src/fux/refer/fetchcache.py) and the `cached` verdict in [`refer/freshness.py`](../src/fux/refer/freshness.py); the decision is [ADR-REFER](../docs/adr/0030_refer-plane.md) 5a-5c and 6, amended in the same change per Law zero. Both hazards it named are honoured and tested: `cached` never renders as `current`, and the TTL store is provably separate from ARC's keyspace |

Every outcome is recorded in
[`work/IMPLEMENTATION.md`](../work/IMPLEMENTATION.md) — §Ratified decisions for
the human calls, §Defects closed outside a milestone for the rest, and the
milestone table for the milestones.

## Retired planning documents

| artifact | retired | live successors |
|---|---|---|
| [`PLAN-v0.30.md`](PLAN-v0.30.md) | 2026-08-18, on Arpit's instruction | **Milestone scope** → the item's own detail file under [`work/open/`](../work/open/README.md) (M3→W-23 … M8→W-38), migrated verbatim · **what shipped** → [`work/IMPLEMENTATION.md`](../work/IMPLEMENTATION.md) · **predictions** → [`work/OPEN-WORK.md`](../work/OPEN-WORK.md) · **the port list** → [ADR-PORT-LIST](../docs/adr/0015_port-list.md) · **risks and the process contract** → [`CLAUDE.md`](../CLAUDE.md) and [`work/INTERVIEW.md`](../work/INTERVIEW.md) §standing constraints |
| [`PRIORITY.md`](PRIORITY.md) | 2026-08-21, on Arpit's instruction — every row (P1–P8) resolved | **The ranked P1–P8 list** → [`work/OPEN-WORK.md`](../work/OPEN-WORK.md), which it was always a temporary, Arpit-ordered override *of* (CLAUDE.md's own text calls `OPEN-WORK.md` "the single live queue"; `PRIORITY.md` existed for one audit-driven pass, 2026-08-20–2026-08-21). **P1–P7's outcomes** → [`work/IMPLEMENTATION.md`](../work/IMPLEMENTATION.md) (one row each, with commit shas). **P8** → carried forward as [`archive/open/W-62-measure-against-the-outside-world.md`](open/W-62-measure-against-the-outside-world.md) — **withdrawn 2026-08-22, not completed**, not resolved, just rehomed. **P7's process-diet candidates** → [`work/proposals/process-diet.md`](../work/proposals/process-diet.md), Arpit's verdict on each. |

Both retired documents' content was migrated **before** each moved, so no
live item was left citing an archived one. The design of record is now the
ADR register plus the open queue: decisions in
[`docs/adr/`](../docs/adr/README.md), scope in
[`work/OPEN-WORK.md`](../work/OPEN-WORK.md) and the item that will build it.

## Old builds

| entry | what it is |
|---|---|
| [`v0.1/`](v0.1/) | the first build (pre-reset #1) |
| [`v0.26/`](v0.26/) | the v0.19–0.26 substrate engine — runnable, reference-only, never modified, never imported; M1's eval baseline |
| [`v0.26-docs/`](v0.26-docs/) | that engine's documentation: ADRs 0001–0015 (always cited as **"archived ADR-NNNN"** *with this path*), compare docs, tracker |
| [`v0.26-implemented/`](v0.26-implemented/) | the v0.26 line's implemented artifacts: master-prompt, `PLAN-v0.26.md`, every executed pair v0.20→v0.26 |
| [`v0.30-rev1-planning/`](v0.30-rev1-planning/) | the rebuild's research phase: both gate handoff pairs (→ ADR-PRUNING-GATE / ADR-PRUNING-RERUN) and the superseded rev-1 diagrams |

---

## History — the two rulings

**2026-08-10.** The v0.26 doc set used to sit nested inside a second archive
under `docs/`. Arpit ruled that everything belonging to an old build lives at
the repo root, and it moved to [`v0.26-docs/`](v0.26-docs/). That ruling scoped
the v0.26 doc set; a second archive continued to exist for completed doc
artifacts of the current build.

**2026-08-18.** The `work/` restructure carried that second archive along as
`work/archive/`, which is exactly the split the first ruling was aimed at.
Arpit restated the rule in its general form — **one archive, at root, and
anything archived moves here** — and `work/archive/` was dissolved into this
directory. There is no longer a second place to look.

The 2026-08-10 discrepancy is recorded rather than deleted because
[ADR-RECORD](../docs/adr/0010_index-record.md) §Consequences cites it as
the reason R2 question 3 could not be answered at M1.

## Proposals archived 2026-08-22

| file | archived | why |
|---|---|---|
| [`proposals/consumer-intent-policy.md`](proposals/consumer-intent-policy.md) | 2026-08-22 | **Graduated and built.** Became [ADR-AGENT-POLICY](../docs/adr/0035_agent-policy.md); `fux setup` installs the four renderings, which live at [`src/fux/templates/agents/`](../src/fux/templates/agents/). Its `consumer-policy/` drafts directory came with it — by then only a pointer, since the files had already moved into the wheel |
| [`proposals/process-diet.md`](proposals/process-diet.md) | 2026-08-22 | **Graduated 2026-08-21** (PRIORITY P7) and the change is live in the process: the `Cost:` line left the WORKLOG format after 58/58 entries said `unmeasured` |
| [`proposals/consumer-policy-README.md`](proposals/consumer-policy-README.md) | 2026-08-22 | the drafts directory's index, kept only so the pointer it carried is not lost |
