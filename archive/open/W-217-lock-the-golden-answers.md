---
type: OpenItem
id: W-217
title: "W-217 — ARPIT LOCKS the golden answers again: `just golden-lock`, typed by him, the moment scoring is done"
description: "The other half of W-216, filed at the same time on purpose. LOCKED is the resting state; a tree left open is the failure this item exists to prevent, and L11 forbids a session from closing it itself, so nothing but this queue row can carry the obligation. Verifies every guard came back byte-identically; a mismatch is a breach to declare, not a thing to overwrite."
status: open
lane: arpit
timestamp: 2026-09-22T00:00:00Z
filed: 2026-09-22
ball: arpit
---

# W-217 — the lock. **Arpit types it. No agent, ever.**

**Waiting on [W-216](W-216-unlock-the-golden-answers.md)** and on the scoring run
that unlock exists for. 🔴 **Filed at the same time as W-216 and not afterwards**
— [SR-WORK-GOLDEN](../../records/0066_WORK-golden.md) decision 16. The reason is
plain: **a tree stays open when the only reminder to close it lived in a session
that ended**, and L11 forbids a session from closing it itself, so a queue row is
the only thing that can hold the obligation.

## What he types, in his own shell, in the repo root

```bash
just golden-lock
```

## What it must do, and the one thing to check

`lock` puts back the bytes `unlock` stashed in `.claude/.golden-lock/` and
**verifies the digest**. It re-registers the two `PreToolUse` hooks and restores
the `permissions.deny` rules naming the key.

🔴 **Every guard must come back byte-identically.** A restore that does not match
the digest is **a breach to declare, not a thing to overwrite** — `lock` refuses
rather than guessing, and that refusal is the point. If it refuses, **stop and
say so**; do not hand-edit `.claude/settings.json` to make it pass.

## How to confirm the tree is closed

```bash
just golden-state      # prints `locked` or `unlocked`
```

🟢 **`golden-state` is safe for anyone, agents included** — it reads one file
under `.claude/` and never goes near the key. It is the one verb of the four that
is not his alone, and it is how a session answers *"is the tree open?"* without
asking him.

## Definition of done

1. `just golden-lock` run by Arpit, and it did **not** refuse.
2. `just golden-state` prints `locked`.
3. `uv run pytest -q tests/test_golden_key_guards.py tests/test_golden_switch.py
   tests/test_golden_key_never_committed.py` — green. **The guards are the
   defence, so the proof that they are back is a test run, not a screenshot.**
4. Both this item and W-216 archived to `archive/open/` with their rows, per
   SR-WORK-OPEN-QUEUE rules 54–58.

## What is still true while the tree is unlocked

A session may read the key **for scoring and review and nothing else**. It is not
a licence to copy it, quote it into a document, write any part of it to a
committed path, or carry an answer into another session. 🔴 **Never committed is
the one clause no state relaxes.**

## Out of scope

Retiring any set. Unlocking again. Any agent running any of the three verbs this
item or W-216 names.
