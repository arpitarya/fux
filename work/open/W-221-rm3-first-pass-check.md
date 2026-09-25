---
type: Handoff
name: W-221
description: "Before RM3 (W-168 step 5) is filed away on its FAIL verdict: check whether the lexical-only top-10 the build fed RM3 differs from the graph-boosted top-10 `ask` actually shows on rung-01000. Resolves the open question in work/regression/2026-09-23-rm3/ANALYSIS.md §1."
item: W-221
filed: 2026-09-25
ball: agent
---

## Why this exists

[VERDICT](../regression/2026-09-23-rm3/VERDICT.md) ruled RM3 **FAIL** (drift
broken at every weight; `rm3_weight` stays `0.0`). [ANALYSIS](../regression/2026-09-23-rm3/ANALYSIS.md)
§1 flagged, before scoring, that the arms may not have tested the mechanism as
written: `rung-01000`'s tune sets `ask_boost = true`, so `ask` shows a
**graph-boosted** top 10. RM3's first pass reads the **lexical** ranking
(SR-EXPAND 16), so the ten feedback documents RM3 actually learned from can
differ from the ten a user would see. The pre-registration's stated reason for
`fbDocs = 10` was *"exactly the `--top 10` list the harness already
captures"* — if that was meant as the mechanism rather than a rationale, the
build tested the wrong ten documents and the arms need a re-run.

**Left unresolved by the verdict.** Arpit ruled the table's FAIL outcome
without this being checked either way.

## Definition of done

1. On `rung-01000` (index root
   `17fe414e52d2851697a15763dc7b42760f4d346961958b943c4dba73cd2a927d`), for a
   sample of `set-2-u` questions (the 92 tagged `rm3_underspecified`, or a
   representative subset), capture:
   - the **lexical** top 10 (the ranking RM3's first pass actually reads)
   - the **graph-boosted** top 10 (`ask_boost = true`, what `ask` prints today)
2. Compare the two top-10 lists per question: same document set? same order?
3. **No golden key is read.** This compares ranked document ids against each
   other, never against a relevance judgment — fully within what Claude may
   read under [L11](../../records/0012_LAW-11-sealed-answer-key.md).
4. Write the comparison (counts of identical / reordered / different-membership
   top-10s, with a couple of worked examples) to
   `work/regression/2026-09-23-rm3/evidence/first-pass-check.md`.
5. **Two outcomes, not a ruling either way:**
   - **Largely the same ten documents** (reordering only, or near-identical
     membership) → the mechanism concern is immaterial, the FAIL verdict
     stands as scored, and this item closes with that noted in
     `VERDICT.md`.
   - **Meaningfully different top-10s** → this is a 🔴 inbox row: tell Arpit
     the RM3 arms may have been tested against a first pass nobody sees, and
     ask whether the 2026-09-23 run should be re-registered against the
     graph-boosted list and re-run.

## Outcome (2026-09-25) — ambiguous, to Arpit

Run and filed: [first-pass-check.md](../regression/2026-09-23-rm3/evidence/first-pass-check.md).
The boosted list reproduces the capture on 125/125. **Documents:** 26 identical, 26 reordered, 73 with a different set;
rank 1 is the same on 124 of 125 questions; median overlap is 9 of 10; every displaced document is at lexical rank 6–10.
**Feedback terms:** identical set on 62; 2–6 of 10 differ on 35 (26 tagged). Neither of the
two outcomes below fits cleanly, so per §Hazards this is Arpit's call: re-register and re-run, or let FAIL stand.

## RULED 2026-09-25 (Arpit): *"re-run"*. Done as far as an agent may go

1. **Re-registered first**, as [`2026-09-25-rm3-boosted`](../regression/2026-09-25-rm3-boosted/PRE-REGISTRATION.md) (`d1eeaae3`). It changes one row: the feedback set.
2. **Built** at `0ff3078c`. SR-EXPAND 16 and both readers were changed, and W-222 was filed for a separate Node last-bit gap.
3. **Captured**: five arms on the frozen `17fe414e…` index, as described in the [report](../regression/2026-09-25-rm3-boosted/report.md).
   ⚠ The live `rung-01000` was rebuilt on 2026-09-23, so the arms were copied from the 2026-09-23 arm copies instead.
4. **Next, and not this session's:**
   - Arpit types `just golden-score work/regression/2026-09-25-rm3-boosted`.
   - Then a session that did **not** capture the arms runs `evidence/decide.py` and writes `VERDICT.md`.
   - INCONCLUSIVE goes to Arpit.

## Blockers

🔴 Arpit's score (inbox). Earlier: his ruling, given 2026-09-25. Before the run: none. Agent-executable: no code change, no build, reads only the released
question ids/text and produces ranked lists — nothing this touches is a golden
answer.

## Hazards

- Do not read `work/golden/golden-answers/` or any scored file under
  `evidence/scores/` — this item needs only ranked document ids, never a
  relevance judgment.
- If the comparison is ambiguous (neither clearly "same" nor clearly
  "different"), that ambiguity itself goes to Arpit rather than being called
  either way.

## Model

**Model: Sonnet** — a read-only comparison of two rankings already produced by
existing code paths; no design judgment, no new mechanism.

## Records this will touch

None if the outcome is "immaterial" (a note in `VERDICT.md` only). If the
outcome reopens the run, [SR-RS](../../records/0133_predictions.md) (the
prediction id) when the re-run is filed.
