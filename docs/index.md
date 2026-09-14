---
okf_version: "0.1"
---

# Fux docs — knowledge bundle root (v0.30 rebuild)

The bundle is **`docs/` + `records/` + `work/`**, and this index spans all three. It was one tree
until 2026-08-18; the split does not change the bundle, only its shape:

- **`docs/`** — what the project **is**: the plan, the glossary, the SR
  register.
- **[`work/`](../work/README.md)** — what is **happening to it**: the session
  memory, the queue, the evidence, and every doc currently mid-rewrite.

Large docs carry two sections — *For humans* then *For AI agents* — update both
or neither.

## What is in the bundle, and what conforms

**Every knowledge doc in the bundle carries frontmatter with a non-empty
`type`** — ALL-CAPS trackers included. **The ALL-CAPS exemption was retired
2026-09-12**: it was a repo convention the OKF spec does not have, so a
conformance claim and the tree disagreed. `OPEN-WORK.md`, `INTERVIEW.md`,
`IMPLEMENTATION.md`, `WORKLOG.md`, `MACHINE.md`, `NOW.md`, `GLOSSARY.md`,
`DOC-REGISTRY.md`, `governance.md`, the SR register and every directory
`README.md` now declare a `type`.

**This file is the bundle root** (`okf_version: "0.1"`) and is the one reserved
file that declares only `okf_version`.

**Three things under `docs/`+`work/` are outside the bundle.** They are files
the tree happens to contain, not knowledge documents it publishes:

| outside the bundle | why |
|---|---|
| `work/regression/*/evidence/**` | raw run material — model output, generated corpora, captured stdout. Evidence is cited *by* a document; it is not one. |
| `work/golden/seed/**`, `work/golden/golden-answer/**`, `work/golden/questions/questions.jsonl` | the sealed benchmark's test data, authored outside this lane ([`work/golden/README.md`](../work/golden/README.md)). Editing it to satisfy a docs rule would corrupt the instrument. `questions/README.md` is a document and stays in the bundle; the `.jsonl` beside it is emitted from the key. |
| repo-root `CLAUDE.md`, `README.md` | tool entry points, outside `docs/`+`work/` to begin with. |

**Filed regression runs before 2026-08-25 are exempt by baseline, not by
exception.** `report.md` and `ANALYSIS.md` in those directories are frozen —
`tests/test_regression_runs.py` already baselines its classification rule on
the same date, for the same reason: *turning a rule on by editing the evidence
it governs is the failure the rule is about*. Runs filed on or after that date
conform.

🔴 **NOT ENFORCED — and this paragraph said it was.** It read *"enforced by
`tests/test_okf_bundle.py`, so the claim and the tree cannot drift apart
again"*, and **that file has never existed** (found 2026-09-12 by
`tests/test_doc_links.py`, which counts links to files that are not there).

- **The drift it claimed to prevent is measured and real:**
  [the positioning proposal](../work/proposals/positioning-documents-not-code.md)
  §6 found **94 of 314 files** failing a conformance bar this repo asserts in
  prose and checks nowhere.
- ⚠ **The test is not written here on purpose.** It would fail on all 94 today,
  and the tempting next move — loosening it until it passes — is the
  moving-threshold failure this repo refuses everywhere else. **A ratchet
  (conform where we conform, name the 94, never get worse) is the shape that
  would work**, and it is a decision with a cost, not a gap to fill quietly.
- **Until then this bar is a convention, not a guarantee.** Read it as *what a
  conforming file looks like*, and do not cite it as a property of the tree.

## The tree — where everything lives

**The full layout, stated once.** `CLAUDE.md` keeps a twelve-line top-level
tree as orientation and points here for the rest (W-173, 2026-09-14).

