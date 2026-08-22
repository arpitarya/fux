---
type: Pre-Registration
title: W-59 budget sweep — greedy assembler vs plain top-k
timestamp: 2026-08-22T00:00:00Z
---

# Pre-registration — the refer-plane budget sweep (W-59, ADR-REFER veto condition 2)

**Written before any number was produced.** Committed in the same change as
the script that runs it and before that script has been run for a number
that counts.

## 1. The question

`src/fux/refer/assemble.py` packs citations into a byte budget **greedy by
score-per-byte**, with a floor that seats the single best-scoring passage
first. ADR-REFER's veto condition 2: *"a measured hit-rate on real Fux
workloads shows [the assembler] no better than plain top-k with truncation —
then take the simpler code."* This has never been measured.

## 2. The metric

**Value-mass**: the sum of `citation.score` for every citation actually
included, never a partial/truncated one (the assembler's own `Citation` type
has no partial form, and the baseline below is held to the same contract for
a fair comparison — no citation is truncated mid-passage in either arm).

## 3. The two arms

- **GREEDY** — `assemble()` as shipped: best-absolute-score seated first,
  everything else packed by score-per-byte, no candidate document may exceed
  `PER_DOC_FRACTION` (50%) of the budget.
- **NAIVE** — score-descending order, no per-byte resort, no per-document
  cap: include whole citations until the next one would not fit, then stop.
  This is "plain top-k with truncation" read as "top-k, truncated to what
  fits" rather than "top-k, with the last one's text cut mid-sentence" — the
  latter is not implementable against `assemble()`'s own citation contract
  without inventing a second contract this record does not ask for.

## 4. The budgets

`500, 1000, 2000, 4000, 8000, 16000` bytes — `8000` is `DEFAULT_BUDGET`; the
rest span from "one short passage" to "generous."

## 5. The two conditions

- **SINGLE** — one candidate document per query, because
  `src/fux/query/refer_answer.py` calls `refer()` with **exactly one**
  candidate (`[(doc_id, loc, sha)]`) — this is what `fux answer` actually
  ships today.
- **MULTI** — 3 candidate documents per query (the correct one plus 2
  plausible-but-wrong ones from the same team/topic), because the general
  `assemble()`/`refer()` API supports multiple candidates and a future verb
  may use it that way. Recorded as the forward-looking case, not the shipped
  one.

## 6. The corpus and queries

The `graph-acceptance` fux-lab corpus (66 documents, committed generator,
seed `20260822`) — the same corpus [W-57](../../work/open/W-57-graph-lane-acceptance.md)
measured against. 5 queries for SINGLE, 3 for MULTI, chosen for topic
diversity (a supersession pair, a runbook, a policy area, an onboarding
guide) rather than cherry-picked for a result.

## 7. The verdict rule — decided before the numbers exist

| outcome | condition |
|---|---|
| **FLAT** (delete the assembler) | mean `\|delta_pct\|` across all 6 budgets, **for the SINGLE condition** (the shipped path — MULTI is recorded but does not gate the decision), is **< 5%** |
| **NOT FLAT** (keep it) | mean `\|delta_pct\|` ≥ 5% |
| **AMBIGUOUS** | the sign of `delta_pct` flips across budgets in a way that is not explained by the per-doc cap or a single-candidate floor effect — handed to Arpit, not adjudicated here |

`delta_pct = 100 * (greedy_value - naive_value) / naive_value` per budget,
per condition (script's own definition, `budget_sweep.py`).

**Why 5%, not a bigger or smaller number, stated rather than left implicit:**
the assembler is ~120 lines of extra logic (the resort, the floor, the
per-doc cap) against a ~15-line naive baseline. A difference under 5% is not
worth that maintenance cost by any reasonable engineering judgment; this
record does not claim 5% is a scientifically derived constant, only a
stated, defensible line drawn before the data existed.

## 8. What this does not test

- Real fetch latency or cache behaviour — R4 already measured that
  separately.
- Whether the *rescoring* (which passages are candidates at all) is good —
  held identical between arms on purpose, so only the packing policy differs.
- The per-document cap's own value in the SINGLE condition, where it can only
  ever bind against one document — flagged as worth a look in ANALYSIS.md
  regardless of the FLAT/NOT-FLAT verdict, because it is a separate,
  unregistered observation this run is likely to surface.

## Reproduce

```bash
cd ~/my_programs/fux-lab/graph-acceptance   # the corpus this sweep reuses
python3 budget_sweep.py out.json            # committed alongside this file
```
