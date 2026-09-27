---
type: Analysis
description: "What the mined-expansion capture shows before scoring, and what it cannot show. No correctness claim: no key and no arm score was read."
run: 2026-09-27-mined-expansion
item: W-168
filed: 2026-09-27
---

# ANALYSIS — mined-expansion arms, before scoring

## 1 · Untagged rank 1 never moves, so clause 2's exposure is the tagged hits

**Symptom.** At every weight, every rank-1 change is on a question tagged
`expansion_form` (report §2). No untagged question changes its rank-1 document.

**Why it matters.** Clause 2, *no new misses*, is read over the whole set. With
no untagged rank-1 change, the only place a new miss can come from is a tagged
question that hits at rank 1 in the baseline. That was **9** on the
precondition's capture, which the baseline reproduces on 80 of 80 rows. A clause
that holds is still a clause that held; this note says where it could have
failed, so a pass is not read as safety across all 80.

**Repro.** `describe.py`, the `top1Δ` and `tagged` columns.

## 2 · The changes are few, and they cannot all be wins by arithmetic

Rank 1 changes on **2 / 5 / 6 / 7** questions. The bar needs a net of **6** with
no loss (SR-RS d19), so **`0.1` cannot clear clause 1 at all**, and `0.2` can
clear it only if all 5 changes are wins and another arm moves more. This is
arithmetic on the capture, not a prediction of the score.

## 3 · Membership moves more than rank 1 at `0.5`

At `0.5`, **11** questions gain or lose a document in their top 10, against 7
rank-1 changes. The fold adds long-form or short-form hashes that other
documents also carry, which is the *hurts* row of the bar's direction table: a
short form with more than one expansion, or a defining document lifted by both
spellings. **Unresolved:** which documents entered, and whether any is a
relevant one, needs the score.

## Owed

- **Nothing to the engine** before the verdict. The mechanism ships at `0.0`
  whatever the outcome; on FAIL, what happens to the code is Arpit's (the bar,
  §The decision rule).
