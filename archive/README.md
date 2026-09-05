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
  templates/             retired shipped-fetcher code, lifted out of src/fux/templates/
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
| [`W-98-acquired-plane-handoff.md`](handoff/W-98-acquired-plane-handoff.md) · [prompt](handoff/W-98-acquired-plane-prompt.md) · [the refusal starter](handoff/W-98-refusals-starter.toml) | all four phases landed 2026-09-01 | [ADR-ACQUIRED](../docs/adr/0050_acquired-plane.md) · [ADR-REFUSAL](../docs/adr/0051_refusals.md) · [ADR-URL-FRESHNESS](../docs/adr/0052_url-freshness.md) — ⚠ **the pair was written into `work/handoff/`, a directory retired on 2026-08-18**, and `tests/test_archive_law.py` was red for a day because of it. The spec it carried lives in [W-98](../work/open/W-98-acquired-plane.md); the shipped refusal starter is `src/fux/templates/refusals.toml.txt`, and this copy is the frozen original |

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
| [`W-98-acquired-plane.md`](open/W-98-acquired-plane.md) | 2026-09-01 | **All four phases landed**: the browser fetcher returns the intercepted resource, declarative refusal detection, the clock-free `.fux/acquired/` plane, and `ttl=` with the sixth `as-ingested` verdict. Live successors: [ADR-CDP-FETCHER](../docs/adr/0020_cdp-fetcher.md) · [ADR-REFUSAL](../docs/adr/0051_refusals.md) · [ADR-ACQUIRED](../docs/adr/0050_acquired-plane.md) · [ADR-URL-FRESHNESS](../docs/adr/0052_url-freshness.md). ⚠ **Two of its own claims were WRONG and are worth knowing**: the in-page `fetch(url, {credentials:'include'})` the spec prescribed could never have worked (CORS/CSP are page-level, CDP is not — so `ETag` was invisible and `validate()` undeliverable), and its guess that `cdp.py`'s `HTMLParser`/`urljoin` were dead code was ruled the other way. ⚠ **Its Phase 2 spec was CUT, not built** — four conditions would have put HTTP facts inside the engine, which [ADR-FETCHER](../docs/adr/0019_fetcher.md) decision 13 forbids |
| [`W-30-ratify-adr-0001.md`](open/W-30-ratify-adr-0001.md) | 2026-08-19 | Arpit ratified the ingest-mode naming → [ADR-EXTRACTED](../docs/adr/0016_extracted-mode.md) · [ADR-ENRICHED](../docs/adr/0017_enriched-mode.md), both accepted. The file's own "**Non-blocking**" note was **wrong**: `mode` is a committed wire-format value, so the *reversal* cost rises with every index written |
| [`W-32-claude-md-adoption.md`](open/W-32-claude-md-adoption.md) | 2026-08-19 | Arpit adopted the M0a rewrite → the live [`CLAUDE.md`](../CLAUDE.md), PROPOSED header deleted. The file's "Correction (2026-08-12): there is no `CLAUDE.md.proposed`" was **wrong as history** — the file existed at `bed2186` and was implemented into `CLAUDE.md` at `3892c55`; `git log --follow` cannot see a delete-plus-overwrite, so a *verified* claim rested on evidence that could not show it |

| [`W-31-ratify-adr-0010-0011.md`](open/W-31-ratify-adr-0010-0011.md) | 2026-08-19 | Arpit ratified all three as-is → [ADR-DOTFUX](../docs/adr/0003_fux-directory.md) · [ADR-URL-INGEST](../docs/adr/0008_url-ingest.md) · [ADR-CONFIG](../docs/adr/0014_config.md), and confirmed `.fux/README.md` is generated at **ingest** time. Two of its three DoD items had already been satisfied by unrelated changes; the third named the wrong section of `CHANGELOG.md` |

| [`W-33-adr-numbering-contradiction.md`](open/W-33-adr-numbering-contradiction.md) | 2026-08-19 | Arpit confirmed the convention: **`docs/adr/` is the live set and starts at 0001; the records under `archive/` are archived.** Every mechanical item had already been satisfied by other changes. Its live consequence — four items reserving numbers that accepted records already held — was swept to **names** in the same change |

