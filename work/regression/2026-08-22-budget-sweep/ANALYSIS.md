# ANALYSIS — the budget sweep, 2026-08-22

## The headline, stated once, plainly

**The greedy assembler is not "flat" against plain top-k — it is measurably
worse on the path `fux answer` actually ships**, at realistic budgets, and
the cause is identified: the per-document cap binds against the *only*
candidate document when there is exactly one, which is every real call
today.

## Why this is not a case for deleting the assembler

ADR-REFER veto condition 2's deletion trigger is specifically "flat" —
score-per-byte packing earning nothing over truncation. **That part of the
hypothesis is not confirmed and not falsified either way as a wash**: once
the per-doc cap stops binding, GREEDY and NAIVE are byte-identical, meaning
the packing logic itself is inert on this corpus, not harmful. Deleting the
whole assembler over a defect in one of its three mechanisms (the floor, the
per-byte resort, the per-doc cap) would remove two mechanisms that this run
found no fault with, based on a defect in the third.

## Why this is not a case for "keep it, unchanged" either

The rule's numeric output (NOT FLAT, mean |delta| 12.55%) is real and would
normally mean "keep it as shipped." But every single measured delta is
negative — the assembler never wins, only loses or ties, in both the
shipped SINGLE-candidate case and the general MULTI case. **A rule that
outputs "keep" on a result where the thing being kept never once
outperformed the baseline is being satisfied by its letter and violated by
its purpose.** That mismatch is reported here rather than smoothed over,
per CLAUDE.md's own instruction for exactly this situation ("if the
measurement turns out not to test what the threshold assumed, say that").

## What is actually recommended

**A narrower fix than either "delete" or "keep unchanged": the per-document
cap should not bind when there is only one candidate document.** This is a
small, testable code change (`assemble()` gains a
`len({s.doc_id for s in candidates}) > 1` guard around the cap, or the cap
is computed per the *actual number of candidate documents*, not a flat 50%),
with its own before/after on `answer`'s shipped `--json` output — the
existing tests
(`tests/refer/test_assemble.py::test_the_best_answer_is_not_crowded_out_by_cheaper_fragments`
and the per-doc cap's own tests) are the right place to add the
single-candidate case this run's numbers say is currently underserved.

**This is a recommendation, not an action taken in this run.** Per the
"measuring and fixing in the same motion" hazard named in `report.md` §4,
no code changed as part of this measurement.

## Answering ADR-REFER's veto condition 2, honestly

The condition as written: *"a measured hit-rate on real Fux workloads shows
[the assembler] no better than plain top-k... then take the simpler code."*
**This run's answer is neither of the two outcomes the condition
anticipated.** It found the assembler's packing logic to be a wash
(consistent with "no better," which would argue for simplifying) **and**
found a specific, fixable defect that is not an argument against the
packing logic at all. Recommend ADR-REFER record this as: **veto condition 2
is answered with a finding narrower than either branch it was written for
— not closed as "assembler validated," not closed as "assembler deleted."**
The record's own next step, if Arpit agrees with the recommendation above,
is a new small item for the per-doc-cap fix, separate from this
measurement.

## Reproduce

```bash
cd fux/tools/refer-budget-sweep
python3 budget_sweep.py out.json
```

Corpus determinism already established in W-57's run; this sweep does not
regenerate it.
