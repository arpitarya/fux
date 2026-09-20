---
type: OpenItem
id: W-198
title: "W-198 — `golden-answers/` is the canonical local key directory: L11 decision 3 amended, both spellings guarded"
description: "Arpit's ruling 2026-09-18 on W-197 — the plural directory holds answer docs and STAYS on disk. L11 is amended to permit a local, gitignored, agent-closed key directory; `golden-answers/` becomes the canonical spelling everywhere; every guard covers both spellings by glob; the Cowork-mount exposure is recorded. RATIFIED, NOT BUILT."
status: open
lane: agent
timestamp: 2026-09-18T00:00:00Z
filed: 2026-09-18
ball: agent
---

# W-198 — the key lives on disk again, guarded, under one name

**Model: Opus** — it amends a Law record, regenerates the two CLAUDE.md blocks a
test binds byte-equal, and touches four guards. ⚠ **RATIFIED, NOT BUILT.**

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
