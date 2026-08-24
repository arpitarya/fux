---
okf_version: "0.1"
---

# Fux docs — knowledge bundle root (v0.30 rebuild)

The bundle is **`docs/` + `work/`**, and this index spans both. It was one tree
until 2026-08-18; the split does not change the bundle, only its shape:

- **`docs/`** — what the project **is**: the plan, the glossary, the ADR
  register.
- **[`work/`](../work/README.md)** — what is **happening to it**: the session
  memory, the queue, the evidence, and every doc currently mid-rewrite.

Every lowercase knowledge doc carries frontmatter with a `type`; this index
gives progressive disclosure. ALL-CAPS docs (`OPEN-WORK.md`,
`INTERVIEW.md`, `IMPLEMENTATION.md`, `WORKLOG.md`, `MACHINE.md`, `GLOSSARY.md`,
`DOC-REGISTRY.md`) plus repo-root `CLAUDE.md`/`README.md` are
entry-point/tracker files, exempt from the `type` requirement by repo
convention. Large docs carry two sections — *For humans* then *For AI agents* —
update both or neither.

# Core (read in this order)

* [The ADR register](adr/README.md) - the decisions of record. `PLAN.md` was archived 2026-08-18; milestone scope now lives in the item that will build it, under [`work/open/`](../work/open/README.md).
* [Open work](../work/OPEN-WORK.md) - **the single live queue**, two concurrent lanes; finished items are deleted, not ticked.
* [Implementation](../work/IMPLEMENTATION.md) - the milestone log: what shipped, when, and the outcome. What OPEN-WORK reconciles against.
* [The paper](../work/paper/the-fux-index-paper.md) - the architecture of record, with figures and falsifiable predictions.
* [High-level diagram](../work/architecture-high-level.svg) - what fux is, in three boxes, for someone who has never seen it · [detailed diagram](../work/architecture-detailed.svg) - the mechanism: record shape, both retrieval paths, the two planes and the laws that separate them.
* [Model handoff interview](../work/INTERVIEW.md) - the state of play; read before substantive changes.
* [Worklog](../work/WORKLOG.md) - per-exchange session trail, newest first.
* [Machine notes](../work/MACHINE.md) - what breaks on which surface, and why.
* [Doc registry](../work/DOC-REGISTRY.md) - maintained docs, update triggers, last-verified dates.
* [Glossary](GLOSSARY.md) - recurring terms, defined once.

# Decisions

**A record's directory is its state** - `docs/adr/` live · `work/adr/`
superseded-pending (in force, citable, replacement planned) ·
`archive/adr/` superseded, and archive is never evidence.

* [The ADR register](adr/README.md) - the convention, the ownership table, and the state of every record. **Records are cited by NAME, never by number.**
* [ADR-LAWS](adr/0001_laws.md) - the non-negotiable constraints have exactly one home; no record restates them.
* [ADR-CLI](adr/0002_cli-surface.md) - the command-line surface: six verbs, one boundary, three output modes, every command captured verbatim.
* [ADR-ASK](adr/0004_ask.md) - the `ask` verb: one scorer, one sort, two candidate generators that can never disagree. ⏳ proposed.
* [ADR-FIND](adr/0005_find.md) - the `find` verb: one line per hit, for pipes; the same ranking as `ask`. ⏳ proposed.
* [ADR-ANSWER](adr/0006_answer.md) - the `answer` verb: bounded by what the index holds, and it says so in every response. ⏳ proposed.
* [ADR-RECORD](adr/0010_index-record.md) - one line of the committed index, property by property. ⏳ proposed.
* [ADR-T1-ACCELERATOR](adr/0011_accelerator.md) - the derived index: disposable, term-major, forbidden from changing an answer. ⏳ proposed.
* [ADR-RANKING](adr/0012_ranking.md) - BM25F, weight-then-saturate once, one scorer and one rounded sort. ⏳ proposed.
* [ADR-POSTINGS](adr/0013_postings.md) - the postings in two shapes, and why git gets the doc-major one. ⏳ proposed.
* [ADR-CONFIG](adr/0014_config.md) - `fux.toml` and every property in it. ⏳ proposed.
* [ADR-DOTFUX](adr/0003_fux-directory.md) - the `.fux/` directory: every child declared committed or derived, the ignore rule asserted against git. ⏳ proposed.
* [ADR-INGEST](adr/0007_ingest.md) - how ingest works: re-extract everything, re-resolve every edge, write only what changed. ⏳ proposed.
* [ADR-URL-INGEST](adr/0008_url-ingest.md) - URL ingestion through consumer-owned fetcher; fux never fetches. ⏳ proposed.
* [ADR-INDEX-LIFECYCLE](adr/0009_index-lifecycle.md) - index generation and update, and the derived plane that refuses to diverge. ⏳ proposed.
* [The retired v0.30 set](../archive/adr/README.md) - five records, archived 2026-08-18, each mapped to its live successor. **Named, never cited** — archive is not evidence.
* [Compare docs](../work/compare/README.md) - the v0.30 forks, verdict at the top of each, every one with a reopen-trigger.
* [Proposals](../work/proposals/README.md) - parked ideas with graduation triggers.

# Build

* [Handoffs](../archive/README.md) - **the handoff directory was retired 2026-08-18**; its contents are in `archive/handoff/`. A spec for open work now lives in that item's detail file under [`work/open/`](../work/open/README.md).
* [Regression evidence](../work/regression/README.md) - every measurement run: report + ANALYSIS + raw evidence. This is what other docs cite as grounding.
* [`tools/pruning-eval/`](../tools/pruning-eval/README.md) - M1's gate: the frozen [pre-registration](../tools/pruning-eval/PRE-REGISTRATION.md), the KL selector, the harness.
* [Archive](../archive/) - **old builds live in the root archive** (Arpit's ruling, 2026-08-10): [v0.1](../archive/v0.1/) · [v0.26 engine](../archive/v0.26/) · [v0.26 docs](../archive/v0.26-docs/) · [v0.26 implemented](../archive/v0.26-implemented/) · [v0.30 rev-1 planning](../archive/v0.30-rev1-planning/). Completed **doc artifacts** of the current build live in [`archive/`](../archive/README.md) instead.
