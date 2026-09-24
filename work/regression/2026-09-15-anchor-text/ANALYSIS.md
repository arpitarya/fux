---
type: Analysis
description: "What the anchor capture shows before scoring, and what it owes. No correctness claim: no key and no anchor-arm score was read."
run: 2026-09-15-anchor-text
item: W-168
filed: 2026-09-24
---

# ANALYSIS — anchor arms, before scoring

## 1 · Clause 2 cannot fail on this capture, and that is not a pass

**Symptom.** At every weight, every rank-1 change is on one of the 27 tagged
questions (report §2). The 53 untagged questions are reordered lower in the list
(6–19 of them), but **not one changes its rank-1 document.**

**Why it matters.** Clause 2 counts `hit@1` wins minus losses on the untagged
53. With no rank-1 change there, it is `0 − 0` at every weight and **holds by
construction**. The regression the pre-registration fears still shows up, but
inside the tagged net: a tagged baseline hit (11 of them) that loses rank 1
counts as a loss in clauses 1 and 4. **The frozen rule is applied as written.**
This note stops a reader from treating *clause 2 held* as evidence of safety
beyond the tagged 27.

**Repro.** `describe.py`, the `top1Δ` and `tag` columns.

## 2 · There are more tagged rank-1 changes than tagged misses

At `2.0` and `3.0`, 17 and 18 tagged questions change their rank-1 document,
and only 14 tagged answerable questions miss at baseline. **So at least 3 or 4
of the changes land on questions that were hits at baseline**, or on the two
unanswerable ones. A change on a baseline hit is a loss only if the new first
document is not relevant, and only the score says which. Nothing is owed. It is
the reason the gain net, not the change count, gates.

## 3 · The hub control is exposed and barely moves

The hub is first on 5 questions at baseline and 4 at `3.0`. Its rank rises on
1–3 questions. Clause 3 fails only if the hub **becomes** first on a `hit@1`
miss, and it becomes first nowhere new in these captures (5 → 5 → 5 → 5 → 4).
So clause 3 is likely to hold, and its *half-moving* reading (a climb within
2–10 on a miss) is the one to watch.

## 4 · The anchor fold runs under the graph tier

`rung-01000`'s tune has `ask_boost = true`, so `ask` re-orders the lexical window
by RRF with PPR. The anchor field changes the lexical scores **before** that
fusion. The arms measure `ask` as the rung ships it, and the pre-registration
holds everything but `anchor`. **Stated, not a defect:** a PASS supports *anchor
at weight w under the shipped graph tier*, not the anchor field on its own.

## 5 · What is owed next

1. Arpit: `just golden-score work/regression/2026-09-15-anchor-text`.
2. A session that did not capture these arms: `evidence/decide.py` → `decision.json`, `per-query.jsonl`, then `VERDICT.md`.
3. On INCONCLUSIVE, Arpit, with the per-query rows.
