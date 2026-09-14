---
type: Index
description: "Map of work/ — the shared memory between sessions."
---

# `work/` — the shared memory between sessions

**How to use this directory.** Everything here exists so a session that has
never seen this repo can arrive cold, learn the true state in minutes, do
work, and leave the next session better off than it found it. Nothing here is
decoration; every file has a trigger that says when it must change.

`docs/` holds what the project **is** — the plan, the glossary, and the SR
register. `work/` holds what is **happening to it**, which since 2026-08-18
includes the paper, the diagrams, the handoffs and the v0.30 record set: those
are all mid-rewrite, and a doc being rewritten is work.

## The map

| file | what it is | when it changes |
|---|---|---|
| [`OPEN-WORK.md`](OPEN-WORK.md) | **read first** — the single live queue, **items first, grouped by record**; rules at the foot | in the **same change** as the work that affects it |
| [`BACKLOG.md`](BACKLOG.md) | the **named-but-unclaimed** — everything a record, proposal or compare doc says is outstanding and nobody is doing, in five classes; rules in [SR-WORK-BACKLOG](../records/0055_WORK-backlog.md). ⚠ **its length is not a signal** | a record names something outstanding, or an item is promoted into the queue — **same change**, always |
| [`WORKLOG.md`](WORKLOG.md) | append-only session log, newest first | **every** session, before it ends — chat-only ones too |
| [`INTERVIEW.md`](INTERVIEW.md) | the state-of-play doc a cold successor reads | **during** the session, not at the end |
| [`IMPLEMENTATION.md`](IMPLEMENTATION.md) | milestone log — what shipped, when, and how it turned out | a milestone or release lands |
| [`MACHINE.md`](MACHINE.md) | environment and tooling quirks of wherever this runs | a surface breaks in a way the code did not cause |
| [`DOC-REGISTRY.md`](DOC-REGISTRY.md) | per-doc freshness table, **live documents only** | any doc in it is touched; an archived doc's row is deleted, not annotated |
| [`open/`](open/README.md) | one detail file per open `W-nn` | opened with the item, **deleted with it** |
| [`regression/`](regression/README.md) | dated, measured evidence other docs cite | every measurement run |
| [`golden/`](golden/README.md) | the sealed benchmark — seed docs, ladder manifests, prompts. 🔴 `golden-answer/` is **never read by Claude** | a phase of W-136 runs; the process changes |
| [`compare/`](compare/README.md) | live forks — verdict + reopen-trigger | a fork opens, closes, or its trigger fires |
| [`proposals/`](proposals/README.md) | parked ideas, not adopted | an idea is filed, graduates, or is rejected |
| `architecture-*.svg` | **the six diagrams**, redrawn from the code 2026-09-12 and again the same day for the Node read plane: `high-level` (what fux is) · `detailed` (every plane, committed vs not, and **the two readers**) · `decoders` · `ask` · `answer` · `two-readers` (Python versus Node, component for component). `docs/architecture-*.png` are rendered from these and are never edited directly | the plane, verb, **reader** or record shape each one draws changes. **`high-level` should move rarely** — if it moves often it is drawn at the wrong altitude |
| [`setup/`](setup/README.md) | the three sibling environments fux needs but does not contain — `fux-playground`, `fux-lab`, `fux-benchmark`; each one's job is [SR-WORK-ENVIRONMENTS](../records/0052_WORK-environments.md)'s | any of them is set up differently, or a new external dependency appears |

**Records live in [`../records/`](../records/README.md), and nowhere else.**
`work/adr/` existed for one day as a superseded-pending staging area and was
retired on 2026-08-18. There is no archive tier either: on 2026-09-06 Arpit
deleted the archived records outright, so a superseded record is **rewritten or
deleted in the change that supersedes it** and leaves no second file behind.

**Fork or idea?** A live fork — two implementations that both exist, or a
decision with real options on the table — gets a `compare/` doc with a verdict
and a reopen-trigger. An idea nobody has decided on gets a `proposals/` doc.
If you cannot tell which, it is a proposal.

**Queue or backlog?** If somebody is doing it, or is about to, it is a `W-nn` in
[`OPEN-WORK.md`](OPEN-WORK.md) with a ball and a detail file. If it has only been
*named* — a record says it is unbuilt, ungated, unmeasured, unruled, or a cost
accepted — it is a `B-nnn` row in [`BACKLOG.md`](BACKLOG.md) and nothing else.
**Never both** ([SR-WORK-BACKLOG](../records/0055_WORK-backlog.md) rule 7).

## Three cross-cutting rules

**0. There is one archive, and it is not in here.**
[`../archive/`](../archive/README.md), at the repo root, holds everything
retired — mirroring the live tree; the handoff directory, for instance, retired
wholesale into `archive/handoff/`. **Decision records are the exception: they
are not archived, they are deleted** (Arpit, 2026-09-06). `work/`
holds live work only. A second
archive is a defect, and `tests/test_archive_law.py` fails on one.

**1. Archive is not evidence.** A doc under any `archive/` may be *named*
("superseded by X") but must **never be cited as backing a live claim**.
Nothing guarantees an archived file was not overwritten after the fact. When
you find a live citation pointing into an archive, repoint it at the **live
successor** — do not simply delete the link, or the claim silently loses its
grounding.

**2. Concurrent sessions are real.** Cowork, Claude Code and a scheduled task
can all touch these files. Before committing a change to any `work/*.md`,
**re-read the file and re-apply your edit** — another session may have landed
an entry in between. Assume your copy is stale; it costs seconds to check.

**3. Ground truth over prose.** Before writing any status claim — release
state, test counts, "nothing pending", "X is done" — check it against the
actual source of truth: `git log`, `git status`, `git tag`, the code, a
command that reproduces. A doc repeating another doc is not a second source.

## Starting a session here

1. Read [`../CLAUDE.md`](../CLAUDE.md) §Documentation discipline.
2. Read [`INTERVIEW.md`](INTERVIEW.md) — state of play, in-flight work, next step.
3. Read [`OPEN-WORK.md`](OPEN-WORK.md) — and [`BACKLOG.md`](BACKLOG.md) before
   filing anything new, so a thing already named does not get named twice — then
   **reconcile** the queue against
   [`IMPLEMENTATION.md`](IMPLEMENTATION.md), [`regression/`](regression/README.md)
   and the repo itself before believing any of its status markers.
4. Do the work, updating `OPEN-WORK.md` and `INTERVIEW.md` as you go.
5. Append to [`WORKLOG.md`](WORKLOG.md) before you finish.
