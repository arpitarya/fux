# GOVERNANCE — how this repo's process is documented, and by what

**How to use this file.** Fux is governed by ~90 markdown/JSON files spread
across `CLAUDE.md`, `docs/`, `work/`, and `tests/`. This is the map: what each
governs, who reads it (agent, human, or both), what enforces it, and where the
weight could come out. It does not replace any file below — it is the index
none of them currently is.

## 1. The steering files (repo root)

| file | governs | audience | enforced by | update trigger |
|---|---|---|---|---|
| `CLAUDE.md` | the whole agent contract: laws, lifecycle, doc discipline, litmus test, blockers, answer-length | **agent** (primary) | convention only — no test reads it | any rule changes |
| `README.md` | what fux is, for someone outside the process | **human** | none | status/architecture changes |
| `DOGFOOD.md` | "fux used on itself" — one standing obligation | both | none | every version bump |
| `CHANGELOG.md` | release history | human | convention | every release |

## 2. `work/` — the live session-memory layer

| file/dir | governs | audience | enforced by | update trigger |
|---|---|---|---|---|
| `PRIORITY.md` | **the one ranked order of work** — read before anything else | agent | `Stop` hook (`stop-if-blocked.sh`) reads `BLOCKED.json`, not this file directly | Arpit reorders; row → DONE with a commit sha |
| `OPEN-WORK.md` | the single live queue, two lanes (`agent`/`arpit`) | both | none directly | same change as the work it tracks |
| `open/W-nn-*.md` (7 files) | one detail spec per open item | agent (executor) | none | opened with the item, deleted with it |
| `BLOCKED.json` | the machine-readable gate state | agent | `stop-if-blocked.sh` hook | a session blocks or unblocks |
| `INTERVIEW.md` (72 KB) | cold-start state of play for a successor session | agent | none | during the session, not at the end |
| `IMPLEMENTATION.md` (28 KB) | milestone log — what shipped, when | both | none | a milestone lands |
| `WORKLOG.md` (305 KB, append-only) | per-session trail, mandatory `Cost:` line | both (audit trail) | none — but P4/CLAUDE.md require it every session | every session |
| `NOW.md` (1 line) | one-line current-state pointer | both | none | changes with `PRIORITY.md`'s state |
| `MACHINE.md` | environment/surface quirks (4 surfaces) | agent | none | a surface breaks in a new way |
| `DOC-REGISTRY.md` (62 KB) | per-doc freshness table for **live** docs | both | `tests/test_doc_registry.py` | any registered doc is touched |
| `compare/*.md` (13 docs + README) | live forks — verdict + reopen-trigger | both | none | fork opens/closes/reopen-trigger fires |
| `proposals/*.md` (8 docs + README) | parked, undecided ideas | both | none | filed, graduates, or rejected |
| `regression/<date>-<run>/` (13 runs) | measured evidence other docs cite | both | `tests/test_regression_runs.py` | every measurement run |
| `setup/*.md` (2 docs + README) | how `fux-playground`/`fux-lab` are stood up | human (mostly) | `tests/test_setup_docs.py` | either sibling changes |
| `paper/the-fux-index-paper.md` | architecture of record + falsifiable predictions | both | none | architecture changes / a prediction is measured |
| `architecture*.svg` (2 diagrams) | visual architecture | human | none | tier/component changes |

## 3. `docs/` — what the project *is*

| file/dir | governs | audience | enforced by | update trigger |
|---|---|---|---|---|
| `docs/index.md` | bundle root, reading order across `docs/`+`work/` | both | none | either tree's structure changes |
| `docs/GLOSSARY.md` (24 KB) | recurring terms, defined once | human | none | a term is coined or redefined |
| `docs/adr/README.md` | the ADR register: convention, ownership, state | both | none directly (feeds the tests below) | a record's state changes |
| `docs/adr/000N_*.md` (**33 live records**) | one decision per completed feature/measurement | both (§1 human, §2 agent, per-record) | `test_adr_frontmatter.py`, `test_adr_freshness.py`, `test_adr_ownership.py`, `test_adr_owns_consistency.py` | the owning code changes |
| `docs/adr/TEMPLATE.md` | the shape new ADRs must follow | agent (author) | none | convention changes |
| `docs/adr/RULE-SINCE` | the freshness gate's audit baseline | agent (tooling) | read by `test_adr_freshness.py` | the gate's rule tightens |

## 4. `archive/` — retired, not evidence

One archive at the repo root, mirroring the live tree (`archive/adr/`,
`archive/open/`, `archive/handoff/`, …). Enforced by `tests/test_archive_law.py`
— a second archive anywhere else fails CI. Named in prose, never cited as
grounding.

## 5. What enforces any of this

