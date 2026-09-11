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

**`docs/adr/` is the only home a record has** (Arpit, 2026-09-06). The archive
tier is gone — the retired records were deleted, not filed. A citation resolves
into this directory or it does not resolve.

* [The ADR register](adr/README.md) - the convention, the ownership table, and the state of every record. **Records are cited by NAME, never by number.** It lists all 62 live records; the entry points below are the reading order, not the set.
* [ADR-LAWS](adr/0001_LAWS.md) - the meta-rules and the index: the non-negotiable constraints have exactly one home, and no record restates them.
* The nine law records - one law, one record: [L0 authority](adr/0002_LAW-0-authority.md) · [L1 `$0`/FOSS-only](adr/0003_LAW-1-zero-cost.md) · [L2 content never durable](adr/0004_LAW-2-content-never-durable.md) · [L3 deterministic](adr/0005_LAW-3-deterministic.md) · [L4 offline by default](adr/0006_LAW-4-offline-by-default.md) · [L5 hashed meta](adr/0007_LAW-5-hashed-meta.md) · [L6 say index](adr/0008_LAW-6-say-index.md) · [L7 Python 3.11](adr/0009_LAW-7-python-311.md) · [L8 use record](adr/0010_LAW-8-use-record.md).
* [ADR-CLI](adr/0101_cli-surface.md) - the command-line surface: flat verbs in seven groups, one error boundary, three output modes, every command captured verbatim.
* [ADR-DOTFUX](adr/0102_fux-directory.md) - the `.fux/` directory: every child declared committed or derived, the ignore rule asserted against git itself.
* [ADR-ASK](adr/0103_ask.md) - the `ask` verb: one scorer, one sort; the path that answers can never change the answer.
* [ADR-FIND](adr/0104_find.md) - the `find` verb: one line per hit, for pipes; a projection of `ask`, not a second strategy.
* [ADR-ANSWER](adr/0105_answer.md) - the `answer` verb: a fetched, re-scored passage with a fresh sha, its footing stated every time, and no model on the path.
* [ADR-INGEST](adr/0106_ingest.md) - how ingest works: carry unchanged extraction forward, re-resolve every edge, write only shards whose bytes changed.
* [ADR-URL-INGEST](adr/0107_url-ingest.md) - URL ingestion behaviour: fetching only inside a named fenced path, a failed fetch is a skip not a deletion.
* [ADR-INDEX-LIFECYCLE](adr/0108_index-lifecycle.md) - index generation and update, and the derived plane that refuses to diverge.
* [ADR-RECORD](adr/0109_index-record.md) - one line of the committed index, property by property, including the conditional ones.
* [ADR-T1-ACCELERATOR](adr/0110_accelerator.md) - the derived index: disposable, term-major, forbidden from changing an answer.
* [ADR-RANKING](adr/0111_ranking.md) - BM25F, weight-then-saturate once, one scorer and one rounded sort.
* [ADR-POSTINGS](adr/0112_postings.md) - the postings in two shapes, and why git gets the doc-major one.
* [ADR-CONFIG](adr/0113_config.md) - `fux.toml` and every property in it: three tables read, two refused by name, one passed through unread.
* The remaining records - the refer plane, fetchers, decode, tuning, quality, confidence, provenance, MCP and the rest. **Not listed here on purpose:** the [register](adr/README.md) is the one place that states every record and its status, and a second list is a second thing to keep true.
* [Compare docs](../work/compare/README.md) - the v0.30 forks, verdict at the top of each, every one with a reopen-trigger.
* [Proposals](../work/proposals/README.md) - parked ideas with graduation triggers.

# Build

* [Handoffs](../archive/README.md) - **the handoff directory was retired 2026-08-18**; its contents are in `archive/handoff/`. A spec for open work now lives in that item's detail file under [`work/open/`](../work/open/README.md).
* [Regression evidence](../work/regression/README.md) - every measurement run: report + ANALYSIS + raw evidence. This is what other docs cite as grounding.
* [`tools/pruning-eval/`](../tools/pruning-eval/README.md) - M1's gate: the frozen [pre-registration](../tools/pruning-eval/PRE-REGISTRATION.md), the KL selector, the harness.
* [Archive](../archive/) - **old builds live in the root archive** (Arpit's ruling, 2026-08-10): [v0.1](../archive/v0.1/) · [v0.26 engine](../archive/v0.26/) · [v0.26 docs](../archive/v0.26-docs/) · [v0.26 implemented](../archive/v0.26-implemented/) · [v0.30 rev-1 planning](../archive/v0.30-rev1-planning/). Completed **doc artifacts** of the current build live in [`archive/`](../archive/README.md) instead.
