---
type: Analysis
description: "W-257 pilot - what a 31.8 percent first-pass refusal says: the filter refuses the paraphrases doc2query exists to add, so the full rung's real question is whether --check helps or hurts."
run: 2026-10-09-enrich-pilot-gen4
item: W-257
classification: blind
filed: 2026-10-10
---

# Analysis — the filter and the method pull opposite ways

**This is a surface capture, not a measurement.** [Report](report.md).

## §1 — the refusal is visible now

SR-ENRICH d16 called the filter *"too small to see"* at 2 of 98. Here it refuses
**237 of 745 (31.8 %)**, and 77 of 94 documents lose at least one question. On a
blind author's questions, the filter is the largest single effect in the pilot.

## §2 — what it refuses

Every refusal has one reason: the question, scored with `title` and `ctx`
zeroed, does not bring its own document into the top 3. The refused lines are
**paraphrases in a reader's words**, for example *"above 8 degrees … a breach"* for a
document that writes *"above +8.0 C … excursion"*, or *"GPS tracking provider"* for a
document that says *"telematics"* five times and *"tracking"* never. That
vocabulary gap is exactly what doc2query is meant to bridge. The filter's own
footer gives the trade-off: such a question *"adds terms that pull OTHER
documents up."* ⚠ **Which side wins is a measurement, not a reading of these
lines**, and it is what B-109 asks.

## §3 — what it does and does not license

- **Licensed:** the blind prompt works end to end (plan → write → check, 94/94
  files). The refusal rate is far from wholesale (68 % of questions pass), so
  W-257's *"a blind author can fail `--check` wholesale"* hazard did not occur.
- **Not licensed:** any claim that the refused questions hurt or help ranking.
  No `ask` ran, by design.
- **For the full rung's pre-registration:** both arms already exist with no
  extra spend. The **filtered** arm keeps the 508 passing questions; the
  **unfiltered** arm keeps all 745. A paired run between them is B-109's
  answer, and it is the case for **not** rewriting refused questions into the
  documents' own words. That rewrite would delete the very arm B-109 needs.
