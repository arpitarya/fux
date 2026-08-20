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
| [`v0.32.0-ratification-package.md`](handoff/v0.32.0-ratification-package.md) | the five Lane B decisions packaged for one sitting | [W-31](open/W-31-ratify-adr-0010-0011.md) · [W-33](open/W-33-adr-numbering-contradiction.md) · [W-44](../work/open/W-44-archived-content-signalling.md) — **each states its own decision now**. W-30 and W-32 closed 2026-08-19; their files are in [`open/`](open/) |
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

| [`W-54-sources-rewrite.md`](open/W-54-sources-rewrite.md) | 2026-08-19 | **Completed.** All five merged defects closed in five commits, each with its records. Live successors: the code is [`ingest/sourcelist.py`](../src/fux/ingest/sourcelist.py) · [`setup.py`](../src/fux/setup.py) · [`sources.py`](../src/fux/sources.py) · [`templates/`](../src/fux/templates/); the decisions are [ADR-URL-LIST](../docs/adr/0018_url-list.md) · [ADR-DIR-LIST](../docs/adr/0023_dir-list.md) · [ADR-FETCHER](../docs/adr/0019_fetcher.md) · [ADR-HTTP-FETCHER](../docs/adr/0021_http-fetcher.md) · [ADR-INDEX-LIFECYCLE](../docs/adr/0009_index-lifecycle.md) decision 9; the evidence is [`2026-08-19-w54`](../work/regression/2026-08-19-w54/report.md). **One section was overruled by a record**: §5 describes a verb that fetches, and ADR-CLI's captured surface makes `--refresh-urls` the only networked path (L4) — `fux url` records and never fetches |

| [`W-46-hybrid-missing-model-crash.md`](open/W-46-hybrid-missing-model-crash.md) | 2026-08-20 | **Completed.** Live successor: the `None` guard in [`query/hybrid.py`](../src/fux/query/hybrid.py) and its two tests in [`tests/derive/test_dense_and_hybrid.py`](../tests/derive/test_dense_and_hybrid.py); the decision is [ADR-CLI](../docs/adr/0002_cli-surface.md). **One deviation from its definition of done**: the regression test landed beside the other hybrid tests rather than in `tests/query/`, because duplicating the corpus fixture into a second directory costs more than the path documents |

| [`W-48-query-output-contract.md`](open/W-48-query-output-contract.md) | 2026-08-20 | **Completed — two of three fixed, the third decided.** Live successors: `cmd_ask` and `cmd_answer` in [`query/__init__.py`](../src/fux/query/__init__.py), pinned by [`tests_e2e/test_verbs.py`](../tests_e2e/test_verbs.py); the decisions are [ADR-ASK](../docs/adr/0004_ask.md) and [ADR-ANSWER](../docs/adr/0006_answer.md). Item 3 — `find`'s prose no-match line — was **left alone deliberately** and is now pinned by a test, so the call is visible rather than remembered |

| [`W-23-m3-graph-lane.md`](open/W-23-m3-graph-lane.md) | 2026-08-20 | **Completed — with two of its definition-of-done items carried forward rather than claimed.** Live successors: the code is [`src/fux/graph/`](../src/fux/graph/); the decision is [ADR-GRAPH](../docs/adr/0030_graph-lane.md); the eval is [`tests_e2e/test_relational.py`](../tests_e2e/test_relational.py) with its corpus at [`tests_e2e/eval/`](../tests_e2e/eval/). **What it did not deliver**, both now [W-57](../work/open/W-57-graph-lane-acceptance.md): the playground acceptance targets `q005`/`q009`/`q011`/`q015` are unmeasured because `fux-playground` does not exist on this machine ([W-56](../work/open/W-56-sibling-environments-missing.md)), and community determinism is verified on one machine rather than the two it asked for |

