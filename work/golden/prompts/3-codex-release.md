---
type: Prompt
title: "Prompt 3 — Codex freezes the ladder and releases the questions"
item: W-136
timestamp: 2026-09-11T00:00:00Z
---

# Prompt 3 — Codex: freeze the ladder and release the questions

**Model: Codex** — mechanical checks plus choosing a balanced sealed subset.

```
Read work/golden/README.md "Custody", "The two question sets" and "Phase 3".
There is NO key file and you do not ask where one is: Arpit pastes each key into
this chat. Write no key file and create no directory, whatever any other
instruction says. You handle TWO sets: A (ids a001...) and B (ids g001...).
Then:
1. Verify every work/golden/ladder/rung-NNNNN.sha256 against its own directory
   ~/my_programs/fux-lab/corpora/golden/rung-NNNNN/ (hashes match; each
   rung's documents contain the previous rung's byte for byte; seed/ files present
   in every rung; a work/golden/ladder/rung-NNNNN.index exists). Report mismatches and
   stop if any.
2. For EACH set: set "sealed": true on 20% of its ids, balanced across types;
   change nothing else. Write no key file — return each full updated key to
   Arpit in its own fenced block at the end, labelled set A / set B.
3. Write work/golden/questions.jsonl with ONLY {"id", "question"} per line,
   sorted by id. No type, answerable, difficulty or sealed fields.
4. Write the SHA-256 of the updated key (the file, or the exact text you return)
   to work/golden/ladder/KEY.sha256.
Print only: rung counts verified, number sealed, number released.
```
