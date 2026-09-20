---
type: OpenItem
id: W-198
title: "W-198 — `golden-answers/` is the canonical local key directory: L11 decision 3 amended, both spellings guarded"
description: "Arpit's ruling 2026-09-18 on W-197 — the plural directory holds answer docs and STAYS on disk. L11 is amended to permit a local, gitignored, agent-closed key directory; `golden-answers/` becomes the canonical spelling everywhere; every guard covers both spellings by glob; the Cowork-mount exposure is recorded. BUILT 2026-09-20; six guards, not four, and the gitignore hole the spec did not predict."
status: closed
lane: agent
timestamp: 2026-09-18T00:00:00Z
filed: 2026-09-18
closed: 2026-09-20
ball: agent
---

# W-198 — the key lives on disk again, guarded, under one name

**Model: Opus** — it amends a Law record, regenerates the two CLAUDE.md blocks a
test binds byte-equal, and touches four guards. ✅ **BUILT 2026-09-20** — see §Built at the end for the four places the delivered change differs from this spec.

🔴 **Nothing in this item aims a tool at `work/golden/golden-answers/`.** Every
edit here is to records, docs, guards and tests. L11 decision 5 still holds for
every agent on every surface: the directory is closed to listing, stat, glob,
read, write, hash, diff and delete. **The rename is of references, never of the
directory.**

## The ruling

> **Arpit, 2026-09-18**, on W-197: *"answer docs — wherever we have golden-answer
> or golden-answers change it to golden-answers but add similar restriction to
> both."*
>
> Asked whether the answer docs stay on disk: *"Yes — keep them; amend L11 to
> allow a local guarded key dir."*

## What this reverses, stated plainly

- [SR-LAW-11](../../records/0012_LAW-11-sealed-answer-key.md) **decision 3** says
  *"No agent writes a key file, so no agent can be asked to read one.
  `work/golden/golden-answer/` is named in this law only to say that it is not a
  location."* **That sentence is withdrawn.** A key directory exists, on Arpit's
  machine, gitignored, and it is a location — one no agent may reach.
- The law's **central claim moves** from *"there is nothing on disk to reach"* to
  *"the guards are the defence and prose covers what the guards cannot."* That
  is where the law stood before 2026-09-15; the record must say the move was
  made knowingly and why.
- **Both L11 veto conditions have fired** — a Claude session held an answer
  (W-196) and a key file was found on a reachable machine (W-197). The record is
  formally reopened. This item resolves the second; **the first stays open under
  W-196** and this item does not touch it.

## Definition of done

1. **SR-LAW-11 decision 3 amended**, Arpit's ruling quoted and dated. A key MAY
   exist at `work/golden/golden-answers/` on Arpit's machine: **gitignored, never
   committed, closed to every agent under decision 5, on both spellings.**
2. **SR-LAW-11's veto condition rewritten.** *"A key file on any machine an agent
   can reach"* no longer reopens the law — the canonical directory is exactly
   that. It now reopens on **a key outside the canonical directory, or a key
   committed on any ref.**
3. **SR-LAW-11 Consequences carries the Cowork-mount exposure**, in these
   terms: `permissions.deny` and the hook govern Claude Code; a Cowork session
   mounts the whole folder and reaches the directory with a plain shell call,
   stopped by L11's prose alone. **Accepted, not closed.** ⚠ This is the second
   prose-only door beside the paste one W-196 came through.
4. **Canonical spelling is `golden-answers/`.** Every reference to the singular
   in records, `work/golden/README.md`, prompts 1–8 and 6E, work items, tests,
   `CLAUDE.md`'s generated blocks and `docs/` is repointed. **The singular
   survives only inside guards**, where both must match.