| test | checks |
|---|---|
| `test_adr_freshness.py` | a changed ADR-owned file's **owning** record was touched in the same commit |
| `test_adr_frontmatter.py` | the 6-key frontmatter block, name/status consistency |
| `test_adr_ownership.py` / `test_adr_owns_consistency.py` | `**Owns:**` lines match the register, no path owned twice |
| `test_archive_law.py` | exactly one `archive/` directory exists |
| `test_doc_registry.py` | `DOC-REGISTRY.md` rows match live docs |
| `test_setup_docs.py` | `work/setup/*.md` carry the required frontmatter |
| `test_regression_runs.py` | a `regression/` run has the required artifacts |
| `.claude/hooks/stop-if-blocked.sh` | a session cannot end with an unsurfaced `BLOCKED.json` |
| `.claude/hooks/require-progress.sh`, `inject-inbox.sh`, `session-lock.sh` | session-level agent behavior, not doc content |
| `scripts/adr-guard.sh` (+ `commit-msg` hook) | commit-time ADR-ownership check |

**8 of ~18 test files in `tests/` exist to guard prose/process, not engine
correctness** — the "30% of tests guard prose" figure `PRIORITY.md` P7 already
cites is, if anything, a slight undercount today.

---

## My read: yes, this can be smaller

You already have the diagnosis filed — `PRIORITY.md` **P7 "Put the process on
a diet"** says almost exactly this: *"15 of the last 20 sessions shipped no
engine code; prose:code 3.2:1; 30% of tests guard prose. Both resets were
followed by more governance, not less."* This file is evidence for that row,
not a new idea competing with it. P7's own rule is that an agent proposes the
diff and Arpit decides — so treat what follows as that proposal, not an
executed change.

**Where the fat actually is:**

1. **`NOW.md` (1 line) duplicates `PRIORITY.md`'s state.** It exists only to
   be read faster than a full file. Fold its one line into the top of
   `INTERVIEW.md` or `PRIORITY.md` itself; delete the file. P7 already names
   this exact merge.
2. **`IMPLEMENTATION.md` (28 KB) and `OPEN-WORK.md` overlap by design** — an
   item's outcome is supposed to land in one, its queue-row deleted from the
   other, in the same change. P7 proposes merging `IMPLEMENTATION.md`'s
   content into `OPEN-WORK.md`'s deleted-row commit messages instead of a
   separate file. That removes one 28 KB file and one synchronization
   obligation (rule "reconcile OPEN-WORK against IMPLEMENTATION" in
   `work/README.md` disappears with it).
3. **`WORKLOG.md` is 305 KB and append-only, growing every session forever.**
   It is the audit trail, so it should not be deleted — but it is also the
   single largest file in the repo and nothing reads old entries back. A
   yearly (or v-major) archive-and-truncate — moving everything before a cut
   date into `archive/worklog/YYYY.md` — would keep the audit trail intact
   under the one-archive law while stopping the live file from growing
   without bound. Not currently proposed anywhere; worth adding to P7's diff.
4. **The mandatory `Cost:` line is dead weight by the numbers already
   gathered**: P7 notes 49/49 logged instances are `unmeasured`. A field that
   has never once carried real data is a formatting tax with no payoff — drop
   the requirement, or replace it with something that's actually filled in.
5. **`DOC-REGISTRY.md` (62 KB) tracking freshness for docs that are already
   individually tested** (ADRs have four dedicated tests; `setup/` has one) is
   partial duplication — the registry's real unique value is covering the
   *untested* prose (`WORKLOG.md`, `MACHINE.md`, `GLOSSARY.md`, the paper).
   Consider scoping it to only the files nothing else checks, which shrinks
   both the file and the surface it has to stay in sync with.
6. **13 `regression/` run directories and 13 `compare/` docs are not
   candidates for cutting** — they're exactly the "ground truth over prose"
   evidence layer CLAUDE.md's own rule 3 requires, and each is small,
   self-contained, and dated. The volume there is a symptom of doing a lot of
   measured work, not of process bloat.

**On audience split:** almost nothing here is agent-only or human-only —
`CLAUDE.md`, `PRIORITY.md`, `BLOCKED.json`, and the `open/W-nn` specs skew
agent (an agent reads them to decide what to do next); `README.md`,
`GLOSSARY.md`, and the two architecture SVGs skew human (nobody automates
against a diagram). Everything else — ADRs, `compare/`, `proposals/`,
`regression/`, `WORKLOG.md`, `INTERVIEW.md` — is written for both by design
(the "§1 for humans / §2 for agents" split inside each ADR is the same idea
applied per-file). That mixed audience is not itself the bloat; the bloat is
in the trackers that duplicate each other's state (`NOW`↔`PRIORITY`,
`IMPLEMENTATION`↔`OPEN-WORK`) and the ones that grow forever with no archive
cut (`WORKLOG.md`).

**Net effect if items 1–4 land:** two files deleted (`NOW.md`,
`IMPLEMENTATION.md`), one synchronization rule removed from `work/README.md`,
one dead-weight field removed from every future worklog entry, and a template
for keeping `WORKLOG.md` from becoming the second-largest cost in the repo. It
does not touch the ADR register, `compare/`, `proposals/`, or `regression/` —
those are the parts of the process that are actually earning their keep.
