# 2026-08-22 — the refer-plane budget sweep (ADR-REFER veto condition 2)

**A measurement against a pre-registered rule, with a result the rule did
not fully anticipate.** The threshold, arms and verdict rule were frozen in
[`PRE-REGISTRATION.md`](PRE-REGISTRATION.md), committed before this script
produced a number.

- **Engine:** working tree at `fa3ba30` (origin/main; the uncommitted local
  diff this session does not touch `src/fux/refer/`).
- **Corpus:** `fux-lab/graph-acceptance` — the same 66-document corpus
  [W-57](../../work/open/W-57-graph-lane-acceptance.md) measured against.
- **Reproduce:** `tools/refer-budget-sweep/budget_sweep.py out.json`.
- **Raw:** [`evidence/budget-sweep-results.json`](evidence/budget-sweep-results.json).

---

## 1 · The numbers

`delta_pct = 100 * (greedy_value - naive_value) / naive_value`, per budget.
Negative means GREEDY captured **less** value-mass than NAIVE.

### SINGLE (the condition `fux answer` actually ships)

| budget | greedy value | naive value | delta |
|---|---|---|---|
| 500 | 2.961 | 3.858 | **−23.25%** |
| 1000 | 4.816 | 7.468 | **−35.51%** |
| 2000 | 7.383 | 8.848 | **−16.56%** |
| 4000 | 8.848 | 8.848 | 0.00% |
| 8000 (`DEFAULT_BUDGET`) | 8.848 | 8.848 | 0.00% |
| 16000 | 8.848 | 8.848 | 0.00% |

**Mean \|delta\| = 12.55%.**

### MULTI (the general API's case, 3 candidate documents)

| budget | greedy value | naive value | delta |
|---|---|---|---|
| 500 | 7.427 | 8.064 | −7.90% |
| 1000 | 10.877 | 15.690 | **−30.68%** |
| 2000 | 20.803 | 23.568 | −11.73% |
| 4000 | 26.184 | 26.184 | 0.00% |
| 8000 | 26.184 | 26.184 | 0.00% |
| 16000 | 26.184 | 26.184 | 0.00% |

**Mean \|delta\| = 8.38%.**

## 2 · Applying the pre-registered rule, verbatim

The rule (§7): FLAT if mean \|delta_pct\| for SINGLE < 5%. **12.55% ≥ 5%, so
by the letter of the rule the verdict is NOT FLAT — keep the assembler.**

**That is the technically correct application of the rule, and it is also
the wrong takeaway if read as "the assembler wins."** NOT FLAT was written
to mean *"greedy clears the naive baseline by enough to earn its
complexity."* Every measured delta here is **negative or zero — GREEDY never
beats NAIVE at any budget, in either condition, and loses by up to 35.5%
at the budgets closest to real answer sizes (500–2000 bytes).** The rule's
binary didn't anticipate a result where the numeric threshold and the
substantive claim point opposite directions. Reporting "NOT FLAT" without
this paragraph would misrepresent the finding.

## 3 · Why — this was flagged as a likely finding *in the pre-registration*, §8

**The per-document cap (`PER_DOC_FRACTION = 0.5`) fires even when there is
exactly one candidate document — which is every real `fux answer` call
today** (`src/fux/query/refer_answer.py` passes `refer()` a single
`(doc_id, loc, sha)` tuple). The cap exists to stop one document dominating
*when several are competing for the same budget*. With one candidate, there
is no other document to protect against, so the cap simply throws away up to
half the budget — exactly the gap the numbers show closing once a
budget is generous enough that the capped half already holds everything
relevant (4000+ bytes here).

**Not a re-derivation of the greedy score-per-byte idea being wrong.** At
every budget in both conditions, once the per-doc cap stops binding
(≥4000 bytes here), GREEDY and NAIVE are byte-identical in value-mass — the
score-per-byte resort by itself does not lose or gain anything over simple
truncation on this corpus. **The defect is the cap's unconditional
application, not the packing algorithm.**

## 4 · What this does and does not settle

- **Settles:** the score-per-byte packing itself is not the problem — it
  performs identically to naive truncation whenever it's allowed to use the
  budget it's given.
- **Finds, not settled:** the per-document cap actively costs value on the
  exact call shape `fux answer` ships today, at the exact budgets a real
  answer uses (well under `DEFAULT_BUDGET`'s 8000 bytes — a short/medium
  answer is closer to 500–2000 bytes of cited text).
- **Not decided here, on purpose:** whether to (a) skip the per-doc cap when
  `len(candidates) == 1`, (b) delete the cap outright, or (c) something else.
  That is a code change with its own before/after on `answer`'s shipped
  output — the same "bigger than it looks because the plane is load-bearing"
  hazard [W-59](../../work/open/W-59-refer-plane-measurement.md) already
  names for the assembler-deletion path. Measuring and fixing in the same
  motion is how a rushed patch gets shipped off one run's numbers; this
  record stops at the finding.

See [`ANALYSIS.md`](ANALYSIS.md) for the recommendation.
