---
type: Prompt
title: "Prompt 3 — Codex freezes the ladder and releases the questions"
item: W-136
timestamp: 2026-09-11T00:00:00Z
---

# Prompt 3 — Codex: freeze the ladder and release the questions

**Model: Codex** — mechanical checks plus choosing a balanced sealed subset.

```
Read work/golden/README.md "Phase 3". Then:
1. Verify every work/golden/ladder/rung-NNNNN.sha256 against its own directory
   ~/my_programs/fux-benchmark/corpora/golden/rung-NNNNN/ (hashes match; each
   rung's documents contain the previous rung's byte for byte; seed/ files present
   in every rung; a work/golden/ladder/rung-NNNNN.index exists). Report mismatches and
   stop if any.
2. In work/golden/golden-answer/answers.jsonl set "sealed": true on 20% of ids,
   balanced across types. Do not change anything else.
3. Write work/golden/questions.jsonl with ONLY {"id", "question"} per line,
   sorted by id. No type, answerable, difficulty or sealed fields.
4. Write the SHA-256 of answers.jsonl to work/golden/ladder/KEY.sha256.
Print only: rung counts verified, number sealed, number released.
```
