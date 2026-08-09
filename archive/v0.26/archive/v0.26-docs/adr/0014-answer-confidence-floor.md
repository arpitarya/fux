---
type: ADR
title: ADR-0014 — Answer confidence floor (shipped disabled)
description: An absolute [answer] min_confidence floor was built and calibrated against all five eval gates — no value clears both the unanswerable and answerable gates simultaneously, so it ships as a documented, permissive-by-default knob rather than an enabled default.
timestamp: 2026-07-23T00:00:00Z
---

# ADR-0014: Answer confidence floor

- **Status:** accepted
- **Date:** 2026-07-23
- **Feature:** Trust & currency, honest-decline half (handoff 0006, M4)

## Context

The acme-payments realistic corpus measured `fux answer`'s "never fabricate"
contract holding only for gibberish: all 4 well-formed, out-of-scope questions
it was asked returned confident extractive prose with 1–5 citations from
unrelated documents (`docs/conformance/2026-07-22-acme-payments/`, Finding 3).
The decline path fired on a near-empty candidate pool with a **relative**
admission threshold (best-of-pool); a fluent off-topic question shares just
enough incidental vocabulary to keep the pool non-empty, so a weak best match
still answered.

`docs/compare/answer-decline-floor.compare.md` accepted an absolute confidence
floor (Option A) over a runner-up margin check (Option B), on the explicit
condition that **the shipped default is a measurement, not a guess** — DoD 6's
calibration rule requires the value to clear all five eval gates
simultaneously, or the finding itself (no value works) must be reported and a
permissive default shipped instead.

## Decision

**Build the floor; calibrate it against all five gates; ship it disabled.**

1. **Mechanism.** `[answer] min_confidence` (`AnswerParams`, validated to
   `[0.0, 1.0]`, `0.0` = disabled) sits *above* the pre-existing empty-pool
   early return in `_run_answer` — that return stays, because removing it
   would make "No confident matches" unreachable for a truly empty pool (the
   phase-4 rationale in CLAUDE.md). `best_confidence()` takes the max scored
   sentence `build_answer()` selected; when the floor is non-zero and the
   best score falls below it, `answer` declines through the same path as the
   empty-pool case. `query.answer.best_confidence()` and `prefer_current()`
   are shared between `_run_answer` and `why`'s decline explanation, so the
   two can never disagree about whether a given query would be declined.
2. **Calibration (`docs/conformance/2026-07-23-min-confidence-calibration/`).**
   A full sweep against acme's 4 unanswerable questions, the gibberish
   control, the 21-pair fixture gate, acme's 55 answerable pairs, and the
   synthetic 1k/5k/10k baselines found:
   - Declining all 4 unanswerable questions needs a floor **≥ 0.25** (the
     strongest fabrication scores 0.2488).
   - Zero false declines across the 55 answerable pairs needs a floor
     **≤ 0.087** (the weakest legitimate answer — a zero-overlap paraphrase —
     scores 0.0869).
   - **`[0.25, 0.087]` is empty.** 13 of 55 legitimate answers score at or
     below the strongest fabrication; the two populations interleave rather
     than separate on this signal.
   - The fixture-21 and synthetic-tier gates are confirmed **no-ops** for this
     knob: the former exercises `ask`, never `answer`; the latter's generator
     plants no answerable/unanswerable pairs at all. Neither constrains the
     value.
3. **Ship `min_confidence = 0.0` (disabled) as the default.** Per the compare
   doc's calibration rule: *"do not ship a default that declines correct
   answers."* An enabled default at any tested non-zero value would have
   false-declined a real answer starting at the very first sweep point
   (0.10). The knob stays exposed and documented in `fux.toml`/`TOML.md` for
   an environment that explicitly prefers a decline over a guess.

## Alternatives considered

- **Ship a non-zero default anyway (e.g. 0.25, "catches all 4 fabrications").**
  Rejected: it false-declines 11 of 55 (20%) correct answers on the very
  corpus used to justify it — exactly the failure this phase exists to
  prevent (a plausible-looking number that quietly breaks correct answers).
- **The runner-up margin check (Option B in the compare doc).** Rejected, and
  its own reopen-trigger does not fire: margin was deferred pending "a
  fabrication whose top score clears the calibrated floor" — there is no
  calibrated floor to clear, so a margin check cannot rescue a case where the
  absolute floor itself has no valid value.
- **Floor on the raw dense cosine instead of the pool-relative sentence
  score.** Not built here — flagged as the load-bearing follow-up (F1/F2
  below), because it changes what confidence the mechanism reads, not just
  its threshold, and deserves its own compare doc and evidence.

## Consequences

**Easier.** The mechanism, its config surface, and its calibration evidence
now exist — a future attempt at a working floor starts from a measured
score table (`evidence/acme-raw-scores.json`) instead of a guess, and an
environment willing to trade false declines for zero fabrication has the knob
today.

**Harder / owed.** The measured defect this phase set out to fix —
`answer` fabricating on well-formed out-of-scope questions — **is not fixed
in this release**, by the same honest-decline standard the phase itself set.
`docs/conformance/2026-07-22-acme-payments/evidence/unanswerable-fabrication.json`
and this ADR's calibration both show 0/4 declines at the shipped default. That
must not be quietly implied as resolved elsewhere in the docs.

**Follow-up, not in scope here (ANALYSIS.md §"Specific fux improvements"):**

- **F1/F2 — calibrate on an absolute, cross-query-comparable signal** (e.g.
  the raw top dense cosine, anchored to ADR 0010's measured 0.23–0.26 noise
  band) instead of the current pool-relative sentence score, which measures
  "best in *this* query's own candidate pool" and is not comparable across
  queries. This is the real path to a working floor.
- **F4 — document the limit as a guarantee, not an implied promise:**
  `answer` declines reliably only when the corpus has near-zero lexical
  overlap with the question; a fluent out-of-scope question sharing
  incidental vocabulary with real documents can still be answered, and
  citations must be verified. This is a permanent limit of model-free
  extractive QA (Rajpurkar et al. 2018), not a bug to be iterated away.

## References

- Rajpurkar, Jia, Liang, *Know What You Don't Know: Unanswerable Questions for
  SQuAD* (ACL 2018) — abstention as a first-class metric; the
  precision/recall frontier this ADR measures (decline-4/4 vs.
  zero-false-decline) is exactly the trade-off that paper formalizes.
- Measured: [`../conformance/2026-07-22-acme-payments/report.md`](../conformance/2026-07-22-acme-payments/report.md)
  §Finding 3 (the original 0/4) ·
  [`../conformance/2026-07-23-min-confidence-calibration/ANALYSIS.md`](../conformance/2026-07-23-min-confidence-calibration/ANALYSIS.md)
  (the full sweep and the empty-interval finding).
- [`../compare/answer-decline-floor.compare.md`](../compare/answer-decline-floor.compare.md) —
  the accepted fork, the calibration rule, and the deferred margin check.
- Internal: [handoff 0006](../handoff/0006-trust-currency-handoff.md) (the build
  contract) · [ADR 0010](0010-fuxvec-binary-dense-search.md) (the 0.23–0.26
  dense noise band F1/F2 would anchor to).
