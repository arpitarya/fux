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
| `OPEN-WORK.md` | the single live queue, two lanes (`agent`/`arpit`) | both | none directly | same change as the work it tracks |
| `open/W-nn-*.md` (7 files) | one detail spec per open item | agent (executor) | none | opened with the item, deleted with it |
| `BLOCKED.json` | the machine-readable gate state | agent | `stop-if-blocked.sh` hook | a session blocks or unblocks |
| `INTERVIEW.md` (72 KB) | cold-start state of play for a successor session | agent | none | during the session, not at the end |
| `IMPLEMENTATION.md` (28 KB) | milestone log — what shipped, when | both | none | a milestone lands |
| `WORKLOG.md` (305 KB, append-only) | per-session trail | both (audit trail) | none — but CLAUDE.md requires it every session | every session |
| `NOW.md` (1 line) | one-line current-state pointer | both | none | every session transition |
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

**ADR maintenance is remitted to the ADR hooks, not to prose.** Law zero —
"ADRs are always up to date" — is enforced by `scripts/adr-guard.sh` running
as a `commit-msg` hook (`ln -sf ../../scripts/adr-guard.sh
.git/hooks/commit-msg` — **not** `pre-commit`, because the `no ADR affected`
escape hatch needs the commit message, which doesn't exist yet at
`pre-commit` time) plus `tests/test_adr_freshness.py` running the identical
check in CI. A commit that touches an ADR-owned path without touching that
path's owning record is rejected. Nobody has to remember to reconcile a
record by discipline — the gate remembers for them.

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

**8 of ~18 test files in `tests/` guard prose/process, not engine
correctness by file count** — but PRIORITY.md P7's audit (2026-08-21) read
all of them and found the "~30% of tests guard prose" figure does not
reproduce: the dedicated set is 35 of 836 tests (≈4%) once
`test_frontmatter.py` (the stdlib parser's own tests, not a governance
check) is correctly excluded from the count. Corrected here on contact
rather than repeated.

---

## P7 landed, 2026-08-21 — this section is now a partial post-mortem, not a live proposal

**This section was written as input to `PRIORITY.md` P7 while P7 was still
open.** P7 has since been decided and applied — see
[`archive/proposals/process-diet.md`](../archive/proposals/process-diet.md) for the actual
four candidates put to Arpit and his verdict on each (only the `Cost:` line
was accepted and dropped; `NOW.md` stays separate from `INTERVIEW.md`, on
the grounds that they serve different read patterns, not just different
sizes). `PRIORITY.md` itself is now archived
([`archive/README.md`](../archive/README.md)); `OPEN-WORK.md` is the live
queue, as it always was.

**Two ideas below were not among P7's four candidates and were not decided
in that round** — left here, explicitly parked rather than acted on or
lost:

1. ~~`NOW.md` duplicates `PRIORITY.md`'s state; delete it.~~ **Decided
   against, 2026-08-21** (P7): the two serve different read patterns — a
   hook reads `NOW.md` unconditionally on every prompt, `INTERVIEW.md` is
   read deliberately once per session.
2. `IMPLEMENTATION.md` and `OPEN-WORK.md` are not a merge candidate —
   confirmed, this reasoning matches Arpit's actual ruling.
3. **`WORKLOG.md` archive-and-truncate — not litigated in P7, still parked.**
   305 KB and growing forever; a yearly (or v-major) cut into
   `archive/worklog/YYYY.md` would keep the audit trail under the one-archive
   law while capping the live file's growth. Worth its own proposal if this
   becomes a real cost, not decided here.
4. ~~The mandatory `Cost:` line is dead weight.~~ **Accepted and applied,
   2026-08-21** (P7) — dropped from CLAUDE.md and `WORKLOG.md`'s template.
5. **`DOC-REGISTRY.md` scoped to only untested prose — not litigated in P7,
   still parked.** The registry's real unique value is covering docs nothing
   else checks (`WORKLOG.md`, `MACHINE.md`, `GLOSSARY.md`, the paper); ADRs
   and `setup/` already have dedicated tests. Worth its own proposal, same as
   item 3.
6. `regression/` and `compare/` are not candidates for cutting — confirmed,
   they are the "ground truth over prose" evidence layer CLAUDE.md's own rule
   requires.
7. ADR maintenance is remitted to the ADR hooks, not a diet candidate —
   confirmed, unchanged.

**On audience split:** almost nothing here is agent-only or human-only —
`CLAUDE.md`, `OPEN-WORK.md`, `BLOCKED.json`, and the `open/W-nn` specs skew
agent (an agent reads them to decide what to do next); `README.md`,
`GLOSSARY.md`, and the two architecture SVGs skew human (nobody automates
against a diagram). Everything else — ADRs, `compare/`, `proposals/`,
`regression/`, `WORKLOG.md`, `INTERVIEW.md` — is written for both by design
(the "§1 for humans / §2 for agents" split inside each ADR is the same idea
applied per-file).
