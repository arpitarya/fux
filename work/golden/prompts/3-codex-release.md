---
type: Prompt
title: "Prompt 3 — Codex freezes the ladder and releases the questions"
item: W-136
timestamp: 2026-09-11T00:00:00Z
---

# Prompt 3 — Codex: freeze the ladder and release the questions

**Model: Codex** — mechanical checks plus choosing a balanced sealed subset.

```
Read work/golden/README.md "Where the key lives" and "Phase 3".
Before anything else, stop and ask Arpit, and wait for his answer:
"Is the answer key (1) in work/golden/golden-answer/answers.jsonl, or (2) will
you paste it here in the chat?" Do not open or create that file until he says (1).
Then:
1. Verify every work/golden/ladder/rung-NNNNN.sha256 against its own directory
   ~/my_programs/fux-lab/corpora/golden/rung-NNNNN/ (hashes match; each
   rung's documents contain the previous rung's byte for byte; seed/ files present
   in every rung; a work/golden/ladder/rung-NNNNN.index exists). Report mismatches and
   stop if any.
2. Set "sealed": true on 20% of ids, balanced across types; change nothing else.
   (1) file: edit it in place. (2) chat: write no key file — return the full
   updated key to Arpit in one fenced block at the end.
3. Write work/golden/questions.jsonl with ONLY {"id", "question"} per line,
   sorted by id. No type, answerable, difficulty or sealed fields.
4. Write the SHA-256 of the updated key (the file, or the exact text you return)
   to work/golden/ladder/KEY.sha256.
Print only: rung counts verified, number sealed, number released.
```
