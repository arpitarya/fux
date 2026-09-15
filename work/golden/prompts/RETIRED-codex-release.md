---
type: Prompt
title: "RETIRED — the freeze-and-release prompt (its three jobs moved on 2026-09-15)"
item: W-136
timestamp: 2026-09-11T00:00:00Z
---

# RETIRED — the freeze-and-release prompt

🔴 **Do not run this.** It is kept because nothing here gets deleted, not because
it still works: it asks *"is the answer key (1) in the file, or (2) in the
chat?"*, a question [L11](../../../records/0012_LAW-11-sealed-answer-key.md)
deleted on 2026-09-15 by giving it one permanent answer.

**Where its three jobs went, 2026-09-15:**

| it used to | now |
|---|---|
| verify every rung manifest against its directory | [prompt 4](4-claude-corpus.md), which starts by checking the eight existing rungs |
| mark 20 % of ids `sealed` | [prompt 2](2-codex-questions.md) and [prompt 3](3-claude-questions.md) — the author marks its own holdout |
| emit the questions-only file | the same two prompts, as **block 1** of the two-block handoff; block 2 is the key, which Arpit keeps |

**Restoring it as a live step is Arpit's call**, and it would need the custody
question cut out first. The text below is the 2026-09-14 version, unchanged.

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
