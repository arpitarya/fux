---
type: Prompt
title: "Prompt 5 — Codex scores one rung without revealing answers"
item: W-136
timestamp: 2026-09-11T00:00:00Z
---

# Prompt 5 — Codex: score one rung without revealing answers

**Model: Codex** — mechanical scoring plus relevance pooling judgments.

```
Read work/golden/README.md "Where the key lives" and "Phase 5".
Before anything else, stop and ask Arpit, and wait for his answer:
"Is the answer key (1) in work/golden/golden-answer/answers.jsonl, or (2) will
you paste it here in the chat?" Do not open or create that file until he says (1).
Then, for rung <RUNG> (e.g. rung-00100):
1. Read work/regression/<date>-golden-<RUNG>/evidence/predictions.jsonl and the
   key from wherever Arpit said.
2. Pooling: for each question, judge every top-5 predicted path not in
   "relevant". If it genuinely answers the question, add it with
   "added_at_rung": <RUNG>, bump key_version, update ladder/KEY.sha256.
   (1) file: edit it in place. (2) chat: return the full updated key to Arpit in
   one fenced block at the end; write no key file.
3. Write evidence/per-query.csv for NON-sealed ids only:
   id,rung,hit@1,hit@5,recall@5,rank_first_relevant,abstained,abstain_correct
   (abstain_correct = engine said answerable:false AND the key says unanswerable).
4. Write evidence/sealed-aggregate.csv: one row per metric over sealed ids.
5. Never write answer text, quotes or relevant document names into any file
   except the key itself. Print: rows written, documents added by pooling,
   key_version — plus the updated key block if (2).
```