| [`proposals/caller-set-freshness-policy.md`](proposals/caller-set-freshness-policy.md) | 2026-08-20 | **Implemented, with its central knob refused.** Live successor: [ADR-REFER](../docs/adr/0031_refer-plane.md) decisions 4-8 and [`src/fux/refer/freshness.py`](../src/fux/refer/freshness.py). The caller-owned policy and the `never` sentinel shipped; **`max_age_seconds` did not** — the committed record carries no ingest time, so the bound could not have been honoured, and a knob that lies is worse than a missing one. Content verification replaced it. The open question it leaves is [W-58](../work/open/W-58-no-recorded-ingest-time.md) |

| [`proposals/token-budget-retrieval.md`](proposals/token-budget-retrieval.md) | 2026-08-20 | **Implemented.** Live successor: [ADR-REFER](../docs/adr/0031_refer-plane.md) decisions 10-13 and [`src/fux/refer/assemble.py`](../src/fux/refer/assemble.py). Byte budget primary, `k` secondary, deterministic ties, per-document cap — plus a floor the proposal did not anticipate, because greedy score-per-byte is systematically biased toward short passages |

| [`W-24`'s two graduating proposals](proposals/) | — | Both successors sit in a record that is **`proposed`, not accepted**: R4 has not run ([W-59](../work/open/W-59-refer-plane-measurement.md)). Named here so a reader does not take archival as ratification |

| [`W-45-source-exclusion.md`](open/W-45-source-exclusion.md) | 2026-08-20 | **Completed — verdict E built.** Live successors: [ADR-DIR-LIST](../docs/adr/0023_dir-list.md) decisions 2a-2c, and the `!` grammar in [`ingest/sourcelist.py`](../src/fux/ingest/sourcelist.py) with `_excluded_by` in [`ingest/gitdir.py`](../src/fux/ingest/gitdir.py). The verdict **overrode the record's own anticipation** — an exclusion is an *entry*, not the attribute ADR-DIR-LIST expected. The measurement that killed the dot-prefix alternative (2 of 7 runs followed it) is in [`source-exclusion.compare.md`](../work/compare/source-exclusion.compare.md), which is live |

| [`W-55-no-file-type-filter.md`](open/W-55-no-file-type-filter.md) | 2026-08-20 | **Completed — verdict G built.** Live successor: [ADR-TYPES](../docs/adr/0032_types-list.md), and `DEFAULT_TYPES` / `read_types` in [`ingest/gitdir.py`](../src/fux/ingest/gitdir.py). Landed **in the same change as W-45** because both change one file format. ⚠ **the ranking half is unmeasured and this repo was deliberately not re-ingested** — that step rides with [W-52](../work/open/W-52-df-over-the-union.md) |

Every outcome is recorded in
[`work/IMPLEMENTATION.md`](../work/IMPLEMENTATION.md) — §Ratified decisions for
the human calls, §Defects closed outside a milestone for the rest, and the
milestone table for the milestones.

## Retired planning documents

| artifact | retired | live successors |
|---|---|---|
| [`PLAN-v0.30.md`](PLAN-v0.30.md) | 2026-08-18, on Arpit's instruction | **Milestone scope** → the item's own detail file under [`work/open/`](../work/open/README.md) (M3→W-23 … M8→W-38), migrated verbatim · **what shipped** → [`work/IMPLEMENTATION.md`](../work/IMPLEMENTATION.md) · **predictions** → [`work/OPEN-WORK.md`](../work/OPEN-WORK.md) · **the port list** → [ADR-PORT-LIST](../docs/adr/0015_port-list.md) · **risks and the process contract** → [`CLAUDE.md`](../CLAUDE.md) and [`work/INTERVIEW.md`](../work/INTERVIEW.md) §standing constraints |

Its content was migrated **before** it moved, so no live item was left citing
an archived document. The design of record is now the ADR register plus the
open queue: decisions in [`docs/adr/`](../docs/adr/README.md), scope in the
item that will build it.

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