```
work/               THE SHARED MEMORY between sessions — start at work/README.md
  WORKLOG.md        append-only session log (an entry every session)
  INTERVIEW.md      state of play, kept current DURING the session
  IMPLEMENTATION.md milestone log — what shipped, when, outcome (the evidence store)
  OPEN-WORK.md      THE single live queue — two lanes; finished items are DELETED
  NOW.md            the one-line running pointer
  LESSONS.md        dated build lessons — a log, because a record carries no history
  MACHINE.md        environment/tooling quirks per surface (local · bridge · cloud · CI)
  DOC-REGISTRY.md   doc freshness tracker (triggers + last-verified)
  BLOCKED.json      the blocker file; its presence stops the session
  paper/            the architecture of record + figures + predictions
  architecture-{high-level,detailed,decoders,ask,answer,two-readers}.svg   the six
                    diagrams, redrawn from the code 2026-09-12. (The proposal target
                    sheet was archived 2026-09-14 with W-112's closure.)
  open/             one detail file per open W-nn; ARCHIVED on close, never deleted
  setup/            the three siblings — playground · lab · benchmark — outside this repo
                    (SR-WORK-ENVIRONMENTS)
  regression/       dated, measured evidence other docs cite as grounding; VERDICT.md rules
  benchmark/reports/ CAP-7, one HTML report per benchmark run, plus TEMPLATE.html
  golden/           the sealed benchmark — seed docs, ladder manifests, prompts. Its
                    answer key is NEVER read by any Claude session; see its README
  compare/          live forks — verdict + explicit reopen-trigger
  proposals/        parked ideas, not yet decided
records/            THE STANDING RECORDS — the register, TEMPLATE.md, SR-LAWS and
                    SR-LAW-0…SR-LAW-10; new records land here. At the repo root
                    since 2026-09-13, and in the OKF bundle from wherever it sits
docs/               WHAT THE PROJECT IS
  GLOSSARY.md       every recurring term, defined once
  index.md          the OKF bundle root — this file
src/fux/            the engine — every component claimed in records/README.md
node/               the Node read plane — authored .mjs; ONE bundled file ships (L10)
tests/              the fast unit suite, incl. test_sr_ownership.py (the ownership twin)
tests_e2e/          the package as a user — real CLI via subprocess, fixture corpora
tools/
  pruning-eval/     the gate — frozen pre-registrations, KL selector, eval harness
  differential/     the differential-law harness and the R3 bench
archive/            THE ONE ARCHIVE — everything retired, mirroring the live tree
  README.md         the map: every archived doc and its live successor
  open/             closed work items, byte for byte, with a successor row
  handoff/          the retired handoff directory (executed pairs + unresolved specs)
  v0.26/            build: the previous engine — runnable, REFERENCE ONLY
  v0.26-docs/       build: the frozen v0.19–0.26 doc set ("archived SR-NNNN")
  v0.26-implemented/ · v0.30-rev1-planning/   frozen build artifacts
  v0.1/             build: the first one
```

⚠ **`archive/adr/` is gone.** There is **no archive tier for records** — the
rule and its consequence are stated in
[the register](../records/README.md), and a record citation resolves into
`records/` or not at all.

**`src/fux/` was gated behind P1, and now exists.** The package scaffold was
M0b and landed only once the pruning gate had been decided — scaffolding a
package for an architecture a measurement might falsify is the *build the fun
part first* failure the plan exists to avoid. It shipped in `v0.30.0`; **the
gating rule stands for every milestone after it**
([SR-RS](../records/0133_predictions.md)).

# Core (read in this order)

* [The SR register](../records/README.md) - the decisions of record. `PLAN.md` was archived 2026-08-18; milestone scope now lives in the item that will build it, under [`work/open/`](../work/open/README.md).
* [Open work](../work/OPEN-WORK.md) - **the single live queue**, two concurrent lanes; finished items are deleted, not ticked.
* [Implementation](../work/IMPLEMENTATION.md) - the milestone log: what shipped, when, and the outcome. What OPEN-WORK reconciles against.
* [The paper](../work/paper/the-fux-index-paper.md) - the architecture of record, with figures and falsifiable predictions.
* **The six diagrams**, redrawn from the code 2026-09-12 — [high-level](../work/architecture-high-level.svg) (what fux is, in three boxes) · [detailed](../work/architecture-detailed.svg) (every plane, what is committed and what is not) · [decoders](../work/architecture-decoders.svg) (how bytes fux cannot read become text it can) · [ask](../work/architecture-ask.svg) (the query path, and the law that lets there be two of them) · [answer](../work/architecture-answer.svg) (the refer plane and the five freshness verdicts) · [two readers](../work/architecture-two-readers.svg) (search in Python versus Node — every twin module, every Python-only component, and the three deliberate asymmetries).
* [Model handoff interview](../work/INTERVIEW.md) - the state of play; read before substantive changes.
* [Worklog](../work/WORKLOG.md) - per-exchange session trail, newest first.
* [Machine notes](../work/MACHINE.md) - what breaks on which surface, and why.
* [Doc registry](../work/DOC-REGISTRY.md) - maintained docs, update triggers, last-verified dates.
* [Glossary](GLOSSARY.md) - recurring terms, defined once.

# Decisions

**`records/` is the only home a record has** (Arpit, 2026-09-06). The archive
tier is gone — the retired records were deleted, not filed. A citation resolves
into this directory or it does not resolve.