| [`W-47`](open/W-47-hashed-meta-blocks-accelerator.md) · [`W-49`](open/W-49-url-fragment-truncation.md) · [`W-50`](open/W-50-url-fetch-mechanism.md) · [`W-51`](open/W-51-fetcher-template-not-shipped.md) · [`W-53`](open/W-53-dirs-file.md) | 2026-08-19 | **Merged, not completed**, into [`W-54`](open/W-54-sources-rewrite.md) on Arpit's call. All five rewrite one parser and one generated set, and each carried a hazard saying *land it with the others* — five definitions of done for one change. **They are still five defects**; their analysis lives here and W-54 is the work order |

| [`W-54-sources-rewrite.md`](open/W-54-sources-rewrite.md) | 2026-08-19 | **Completed.** All five merged defects closed in five commits, each with its records. Live successors: the code is [`ingest/sourcelist.py`](../src/fux/ingest/sourcelist.py) · [`setup.py`](../src/fux/setup.py) · [`sources.py`](../src/fux/sources.py) · [`templates/`](../src/fux/templates/); the decisions are [ADR-URL-LIST](../docs/adr/0018_url-list.md) · [ADR-DIR-LIST](../docs/adr/0022_dir-list.md) · [ADR-FETCHER](../docs/adr/0019_fetcher.md) · [ADR-HTTP-FETCHER](../docs/adr/0021_http-fetcher.md) · [ADR-INDEX-LIFECYCLE](../docs/adr/0009_index-lifecycle.md) decision 9; the evidence is [`2026-08-19-w54`](../work/regression/2026-08-19-w54/report.md). **One section was overruled by a record**: §5 describes a verb that fetches, and ADR-CLI's captured surface makes `--refresh-urls` the only networked path (L4) — `fux url` records and never fetches |

| [`W-109-expand-and-multiquery.md`](open/W-109-expand-and-multiquery.md) | 2026-09-05 | **Completed in full, and its gate cleared 16-0.** Live successors: the code is [`src/fux/query/expand.py`](../src/fux/query/expand.py) and [`src/fux/query/fuse.py`](../src/fux/query/fuse.py) (with the guard in [`rank.py`](../src/fux/query/rank.py) and the bound in [`accel.py`](../src/fux/derive/accel.py)); the decision is [ADR-EXPAND](../docs/adr/0054_expand.md); the measurement is [`2026-09-05-expand`](../work/regression/2026-09-05-expand/report.md). ⚠ **Two things its DoD asked for that the run does NOT establish**, both stated in the run rather than quietly closed: `-q` fusion has unit tests and **no graded run**, and `expand_weight = 0.2` is a literature default **no measurement here has tested**. Both carried to [W-97](../work/open/W-97-tuner-knob-sweep.md) and the queue |

| [`W-108-answer-top3.md`](open/W-108-answer-top3.md) | 2026-09-05 | **Completed in full.** Live successors: the code is [`src/fux/query/__init__.py`](../src/fux/query/__init__.py) (`ANSWER_TOP`, `_answer_via_refer`), [`src/fux/query/refer_answer.py`](../src/fux/query/refer_answer.py) (`_load_fetchers`) and [`src/fux/refer/_rescore.py`](../src/fux/refer/_rescore.py); the decisions are [ADR-ANSWER](../docs/adr/0006_answer.md) 11-13, [ADR-REFER](../docs/adr/0030_refer-plane.md) 21-22, [ADR-RERANK](../docs/adr/0041_rerank.md) 9 and [ADR-CONFIDENCE](../docs/adr/0045_confidence.md) 14; the measurement is [`2026-09-05-answer-top3`](../work/regression/2026-09-05-answer-top3/report.md). ⚠ **One hazard in its own DoD was refuted rather than met** — *"assembled bytes never exceed today's for the same query"* is false on 43 of 43, by design: it conflated the byte *bound* (unchanged, never exceeded) with the byte *spend* (up 157 %). Recorded in ADR-ANSWER decision 13 |

