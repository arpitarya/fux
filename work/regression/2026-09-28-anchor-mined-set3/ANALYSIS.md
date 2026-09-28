---
type: Analysis
description: "What the W-232 PASS does and does not show: the pair's wins split cleanly by step, the B floor is met with no margin, and one decider defect (arm names) was worked around, not fixed."
run: 2026-09-28-anchor-mined-set3
item: W-232
filed: 2026-09-28
---

# ANALYSIS — the shipped anchor + mined pair, after scoring

## 1 · The wins split cleanly between the two steps

**Symptom.** All 6 wins over B (mined off) are on step 4's 22 `expansion_form`
questions, and all 7 wins over C (anchor off) are untagged.

**Diagnosis.** The two switches act on disjoint questions on this set, so adding
one does not cost the other anything here. That is the claim the bar tested, and
this shows the mechanism, not only the count. It does **not** show that the two
never interact: no question in this set is both a mined form and an anchor case.

**Repro.** `python3 -c` over `evidence/decision.json` (`won`), intersected with
the `tagged` ids of `../2026-09-27-mined-expansion/evidence/tags-set-3-u.jsonl`.

## 2 · Against B, the floor is met with no margin

**Symptom.** 6/0 with a required net of 6 (p = 0.031), step 4's own margin.

**Why it matters.** A single flipped question in a later run would move the
comparison to INCONCLUSIVE. The **reopen-trigger** in the verdict covers it. No
change follows from this.

## 3 · The decider did not match its capture's directory names

**Symptom.** Run in place, `decide.py` exits 1 with *"not scored yet"*: it reads
`scores/am-X`, and the capture (and so `golden-score`) wrote `am3-X`.

**Diagnosis.** The second bar changed `SET` in the first bar's decider but kept
its arm names, and the capture chose new names. Nothing ran the decider against
the capture's real layout before scoring.

**Fix, specific:** a bar's author runs the frozen decider once, **after capture
and before scoring**, and checks that it refuses with *"not scored yet"* **for
the directory that capture wrote** (the refusal message names the path). This
is the first time it has happened, so it is recorded here and in the WORKLOG.
It is not yet a gate (SR-WORK-SESSION decision 13 makes the second occurrence
one).

**Repro.** `python3 work/regression/2026-09-28-anchor-mined-set3/evidence/decide.py`
exits 1 and names `scores/am-A/…`.
