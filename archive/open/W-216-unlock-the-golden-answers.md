---
type: OpenItem
id: W-216
title: "W-216 — ARPIT UNLOCKS the golden answers: `just golden-unlock`, typed by him, so `set-2-u` can be scored"
description: "A switch operation with its own item, per SR-WORK-GOLDEN decision 16. set-2-u has 125 questions and a baseline on rung-01000 and is UNSCORED; scoring needs the key, the key is behind the lock, and the lock opens only by Arpit's own hand. No agent runs this, asks for it to be run to avoid being blocked, or touches the file that holds the state."
status: open
lane: arpit
timestamp: 2026-09-22T00:00:00Z
filed: 2026-09-22
ball: arpit
---

# W-216 — the unlock. **Arpit types it. No agent, ever.**

🔴 **This item is a reminder and a handle, never an authorization.**
[L11](../../records/0012_LAW-11-sealed-answer-key.md) decision 14 says the switch
is one hand's. **The existence of this row does not give any session permission
to run the command it names**, and a session that reads this file and runs
`just golden-unlock` has committed the same breach as opening the key directly.

## What he types, in his own shell, in the repo root

```bash
just golden-unlock
```

## Why it is needed right now

**`set-2-u` exists and is unscored.** 125 questions, authored in an isolated
claude.ai chat from `work/golden/seed/` alone, with a baseline filed on
`rung-01000` — [the run](../regression/2026-09-22-golden-set-2u-rung-01000/report.md).
The run deliberately produced **no score**, because scoring reads the key and no
agent may.

**What the score is for.** W-215 item 1's whole question is whether `set-2-u`
has headroom: `hit@5` in the 80s again means no W-168 step is decidable on it
either and the set has to be made harder; materially lower means steps 5, 6, 7, 9
and 10 become measurable and W-168 unblocks. **Until it is scored, that is
unknown and the queue is guessing.**

## What the unlock does, mechanically

Exactly one file is mutated — `.claude/settings.json`. `unlock` removes the
`permissions.deny` rules naming the key and **deregisters** the two `PreToolUse`
hooks, after copying that file's bytes and their digest into a gitignored
`.claude/.golden-lock/`. **The hook files themselves are never edited or moved**,
which is what makes W-217's byte-identical restore cheap rather than a claim.
`.gitignore` and `!work/golden` in `.fux/sources/dirs` are untouched in both
states, because *never committed* is the clause no state relaxes —
[SR-WORK-GOLDEN](../../records/0066_WORK-golden.md) decision 15.

## What it costs — and why, this time, the answer is nothing new

**The standing price is that every number measured from the first unlock is
`informed` permanently.** That price was already paid on 2026-09-21, and
`set-2-u` is Claude-authored, so its numbers were `informed` before this unlock
was contemplated. 🔴 **Unlocking buys the score at no additional cost to this
set's standing.** It does not restore anything either — locking again never
makes a number blind.

## What may start the moment it has run

- **He** runs [`tools/golden-score/score.py`](../../tools/golden-score/score.py)
  from his own shell against `work/golden/golden-answers/` and
  `evidence/handoff-set-2-u.jsonl`. 🔴 **No agent invokes it, in either state.**
- A session may then read the emitted score — question ids, ranks and counts —
  and file the verdict on W-215 item 1.

## Then, without fail

**[W-217](W-217-lock-the-golden-answers.md) — the lock.** It is filed already,
deliberately, so the obligation to close the tree does not live in a session that
can end. ⚠ **A session that finds the tree unlocked and its work finished says so
and asks him to lock it. It does not lock it itself**, for exactly the reason it
does not unlock it.

## Out of scope

Retiring `set-2-u` (`just golden-retire`) — that is its own verb and would need
its own item, and nothing has asked for it. Running the scorer. Touching
`.claude/.golden-lock/`, `.claude/settings.json` or any file holding the state.