* [The SR register](../records/README.md) - the convention, the ownership table, and the state of every record. **Records are cited by NAME, never by number.** It lists all 62 live records; the entry points below are the reading order, not the set.
* [SR-LAWS](../records/0001_LAWS.md) - the meta-rules and the index: the non-negotiable constraints have exactly one home, and no record restates them.
* The ten law records - one law, one record: [L0 authority](../records/0002_LAW-0-authority.md) · [L1 `$0`/FOSS-only](../records/0003_LAW-1-zero-cost.md) · [L2 content never durable](../records/0004_LAW-2-content-never-durable.md) · [L3 deterministic](../records/0005_LAW-3-deterministic.md) · [L4 offline by default](../records/0006_LAW-4-offline-by-default.md) · [L5 hashed meta](../records/0007_LAW-5-hashed-meta.md) · [L6 say index](../records/0008_LAW-6-say-index.md) · [L7 Python 3.11](../records/0009_LAW-7-python-311.md) · [L8 use record](../records/0010_LAW-8-use-record.md) · [L10 build output, never source](../records/0011_LAW-10-bundled-output.md).
* [SR-CLI](../records/0101_cli-surface.md) - the command-line surface: flat verbs in seven groups, one error boundary, three output modes, every command captured verbatim.
* [SR-DOTFUX](../records/0102_fux-directory.md) - the `.fux/` directory: every child declared committed or derived, the ignore rule asserted against git itself.
* [SR-ASK](../records/0103_ask.md) - the `ask` verb: one scorer, one sort; the path that answers can never change the answer.
* [SR-FIND](../records/0104_find.md) - the `find` verb: one line per hit, for pipes; a projection of `ask`, not a second strategy.
* [SR-ANSWER](../records/0105_answer.md) - the `answer` verb: a fetched, re-scored passage with a fresh sha, its footing stated every time, and no model on the path.
* [SR-INGEST](../records/0106_ingest.md) - how ingest works: carry unchanged extraction forward, re-resolve every edge, write only shards whose bytes changed.
* [SR-URL-INGEST](../records/0107_url-ingest.md) - URL ingestion behaviour: fetching only inside a named fenced path, a failed fetch is a skip not a deletion.
* [SR-INDEX-LIFECYCLE](../records/0108_index-lifecycle.md) - index generation and update, and the derived plane that refuses to diverge.
* [SR-RECORD](../records/0109_index-record.md) - one line of the committed index, property by property, including the conditional ones.
* [SR-T1-ACCELERATOR](../records/0110_accelerator.md) - the derived index: disposable, term-major, forbidden from changing an answer.
* [SR-RANKING](../records/0111_ranking.md) - BM25F, weight-then-saturate once, one scorer and one rounded sort.
* [SR-POSTINGS](../records/0112_postings.md) - the postings in two shapes, and why git gets the doc-major one.
* [SR-CONFIG](../records/0113_config.md) - `fux.toml` and every property in it: three tables read, two refused by name, one passed through unread.
* The remaining records - the refer plane, fetchers, decode, tuning, quality, confidence, provenance, MCP and the rest. **Not listed here on purpose:** the [register](../records/README.md) is the one place that states every record and its status, and a second list is a second thing to keep true.
* [Compare docs](../work/compare/README.md) - the v0.30 forks, verdict at the top of each, every one with a reopen-trigger.
* [Proposals](../work/proposals/README.md) - parked ideas with graduation triggers.

# Build

* [Handoffs](../archive/README.md) - **the handoff directory was retired 2026-08-18**; its contents are in `archive/handoff/`. A spec for open work now lives in that item's detail file under [`work/open/`](../work/open/README.md).
* [Regression evidence](../work/regression/README.md) - every measurement run: report + ANALYSIS + raw evidence. This is what other docs cite as grounding.
* [`tools/pruning-eval/`](../tools/pruning-eval/README.md) - M1's gate: the frozen [pre-registration](../tools/pruning-eval/PRE-REGISTRATION.md), the KL selector, the harness.
* [Archive](../archive/) - **old builds live in the root archive** (Arpit's ruling, 2026-08-10): [v0.1](../archive/v0.1/) · [v0.26 engine](../archive/v0.26/) · [v0.26 docs](../archive/v0.26-docs/) · [v0.26 implemented](../archive/v0.26-implemented/) · [v0.30 rev-1 planning](../archive/v0.30-rev1-planning/). Completed **doc artifacts** of the current build live in [`archive/`](../archive/README.md) instead.
