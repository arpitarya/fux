---
type: Pointer
description: "One line: the current state and the immediate next step. Overwritten every session."
---

🔴 2026-09-22 Cowork (Opus): **NEW RECORD SR-WORK-TESTDATA (0068) — the test-data checklist, T1–T14 — and PROMPT 10 for the inputs four features lack. W-215 still waits on Arpit.**

- **[SR-WORK-TESTDATA](../records/0068_WORK-test-data.md)** — fourteen one-line items, each pointing to its rule's home; **T4 anchor-only vocabulary**, **T5 abbreviation pairs** and **T11 git history** stated there because nothing owned them. **Every test-data prompt links it**, gated by `tests/test_test_data_prompts.py`.
- **[Prompt 10](golden/prompts/10-claude-feature-input-seed.md)** — an isolated claude.ai chat writes the seed additions and **`set-3-u`**. **Not run; his, after `set-2-u` is scored.** Running it rebuilds the ladder.
- ⚠ Commit, then re-run `gen-components` + `sr-hash`; run `test_sr_freshness.py` from Claude Code (the bridge cannot).

**Earlier the same session:**

🔴 2026-09-22 Cowork (Opus): **W-216 AND W-217 ARE WITHDRAWN — NOTHING WAITS ON AN UNLOCK. ONE ITEM WAITS ON ARPIT: W-215.**

**His review:** *"is any item block on golden unblock ?? if no then no need for work item."* **The answer was no**,
and the two items saying yes were wrong about why.

🔴 **Scoring needs no unlock.** [L11](../records/0012_LAW-11-sealed-answer-key.md) decision 13's scoring carve-out
attaches to **his hand**: `tools/golden-score/score.py`, started from his own shell, reads the key **while the tree
stays LOCKED** — *"an unlock does NOT replace it."* The lock binds a Claude tool call; it has never bound him. W-216
claimed scoring `set-2-u` needed the unlock. It did not, so nothing in the queue waited on W-216 or W-217.

**Filed:** [SR-WORK-GOLDEN](../records/0066_WORK-golden.md) decision 16 **amended** — a switch item exists **only when
an open item actually waits on the switch**; when one does, it still gets its own 🔴 row naming the verb, and the lock
item is still filed with its unlock item. The generated `CLAUDE.md` bullet follows it (`gen-golden.py`, `sr-hash.py`
re-run). **W-216 and W-217 archived unchanged** to `archive/open/`, with map rows naming the false premise — they are
decision 16's worked counter-example.

**The inbox:** 🔴 **[W-215](open/W-215-generation-2-corpus.md)** — **score `set-2-u` from your own shell, no unlock**,
then rule whether item 1 is enough or items 2–4 and 6 (new seed documents, a ladder rebuild) go ahead. **W-168** waits
on it.

⚠ **Housekeeping, stated:** this session's `git status` left an empty `.git/index.lock` it could not unlink, which
would have blocked the next commit on this machine. Removed after Arpit granted delete permission; nothing else was
deleted.

🔴 **The golden tree is LOCKED and this session went nowhere near the key.**
