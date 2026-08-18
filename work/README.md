# `work/` — the shared memory between sessions

**How to use this directory.** Everything here exists so a session that has
never seen this repo can arrive cold, learn the true state in minutes, do
work, and leave the next session better off than it found it. Nothing here is
decoration; every file has a trigger that says when it must change.

`docs/` holds what the project **is** — the plan, the glossary, and the ADR
register. `work/` holds what is **happening to it**, which since 2026-08-18
includes the paper, the diagrams, the handoffs and the v0.30 record set: those
are all mid-rewrite, and a doc being rewritten is work.

## The map

| file | what it is | when it changes |
|---|---|---|
| [`WORKLOG.md`](WORKLOG.md) | append-only session log, newest first | **every** session, before it ends — chat-only ones too |
| [`INTERVIEW.md`](INTERVIEW.md) | the state-of-play doc a cold successor reads | **during** the session, not at the end |
| [`IMPLEMENTATION.md`](IMPLEMENTATION.md) | milestone log — what shipped, when, and how it turned out | a milestone or release lands |
| [`OPEN-WORK.md`](OPEN-WORK.md) | the single live queue — **items first, grouped by record**; rules at the foot | in the **same change** as the work that affects it |
| [`MACHINE.md`](MACHINE.md) | environment and tooling quirks of wherever this runs | a surface breaks in a way the code did not cause |
| [`DOC-REGISTRY.md`](DOC-REGISTRY.md) | per-doc freshness table, **live documents only** | any doc in it is touched; an archived doc's row is deleted, not annotated |
| [`open/`](open/README.md) | one detail file per open `W-nn` | opened with the item, **deleted with it** |
| [`regression/`](regression/README.md) | dated, measured evidence other docs cite | every measurement run |
| [`compare/`](compare/README.md) | live forks — verdict + reopen-trigger | a fork opens, closes, or its trigger fires |
| [`proposals/`](proposals/README.md) | parked ideas, not adopted | an idea is filed, graduates, or is rejected |
| [`paper/`](paper/the-fux-index-paper.md) | the architecture of record + figures | the architecture changes; a prediction gets measured |
| `architecture.svg` · `architecture-overview.svg` | the two diagrams | any tier/record-shape/query-path change (detailed) · any component add/remove (overview) |
| [`setup/`](setup/README.md) | the two things fux needs but does not contain — `fux-playground` (grades) and `fux-lab` (measures) | either is set up differently, or a new external dependency appears |

**Records live in [`../docs/adr/`](../docs/adr/README.md), and nowhere else.**
`work/adr/` existed for one day as a superseded-pending staging area and was
retired on 2026-08-18 when the whole v0.30 set was archived. A superseded record
now goes straight to [`../archive/adr/`](../archive/adr/README.md), which is not
evidence — it may be named, never cited.

**Fork or idea?** A live fork — two implementations that both exist, or a
decision with real options on the table — gets a `compare/` doc with a verdict
and a reopen-trigger. An idea nobody has decided on gets a `proposals/` doc.
If you cannot tell which, it is a proposal.

## Three cross-cutting rules

**0. There is one archive, and it is not in here.**
[`../archive/`](../archive/README.md), at the repo root, holds everything
retired — mirroring the live tree, so `adr/` retires into `archive/adr/` and
and the handoff directory retired wholesale into `archive/handoff/`. `work/`
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
3. Read [`OPEN-WORK.md`](OPEN-WORK.md), then **reconcile** it against
   [`IMPLEMENTATION.md`](IMPLEMENTATION.md), [`regression/`](regression/README.md)
   and the repo itself before believing any of its status markers.
4. Do the work, updating `OPEN-WORK.md` and `INTERVIEW.md` as you go.
5. Append to [`WORKLOG.md`](WORKLOG.md) — including the mandatory `Cost:` line —
   before you finish.