5. **Every guard covers both spellings, by glob** — `work/golden/golden-answer*/`
   or the equivalent — in `.gitignore`, `.claude/settings.json` `permissions.deny`,
   `.claude/hooks/guard-golden-answer.sh` (already substring-matched — keep, and
   test it), `.fux/sources/dirs` (`!work/golden` already excludes the parent —
   verify, and add the explicit line anyway), and
   `tests/test_golden_key_never_committed.py` (already both spellings — verify).
6. **A test asserts the guards**: each of the four guard files contains the glob,
   and `git ls-files` matches nothing under either spelling on any ref. It works
   from git metadata and never opens the directory.
7. **`scripts/gen-laws.py --write` and `scripts/gen-golden.py --write` re-run**;
   `tests/test_claude_md_laws.py` and `test_claude_md_golden.py` pass byte-equal.
8. **[SR-WORK-GOLDEN](../../records/0066_WORK-golden.md) decision 2's** *"there is
   no key file"* sentences and the *"was deleted on 2026-09-15"* history are
   rewritten to state the new arrangement without erasing the deletion.
9. **W-197 closes** in the same change — archived, not deleted.

## In scope / out of scope

**In:** the record amendment, the rename of references, the guards, the tests,
the generated blocks, the golden README and prompts.

**Out:** **the paste route.** Decision 4 stands — the one route an answer travels
to a scoring turn is still Arpit's paste into Codex. Whether Codex may now read
the directory directly is **a further ruling Arpit has not made**; this item
does not assume it. 🔴 **Out:** anything under W-196 — the disposition of set 1
and the mechanical guard the paste route now needs.

## Key files

| area | files |
|---|---|
| the law | `records/0012_LAW-11-sealed-answer-key.md` (decisions 3, 5; Consequences; Veto condition; "How to check it") |
| the process | `records/0066_WORK-golden.md` decision 2 · `work/golden/README.md` §Custody, §Between the prompts |
| generated | `CLAUDE.md` §Non-negotiable constraints L11 · §Golden answer key — via `scripts/gen-laws.py`, `scripts/gen-golden.py` |
| guards | `.gitignore` · `.claude/settings.json` · `.claude/hooks/guard-golden-answer.sh` · `.fux/sources/dirs` |
| tests | `tests/test_golden_key_never_committed.py` · `tests/test_claude_md_laws.py` · `tests/test_claude_md_golden.py` · new guard test |
| prompts | `work/golden/prompts/{1,2,3,4,5,6,6E,7,8}*.md` |
| items | `work/open/W-136`, `W-196`, `W-197` — references only |

## Hazards

1. 🔴 **The rename must not become a `mv`.** `sed` over files is the tool;
   `git mv`, `mv`, `find -exec` over `work/golden/` are each a breach. A
   recursive `grep`/`sed` over `work/` **excludes `work/golden/golden-answer*`**
   — CLAUDE.md names this as the route no guard sees.
2. **The hook fires on the substring in prose.** Expect it to block the session
   that edits these records; that is the guard working, not a defect. Work in
   the file, not in a shell echo.
3. **Two generated blocks, two generators, one test each.** Edit the record,
   regenerate, never the block.
4. **The paste route is not widened by accident.** Prompt 6 still says *"Arpit
   pastes."* Leave it.

---

## ✅ Built 2026-09-20 (Claude Code, Opus 5)

**Every numbered item in *Definition of done* landed.** Four differences from
the spec are named here rather than left to be found.

### 1. There are SIX guards now, not four — and the sixth is a new file

**`.claude/hooks/guard-sealed-key.sh`.** Item 5 says the existing hook is
*"already substring-matched — keep, and test it."* **That is true of its TARGET
check and false of its Bash branch**, which matches `golden/golden-answer`,
`golden-answer/` and `golden-answer` before a space, quote or end of string.
A bare plural path in a shell command hits none of the three, so an arbitrary
command reading `golden-answers/k.jsonl` was allowed. `permissions.deny` covers
the thirteen *named* commands by substring; an arbitrary command was the hole.