| [`W-46-hybrid-missing-model-crash.md`](open/W-46-hybrid-missing-model-crash.md) | 2026-08-20 | **Completed.** Live successor: the `None` guard in [`query/dense.py`](../src/fux/query/dense.py)'s `query_vector()` and its test in [`tests/derive/test_dense_and_hybrid.py`](../tests/derive/test_dense_and_hybrid.py) (`test_ask_hybrid_exits_zero_on_a_source_install`); the decision is [ADR-CLI](../docs/adr/0002_cli-surface.md). **One deviation from its definition of done**: the regression test landed beside the other dense-lane tests rather than in `tests/query/`, because duplicating the corpus fixture into a second directory costs more than the path documents. ⚠ **Re-homed 2026-08-26 (W-79)**: the fix originally landed in `query/hybrid.py`, which W-79 deleted as dead code (off the live path since W-76 Phase 7); the guard it described now lives in `query/dense.py`, the module `--hybrid` actually calls |

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
| [`W-79-remove-the-dead-fusion-code.md`](open/W-79-remove-the-dead-fusion-code.md) | 2026-08-26 | **Ruled delete, built the same day.** Live successors: [ADR-TUNE](../docs/adr/0038_tuning.md) (the `[fuse]` table removed from the closed key set — six tables, not seven) · [ADR-CLI](../docs/adr/0002_cli-surface.md) (`explain --no-tune` removed) · [ADR-ASK](../docs/adr/0004_ask.md) (decision 9's RRF clause corrected: the module that did RRF is gone). `src/fux/query/hybrid.py` is deleted; `tools/differential/playground_grade.py`'s `"hybrid"` mode now calls `fux.query.run_query(..., use_hybrid=True)`, the same path `fux ask --hybrid` takes. Evidence: [`IMPLEMENTATION.md`](../work/IMPLEMENTATION.md)'s W-79 row |
| [`W-76-DECISIONS.md`](open/W-76-DECISIONS.md) | 2026-08-24 | **D1-D30, every call taken in Arpit's absence during W-76.** Retired with its item. Live successor for any decision that became binding: the record it landed in, above. Kept because the reasoning is worth more than the ruling alone — and because four of the thirty are still owed a ratification, tracked by [W-77](../work/open/W-77-record-reconciliation.md) |
| [`W-62-measure-against-the-outside-world.md`](open/W-62-measure-against-the-outside-world.md) | 2026-08-22 | **WITHDRAWN by Arpit, not completed** — *"the whole w sixty two, remove it, cancel it out. That's on me."* Part 3 (the public README) **was** completed and is the only live successor: two false statements of fact fixed. Parts 1 and 2 — the three-way comparison and five external installs — are **cancelled and personally owned by Arpit**, and no agent should re-file them. ⚠ **The question is not answered**: whether Fux wins on private organisational documents is still untested. **Id retired, not reused** |
| [`compare/`](compare/README.md) — **four closed forks** | 2026-08-25 | **`wire-format`, `keyspace-unification`, `pruning-criterion`, `r7-size-budget`.** A decided fork stays in `work/compare/` because the doc carries its **reopen-trigger**; these four moved because the trigger can no longer fire — two depend on **T2, which was declined on measurement** (R9 PASS, 12x inside its bar), one is **forbidden** by ADR-POSTINGS decision 8, and one forks over the shape of **R7, which was retired with no successor**. Per-doc reasons in [`compare/README.md`](compare/README.md) |
| [`proposals/ideal/`](proposals/ideal/README.md) — **the whole nine-file design review** | 2026-08-25 | **Closed: every one of its nine build-order steps is resolved.** Built: 1 (analyzer v2), 2 (supersession + recency priors), 5 (MCP + line-range citations), 6 as *proximity* reranking, 8 (`fux enrich`). **Refused by Arpit** ([`07-rulings.amendment.md`](proposals/ideal/07-rulings.amendment.md) ruling 1, *"A fresh clone not having an index does not work for me. That part is a big no."*): steps 4 and 9, and with them [`01-index-location`](proposals/ideal/01-index-location.compare.md). **Decided NOT to build on a measurement:** step 3, delta hooks — [the R5 re-run](../work/regression/2026-08-23-r5-rerun-after-code-removal/report.md). **Moot:** step 7 and [`03-semantic-lane`](proposals/ideal/03-semantic-lane.compare.md), whose every artifact was deleted on 2026-08-25, and the cross-encoder half of [`04-model-in-the-loop`](proposals/ideal/04-model-in-the-loop.compare.md), refused by ADR-RERANK. ⚠ **The set is archived whole rather than split** — its rulings file only makes sense beside the documents it rules on. ⚠ **One thing in it was never done and is NOT recorded elsewhere:** ruling 2 proposed a *"Sufficiency"* law, and `CLAUDE.md` still lists only **L1-L7** |
| [`proposals/query-log-pruning.md`](proposals/query-log-pruning.md) | 2026-08-25 | **Moot — it extends a selector that may not be built.** It proposed a committed `.fux/query-views.jsonl` giving the pruning selector a rule that exempts queried terms from the budget. P1-RERUN closed **FAIL** and full postings shipped permanently; ADR-POSTINGS decision 8 forbids pruning work outside a dedicated item, and that item was dropped. ⚠ **The idea underneath survives elsewhere** — query-log-as-asset is load-bearing in `measuring-answer-quality.md` fork 6 and `ranking-tuning.md` §8, both still live |
| [`W-93-benchmark-v1-vs-head.md`](open/W-93-benchmark-v1-vs-head.md) | 2026-08-28 | **Closed by execution — the version benchmark ran.** Arpit asked for a benchmark of fux version one against the latest; the item was blocked on a harness that did not exist, three corpus structures the generator did not plant, and per-query rows nothing emitted. All three were built. Live successors: the run at [`2026-08-28-benchmark-v1-vs-head`](../work/regression/2026-08-28-benchmark-v1-vs-head/report.md) with its seven verdicts, the frozen [pre-registration](../work/benchmark/PRE-REGISTRATION-V1-VS-HEAD.md) (`HEAD` sha written in before the first command ran), [SETUP-BENCHMARK](../work/setup/fux-benchmark.md) corrected to what was actually stood up, and `tests/test_regression_runs.py`'s per-query-rows gate. 🔴 **Every pre-registered paired test returned a discordant count of ZERO** — and the two findings are about the instrument and a default, not about the engines: the primary endpoint was **saturated** (`hit@5` 240/240 in both arms, so a power table sized a set that could not express any effect), and **B2 FAILED its predicted PASS because `superseded_weight` ships at `1.0`** — post-hoc at `0.5` the same arm goes 21/40 inversions → 0/40. ⚠ **Filed `informed`** by the pre-registration's own §3: one session wrote the generator and read the scores. ⚠ **B4 and B8 were never defined** — the item and the register both said *"thresholds B1–B9"* and the frozen document has seven |
| [`W-88-the-skip-notice.md`](open/W-88-the-skip-notice.md) | 2026-08-27 | **Closed the day it was filed, and it never held an OPEN-WORK row** — nothing was pending between the ask and the landing. Arpit: *"showing it the first time is okay — showing it again and again is not okay."* `fux ingest` reported every skip on **every** run, which on a hook-driven corpus is tens to hundreds of identical lines each time. **The rule stays and the repetition goes**: a skip prints the first time it is seen, a later run prints only what is new plus one counted line naming both escape hatches. Live successors: [`src/fux/ingest/skipnotice.py`](../src/fux/ingest/skipnotice.py) (the `.fux/runtime/skipped` notice — derived, gitignored, sorted, **no wall clock**), its one call site in [`ingest/__init__.py`](../src/fux/ingest/__init__.py), and [`tests/ingest/test_skipnotice.py`](../tests/ingest/test_skipnotice.py); the decisions are [ADR-INGEST](../docs/adr/0007_ingest.md) decision 4's W-88 amendment and [ADR-DOTFUX](../docs/adr/0003_fux-directory.md), with [ADR-CLI](../docs/adr/0002_cli-surface.md) annotated as a describing-not-owning record. ⚠ **The framing that matters more than the code:** this is decision 4 *defended*, not weakened — **a wall nobody reads makes a dropped file exactly as invisible as silence would**, so nothing is suppressed that has not already been shown, and the key is `(path, reason)` so a changed reason is news again. ⚠ **An offline run may not replace the URL entries** — it consulted no URL, so it must not forget what a networked run recorded. ⚠ **The tests are unverified under `pytest`**: the build sandbox is Python 3.10 with no `pytest` and no network, so a stdlib harness with a `tomllib` shim outside the repo stood in — 12/12 green there. Someone must run `uv run pytest -q tests` on a real 3.11+ install |
| [`W-84-heading-level-ask.md`](open/W-84-heading-level-ask.md) | 2026-08-26 | **Closed the day it was filed — and the refusal in it is half the outcome.** Arpit asked whether `ask` should cite at line level. It may not: a line range on `ask` could only be computed at ingest, so one edit makes it point at the wrong lines *while looking exactly as right as before*, and it costs a positional index (2–4× the postings) against an index whose pitch is that it fits in git. **`answer` cites lines because it fetches.** What shipped instead was already committed — `phrases`, the document's headings, rendered until now by `answer --no-refer` alone. Live successors: [`src/fux/query/headings.py`](../src/fux/query/headings.py) (the selection and the normative statement of the refusal), its renderings in [`query/__init__.py`](../src/fux/query/__init__.py) and [`mcp.py`](../src/fux/mcp.py), and [`tests/query/test_headings.py`](../tests/query/test_headings.py); the decisions are [ADR-ASK](../docs/adr/0004_ask.md) decision 10 and [ADR-MCP](../docs/adr/0039_mcp.md) decision 9, both amended in the same change. ⚠ **A live defect was found on the way and fixed here**: `fux_search`'s MCP tool description claimed *"line-range citations"* it has never returned — the same wrong claim commit `ad95a24` had fixed in the human docs **earlier the same day**, surviving in the machine-facing copy. **No gate reads a tool description**; `fux_passage`'s and `fux_related`'s are still unchecked |
| [`W-85-max-parallel-is-required.md`](open/W-85-max-parallel-is-required.md) | 2026-08-26 | **Closed the day it was filed — the ruling that finished what W-83 only claimed.** Arpit, shown W-83's output: *"I wanted a property exposed. Where is that property? It should be present by default"* and **"never commented. If it is commented, throw an error that the value has to be present."** W-83 had written `#max_parallel = 4` inside an already-commented `[sources.url]` table, so a consumer opening `fux.toml` saw a comment about a number rather than a number. Live successors: `_load_url_source` in [`config.py`](../src/fux/config.py) (the key is **required** whenever `[sources.url]` exists; `UrlSource.max_parallel` has no default), `_CONFIG` in [`setup.py`](../src/fux/setup.py) (the table ships **live**), and this repo's own [`fux.toml`](../fux.toml); the decisions are [ADR-CONFIG](../docs/adr/0014_config.md) and [ADR-DOTFUX](../docs/adr/0003_fux-directory.md). ⚠ **The finding that outlives it:** `fux setup` is write-if-missing, so **a template change reaches new repos and nobody else** — W-83 believed it had shipped a config property and had shipped it to no existing user. The migration mechanism is a **loader refusal**, never a rewrite. ⚠ **One behaviour changed:** `fux add <URL>` used to record the line and refuse to fetch when `[sources.url]` was commented; in a repo scaffolded after this it fetches, and the gate moves to `.fux/sources/urls` being empty |
| [`W-83-the-unconfigured-fetch-ceiling.md`](open/W-83-the-unconfigured-fetch-ceiling.md) | 2026-08-26 | **Closed the day it was filed — built, and the item's own framing was corrected mid-build.** Arpit asked for the parallel-request count to be a stated property in `fux.toml`, *"otherwise it'll become one of a DDoS attack."* The knob had shipped with W-82 §3.3 and worked; what had not was **the default** — `DEFAULT_MAX_PARALLEL = 4` sat in `ingest/urlsrc.py` carrying the politeness rationale and **referenced by nothing**, so an unconfigured `fux update` inherited `http.py`'s declared `MAX_PARALLEL = 8`. Live successors: `resolve_parallel` in [`ingest/urlsrc.py`](../src/fux/ingest/urlsrc.py), the interpolated `max_parallel` line in [`setup.py`](../src/fux/setup.py)'s `fux.toml`, and the policy clause in [`doctor.py`](../src/fux/doctor.py); the decisions are [ADR-CONFIG](../docs/adr/0014_config.md), [ADR-FETCHER](../docs/adr/0019_fetcher.md) and [ADR-DOTFUX](../docs/adr/0003_fux-directory.md), all amended in the same change. ⚠ **The item expected to change an accepted record and did the opposite**: ADR-CONFIG's W-82 amendment **already specified** *"default 4 when a fetcher declares more"* while stating four paragraphs earlier that *"`None` means whatever the fetcher declares"* — two sentences in one amendment, contradicting each other, and the code had implemented the wrong one. ⚠ **The governance gap it surfaced is NOT fixed**: the freshness gate checks that a record was *touched*, never that it is *coherent* |
| [`W-78-enrichment-was-measured-against-its-own-answers.md`](open/W-78-enrichment-was-measured-against-its-own-answers.md) | 2026-08-25 | **Closed — both rulings made, and neither built anything.** The item existed because enrichment measured `+9` when its author had read the goldens and `+1`/`-1` blind, and a standing refusal rested on the `+9`. **Ruling 2:** the run-classification rule, accepted rewritten — live successors [ADR-RS](../docs/adr/0036_predictions.md) decisions 11-16 and `CLAUDE.md` §Conformance runs. **Ruling 1:** [ADR-RERANK](../docs/adr/0041_rerank.md) veto 1 — condition 1 **vacated**, condition 2 **restated** and falsifiable. ⚠ **Neither the compare doc's recommendation nor a reopening was taken** — the third option was, and it is the one the item's own logic demanded: withdraw an argument that has no evidence rather than replace it with another that has none. ⚠ **The cross-encoder is still refused and still unbuilt**; what changed is that the refusal is now checkable |
| [`W-80-the-bundled-model-has-no-live-recipe.md`](open/W-80-the-bundled-model-has-no-live-recipe.md) | 2026-08-25 | **Closed by DISSOLUTION, not by fix — the bundle it was about no longer exists.** The item was the embedding model's missing provenance: two live error messages and `model.json`'s `recipe` field pointed at `tools/distill/distill.py`, which is not in the repo, and the obvious repair was illegal because grounding a live claim in `archive/v0.26/` breaks archive-is-not-evidence. On 2026-08-25 Arpit removed the model outright, so there is no bundle, no `recipe` field and no error message left to be wrong. Live successors: the measurement at [`2026-08-25-model-removal`](../work/regression/2026-08-25-model-removal/report.md) and [ADR-ENRICHED](../docs/adr/0017_enriched-mode.md)'s 2026-08-25 amendment. ⚠ **Neither fork it offered was taken** — the recipe was not restored live and the provenance claim was not deleted; the subject was. ⚠ **And one of its own claims was wrong**: it cited *"ADR 0006's <=10 MB bundle budget"*, and no such budget exists in any live record — checked across `docs/`, `CLAUDE.md` and `src/`. The 7.9 MB bundle was never governed by a written size rule at all, which is a weaker starting position than the item asserted |
| [`retrieval-tuned-static-embedding.md`](proposals/retrieval-tuned-static-embedding.md) | 2026-08-25 | **Moot — it proposed swapping the bundled model, and the model is gone.** It argued for `potion-retrieval-32M` over the general-purpose `potion-base-8M`, matryoshka-truncated to dim 256 so **not one committed byte per chunk would change**. Its own two caveats are what survived contact: it would breach a size budget (⚠ which turned out not to exist) and **it would not fix `q015`**, because a better static embedding is still order-blind. That second caveat is the whole reason the lane was deleted rather than upgraded — see [the analysis](../work/regression/2026-08-25-model-removal/ANALYSIS.md) §2 |
| [`agent-hybrid-policy.md`](proposals/agent-hybrid-policy.md) | 2026-08-25 | **Moot — it was a policy for when an agent should ask for the hybrid lane, and the lane is gone** along with `ask --hybrid`, `[dense]`, the committed vectors and the model. Retired unbuilt |
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

## The 2026-08-26 consolidation — nine documents, one successor

**Arpit collapsed the open queue to a single item.** Four open items and the
five documents supporting them were replaced by
[`work/open/W-82-the-consolidated-build.md`](../work/open/W-82-the-consolidated-build.md),
which is the **live successor for every row below**.

⚠ **The two compare docs' verdicts were folded into W-82 §4 verbatim before the
move**, precisely because archiving them would otherwise have made those
verdicts uncitable. **W-82 §4 is the live home of both**, including their
reopen triggers; the files below may be named, never cited.

| file | archived | why |
|---|---|---|
| [`open/W-86-the-decoder-plane.md`](open/W-86-the-decoder-plane.md) | 2026-08-26 | **No live successor — the work is done.** All nine phases built and ten forks ruled; the decisions live in [ADR-DECODE](../docs/adr/0042_decode.md) and the outcome in [`work/IMPLEMENTATION.md`](../work/IMPLEMENTATION.md). ⚠ **Three forks were left open and moved with it** — F (a docstring decoder for source files), G (does `fux enrich` consume the queue), I (`fux decoder` as its own verb). None blocks anything; each is a new item if it is wanted. **This file may be named, never cited** |
| [`open/W-74-answer-quality-measurement-contract.md`](open/W-74-answer-quality-measurement-contract.md) | 2026-08-26 | consolidated into **W-82 §5.2**. Item still open — the move is a merge, not a close |
| [`open/W-75-url-freshness.md`](open/W-75-url-freshness.md) | 2026-08-26 | consolidated into **W-82 §3 and §5.1** |
| [`open/W-77-record-reconciliation.md`](open/W-77-record-reconciliation.md) | 2026-08-26 | consolidated into **W-82 §5.3** |
| [`open/W-81-the-sealed-set-and-the-two-controls.md`](open/W-81-the-sealed-set-and-the-two-controls.md) | 2026-08-26 | consolidated into **W-82 §3.5 and §5.4** |
| [`proposals/url-freshness.md`](proposals/url-freshness.md) | 2026-08-26 | its argument is **W-82 §2, §3 and §5.1** |
| [`proposals/measuring-answer-quality.md`](proposals/measuring-answer-quality.md) | 2026-08-26 | its argument is **W-82 §5.2** |
| [`proposals/prepare-then-ask.md`](proposals/prepare-then-ask.md) | 2026-08-26 | ⚠ **withdrawn, not merely moved.** `update --warm` and `answer --memo` were both withdrawn under W-82 §1's ruling — if every cited URL is fetched before the final answer, neither flag has a justification. What survives is **W-82 §3.4** |
| [`compare/url-refresh-trigger.compare.md`](compare/url-refresh-trigger.compare.md) | 2026-08-26 | **verdict folded into W-82 §4.1** before archiving |
| [`compare/url-fetch-concurrency.compare.md`](compare/url-fetch-concurrency.compare.md) | 2026-08-26 | **verdict folded into W-82 §4.2** before archiving; its fork was **ruled** the same day |

## Archived 2026-08-27 — the queue's own backlog of moves

*Every one of these had already been decided; only the `git mv` was
outstanding, and it was outstanding because the Cowork bridge had no shell
between 2026-08-26 and 2026-08-27. **They may be named, never cited.***

| file | archived | why |
|---|---|---|
| [`open/W-89-does-l2-reach-a-query-log.md`](open/W-89-does-l2-reach-a-query-log.md) | 2026-08-27 | **Ruled by Arpit 2026-08-27**: L2 does not reach a query log, because a query is not content — so a new law was written for it. Live successors: `CLAUDE.md` §Non-negotiable constraints (**L8**) and [ADR-LAWS](../docs/adr/0001_laws.md) decision 8. ⚠ **L8 was reverted the same day it was written** — hashing, the size bound and the stdout prohibition are gone; read the live law, never this file's version of it |
| [`open/W-92-output-defaults.md`](open/W-92-output-defaults.md) | 2026-08-27 | **Built.** Live successor: [ADR-OUTPUT](../docs/adr/0047_output-defaults.md) — `.fux/output.toml`, the closed per-verb key set, and the one precedence chain. The surface it exists for is MCP, which has no flags |
| [`proposals/answer-provenance.md`](proposals/answer-provenance.md) | 2026-08-27 | **Graduated.** Live successor: [ADR-PROVENANCE](../docs/adr/0046_provenance.md) — `ask --why`, `answer --receipt`, and `fux verify`'s four-state verdict |
| [`proposals/output-toml-is-the-only-default.md`](proposals/output-toml-is-the-only-default.md) | 2026-08-27 | **Graduated.** Live successor: [ADR-OUTPUT](../docs/adr/0047_output-defaults.md) |
| [`proposals/tune-file-and-source-priority.md`](proposals/tune-file-and-source-priority.md) | 2026-08-27 | **Graduated 2026-08-22**; the move is what was late. Live successor: [ADR-TUNE](../docs/adr/0038_tuning.md) — `.fux/tune.toml` and per-source priority in either direction |
| [`proposals/playground-goldens-draft.md`](proposals/playground-goldens-draft.md) | 2026-08-27 | **Graduated 2026-08-24** when Arpit waived the human-author rule and the 50 candidates were installed; the move is what was late. Live successor: the playground's `goldens/queries.jsonl` ([SETUP-PLAYGROUND](../work/setup/fux-playground.md)) and [ADR-QUALITY](../docs/adr/0044_quality-contract.md) |

## Archived 2026-08-28 — three items closed, and the queue cut back to what is open

*`OPEN-WORK.md` was 209 lines and most of it narrated its own history. Rule 2
says a resolved thing leaves the file entirely, so these left with it. **They may
be named, never cited.***

| file | archived | why |
|---|---|---|
| [`open/W-82-the-consolidated-build.md`](open/W-82-the-consolidated-build.md) | 2026-08-28 | **Closed — zero open forks and ruling 3 landed.** 27 forks: 18 ruled by the ledger, 6 moved to W-87 §5.2, 2 to W-87 P4 (both since built), 1 answered by the build. Narrow-by-default shipped with the widened sweep status, in that order, so rulings 3 and 10 landed together as the ruling requires. Live successors: [ADR-URL-INGEST](../docs/adr/0008_url-ingest.md) decisions 8–9 · [ADR-MAINTENANCE](../docs/adr/0032_hooks.md) decisions 12–13 · [ADR-FETCHER](../docs/adr/0019_fetcher.md) decisions 11–12. ⚠ **One claim this file was the ONLY home of moved out before it left**: answer-time verification cannot fix recall, now [ADR-URL-INGEST](../docs/adr/0008_url-ingest.md) decision 9. ⚠ **Ruling 12's mechanism is still unratified** and is an open item |
| [`open/W-82-rulings-2026-08-27.md`](open/W-82-rulings-2026-08-27.md) | 2026-08-28 | The eighteen rulings from the 2026-08-27 interview, archived with the item they rule on. ⚠ **Ruling 3 is no longer held**; ⚠ **ruling 12's detection mechanism was never Arpit's ruling** — an agent took the recommended shape and it is now load-bearing |
| [`open/W-90-the-confidence-plane.md`](open/W-90-the-confidence-plane.md) | 2026-08-28 | **Closed.** R10 ran and is [`INCONCLUSIVE`](../work/regression/2026-08-27-r10-separation-floor/VERDICT.md); its contradiction is ruled — the verdict table governs, so a non-monotone crossing is *no change* and `SEPARATION_FLOOR` stays `0.10`. `doc_coverage` ships as a published signal with the gate **ruled off** on a measurement. Live successors: [ADR-CONFIDENCE](../docs/adr/0045_confidence.md) decision 12 · [ADR-RS](../docs/adr/0036_predictions.md) decision 18. ⚠ **The verdict is unedited** — the rule is settled, the result is not overturned |
| [`open/W-91-the-provenance-plane.md`](open/W-91-the-provenance-plane.md) | 2026-08-28 | **Closed — `L8` ratified as reverted** (Arpit, 2026-08-27). Live successors: `CLAUDE.md` §Non-negotiable constraints and [ADR-LAWS](../docs/adr/0001_laws.md) decision 8. ⚠ **The AOL-2006 grounding is OVERRIDDEN, NOT REFUTED** — a later session may not cite the ratification as evidence the risk was disproved; the risk is accepted and confinement is the whole mitigation |

## Archived 2026-09-01 — the CDP fetcher stopped rendering

W-98 Phase 1 rebuilt `.fux/fetchers/cdp.py` to intercept the response rather
than render the page. The rendering path is kept rather than deleted, because
it shipped and dogfooded for two releases and its defect is instructive.

| archived | date | live successor |
|---|---|---|
| [`templates/cdp-rendering.py.txt`](templates/cdp-rendering.py.txt) | 2026-09-01 | **Superseded, not deleted.** `capture()`, and the `_call`/`_wait_event` pair that discarded every message not their own. Live successor: `src/fux/templates/cdp.py.txt` — `fetch_resource()` on `Fetch.enable`/`Fetch.getResponseBody`, with an event pump that files replies and events separately. Live record: [ADR-CDP-FETCHER](../docs/adr/0020_cdp-fetcher.md). ⚠ **The discard loop is the point of keeping it**: under interception a lost `Fetch.requestPaused` is a paused request nobody resolves, which wedges the page — the old code's shape is why the new code has a pump |
