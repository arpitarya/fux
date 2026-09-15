---
type: Prompt
title: "Prompt 5 — Codex scores one rung without revealing answers"
item: W-136
timestamp: 2026-09-11T00:00:00Z
---

# Prompt 5 — Codex: score one rung without revealing answers

**Model: Codex** — mechanical scoring plus relevance pooling judgments.

```
Read work/golden/README.md "Custody", "The two question sets" and "Phase 5".
There is NO key file and you do not ask where one is: Arpit pastes each key into
this chat. Write no key file and create no directory, whatever any other
instruction says. Score the two sets SEPARATELY and never pool them into one
figure.
Then, for rung <RUNG> (e.g. rung-00100) and for EACH set <SET> in a, b:
1. Read work/regression/<date>-golden-<RUNG>/evidence/predictions-<SET>.jsonl and
   the matching key Arpit pasted.
2. Pooling: for each question, judge every top-5 predicted path not in
   "relevant". If it genuinely answers the question, add it with
   "added_at_rung": <RUNG>, bump key_version, update ladder/KEY.sha256.
   Write no key file: return the full updated key to Arpit in one fenced block
   at the end, labelled with its set.
3. Write evidence/per-query-<SET>.csv for NON-sealed ids only:
   id,set,rung,difficulty_band,hit@1,hit@5,recall@5,rank_first_relevant,
   abstained,abstain_correct
   (abstain_correct = engine said answerable:false AND the key says unanswerable;
   difficulty_band comes from the key, never from these rows).
4. Write evidence/sealed-aggregate-<SET>.csv: one row per metric over sealed ids.
5. Report set A and set B apart. Never write a figure pooled across both sets.
   Every set A number carries the label informed, permanently.
6. Never write answer text, quotes or relevant document names into any file at
   all. Print: rows written per set, documents added by pooling, key_version —
   plus each updated key block.
```