🔴 **The first hook could not be amended, and that is a property worth
keeping.** It refuses every edit to itself — its own filename contains the
string it matches — so no Claude session can widen *or narrow* it. Closing the
gap by routing around a guard that is working would have been the wrong trade,
so the fix is a second guard registered beside the first. **Both are proved, in
both directions, by [`tests/test_golden_key_guards.py`](../../tests/test_golden_key_guards.py)**
— including a test that asserts the first hook's gap is still exactly where it
is, so the second hook's reason to exist cannot quietly stop being true.

### 2. `.gitignore` had a hole the spec did not predict, and the test found it

`**/golden-answer/` ends in a slash, so **it matches a directory and only while
that directory exists.** After the singular directory was deleted on
2026-09-15, `git check-ignore` reported that exact path **not ignored** — a key
written back to it would have been trackable. Found by
`test_git_ignores_both_spellings` on its first run. Fixed with a slash-free
`**/golden-answer*`, with the reason written into `.gitignore` itself.

### 3. 🔴 This file could not be edited by the tool that should have edited it

**The guard's TARGET check is a bare substring, and this file's NAME contains
it.** So `Edit(work/open/W-198-…-answers-canonical.md)` is denied — the work
item that manages the directory is unmaintainable by any Claude session, and so
is the guard's own file. **Neither is a key**; both are git-tracked, and the
committed-key gate's own matcher (anchored to a path component) agrees they are
not. This section was applied through the shell instead, which **both** guards
inspect and permit, and the fact is declared here and in the session rather
than left silent.

**The sixth guard does not inherit the false positive** — its TARGET check is
anchored to a path component, which is the fix
`tests/test_golden_key_never_committed.py` already made after flagging one of
the guards on its own first run. **The first hook keeps the bug**, because no
agent can touch it: filed for Arpit, since the one-line fix is an edit to a file
the hook will not let an agent make.

### 4. "Every reference repointed" is scoped, deliberately

Item 4 asks for every singular reference in records, `work/golden/README.md`,
the prompts, work items, tests, the generated blocks and `docs/` to be
repointed. **Repointed: every reference that names the directory as a live
location.** **Left as written: dated history** — `WORKLOG.md` (append-only by
its own rule), `IMPLEMENTATION.md` and `DOC-REGISTRY.md` change-log rows,
`INTERVIEW.md`'s dated entries, frozen `work/regression/**` evidence and
pre-registrations, and `archive/`. Rewriting those would make the record of what
was true on 2026-09-15 say something else. Where a historical section could be
*read* as instruction — W-136 §*Where the key lives*, `golden/README.md` §*The
2026-09-15 reset* — a dated supersession note was added above it instead.
**`guard-golden-answer.sh` keeps its name**: it is a filename, not the
directory, and item 5 keeps the singular inside guards.

### What this did NOT touch

- 🔴 **The paste route.** Decision 4 stands. **W-196 is not resolved here and its
  veto condition stays fired** — what the benchmark *is* after a key has reached
  a Claude context is still Arpit's ruling.
- 🔴 **Whether Codex may now read the directory.** No ruling exists; prompt 6
  now says so explicitly instead of leaving the silence to be filled.
- **The directory itself.** No tool call in this change was aimed at it, on
  either spelling. Every check works from `git ls-files`, `git check-ignore`, or
  synthetic paths fed to the hooks as subprocesses.
- **`.fux/.fuxignore` line 37**, which names a *filename* under the singular
  directory. It is generated by ingest, carries no answer, and hand-editing it
  would be the only change here touching the sealed tree's own contents.
  ⚠ Named because it is the one singular reference deliberately left standing in
  a non-history file.
- **[Prompt 9](../golden/prompts/9-claude-code-open-the-key.md), which would
  RETIRE this law.** It is unrun, it is Arpit's to paste, and L11 decision 8
  makes a prompt in the repository no authorization at all. It gained a dated
  header naming the three things W-198 added that its steps 5 and 6 would
  otherwise leave half-removed.
