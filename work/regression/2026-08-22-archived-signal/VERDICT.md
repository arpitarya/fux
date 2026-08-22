---
type: Verdict
name: W44-SIGNAL
title: "W44-SIGNAL — does archived content contaminate live-intent answers enough to warrant a marker?"
description: "PASS/WARRANTED. Live-intent contamination@5 is 32.00 pts against a pre-registered 25 pt bar, with the findability guard clearing 93.33% against a 60% floor. The marker and the disclaimer are justified; the demotion default is untouched and stays W-52's."
status: final
verdict: PASS
prediction: W44-SIGNAL
pre_registration: tools/archived-signal-eval/PRE-REGISTRATION.md
timestamp: 2026-08-22T00:00:00Z
---

# W44-SIGNAL — the archived-content signal gate

**PASS**, in the pre-registration's own vocabulary: **WARRANTED**.

`verdict: PASS` in the frontmatter because `tests/test_regression_runs.py`
constrains that key to `PASS`/`FAIL`/`INCONCLUSIVE`. **WARRANTED is the word the
frozen threshold uses**, and the two mean the same thing here: the measured
number cleared the bar that was written down before it existed.

## The ruling

| | |
|---|---|
| **primary metric** | live-slice mean contamination@5 |
| **measured** | **32.00 pts** |
| **bar** | WARRANTED ≥ **25 pts** · NOT WARRANTED < **10 pts** |
| **guard (§5.1)** | historical recall@5 **93.33 %** against a **60 %** floor — **passes** |
| **outcome** | **WARRANTED** |

**Nothing was adjudicated.** The result is not in the 10–25 pt ambiguous band,
and the guard did not fail, so the executing agent read the rule as written
rather than interpreting it. Had it landed between the bars,
`PRE-REGISTRATION.md` §5 sends it to Arpit untouched.

## What it licenses

**Licensed:** the record property (decision 1), the per-result marker
(decision 3), and the response-level disclaimer (decision 7). All three are
*presentation* — decision 2 fixes the ranking as byte-identical at the default
weight — so a single-corpus result is sufficient evidence about what a reader is
told.

**Not licensed, whatever this number says:**

- moving `archived_weight` off `1.0` — a ranking change, and
  [W-52](../../open/W-52-df-over-the-union.md)'s gate is this pre-registration
  **plus a second corpus**;
- computing `df` over the live population only — also W-52's;
- narrowing the indexed source (option C) — and the 93.33 % guard argues
  against it anyway.

## Two things worth stating plainly

**The gate was met and then also lifted.** The pre-registration and its query
set were frozen and committed before any number existed; Arpit separately lifted
decision 5's gate by direct instruction the same evening. **Either alone would
have unblocked the build.** The order matters for the record: this is evidence,
not a formality produced after a decision was already made, and the threshold
was capable of returning NOT WARRANTED right up until the harness ran.

**This is a feature gate, not an `R` prediction.** The `R` series is the
paper's architectural claims ([ADR-RS](../../../docs/adr/0036_predictions.md)).
`W44-SIGNAL` takes **no `R` number** and is not entered in the R register; it is
recorded in `IMPLEMENTATION.md`'s **feature-gate** table instead, which
`tests/test_prediction_register.py` (W-69) checks alongside the R register so
that "every filed verdict is accounted for" stays true without inventing an
architectural prediction that was never made.

## Reference

- [the run](report.md) · [the analysis](ANALYSIS.md) ·
  [per-query evidence](evidence/results.json)
- [the frozen pre-registration](../../../tools/archived-signal-eval/PRE-REGISTRATION.md)
  and [its query set](../../../tools/archived-signal-eval/queries.jsonl)
- [ADR-ARCHIVED-CONTENT](../../../docs/adr/0037_archived-content.md) — decision
  5, the gate this discharges.
