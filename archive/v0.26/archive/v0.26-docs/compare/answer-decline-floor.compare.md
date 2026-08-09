---
type: Compare Doc
title: Answer Decline Floor
description: How `fux answer` should decline on well-formed out-of-scope questions — an absolute confidence floor, a runner-up margin check, or both. Proposed verdict is the absolute floor alone, calibrated against every existing eval set.
status: accepted
timestamp: 2026-07-23T00:00:00Z
tags: [answer, honest-decline, correctness]
---

# Answer Decline Floor — Comparison

> **Verdict (accepted 2026-07-23, Arpit):** **Add an absolute confidence floor to
> `answer`, above the existing empty-pool early-return. Configurable in
> `fux.toml`. Do NOT add the margin check in the same change.**
> **Status:** ✅ Accepted · **Confidence:** High on the
> mechanism, Medium on the default value until it is calibrated.
> **Honest caveat:** any floor trades fabrications for false declines. The
> defensible default is the one that removes fabrications *without* declining a
> single question the engine answers correctly today — which is a measurement,
> not a guess.

## Context

acme-payments measured the "never fabricate" contract and found it holds only
for gibberish:

- **Gibberish declines correctly** — `answer "xyzzy plugh …"` → `answer=null`,
  0 sources. This is the only decline case the synthetic gate ever tested.
- **All 4 well-formed unanswerable questions fabricate** — a confident
  extractive answer with 1–5 sources from unrelated documents. *"What is Acme's
  policy on cryptocurrency and stablecoin settlement?"* returns prose quoted from
  `0005-store-amounts-in-minor-units.md` with 5 sources.

Cause: the decline path fires on a **(near-)empty candidate pool**, i.e. near-zero
lexical overlap. A fluent out-of-scope question shares enough incidental
vocabulary ("policy", "API", "vendor", "configure") that the pool is non-empty,
and the admission threshold is **relative** (best-of-pool) rather than absolute.
So a weak best match still answers.

evidence: `../conformance/2026-07-22-acme-payments/evidence/unanswerable-fabrication.json`
· proposal: [`../proposals/honest-decline-well-formed-queries.md`](../proposals/honest-decline-well-formed-queries.md)

## The fork

### Option A — Absolute confidence floor

Decline when the best extractive score (and/or top dense cosine) falls below a
fixed threshold, independent of pool size. ADR 0010's measured **0.23–0.26 dense
noise band** is a natural anchor for the dense side.

### Option B — Runner-up margin check

Decline when the top candidate does not clear the runner-up by a margin. Rationale:
off-topic pools are *flat* — the acme fabrications drew 4–5 near-equal weak sources.

### Option C — Both, together

## Comparison matrix

| | A — absolute floor | B — margin | C — both |
|---|---|---|---|
| Catches the measured failure | **✓** (weak top score is the signature) | partly | ✓ |
| Catches a *strong* single wrong match | ✗ | ✗ | ✗ |
| Wrongly declines a legitimate consensus answer | no | **yes** — several docs agreeing is *good* | yes |
| Attributable when it misfires | **✓ one knob** | ✓ one knob | ✗ two interacting knobs |
| Calibratable on existing evals | **✓** | ✓ | harder — interaction effects |
| Reversible | ✓ config | ✓ config | ✓ config |

## The debate

**The case for the margin check (B), stated fairly.** The acme fabrications
shared a distinctive shape — a flat pool of near-equal weak sources, exactly what
"nothing here really answers this" looks like. A margin check keys on that shape
directly, and it would catch a case the floor misses: a pool whose absolute
scores are respectable but where nothing stands out.

**Why A alone wins.**

- **B has a false-positive mode that is structurally wrong.** When several
  documents genuinely agree on an answer, their scores are *legitimately* close.
  That is a corpus doing its job — a runbook, the ADR behind it, and the guide
  citing both. A margin check declines precisely there. The acme
  `cross-doc` class (n=6, hit@5 .833) is the population it would hurt.
- **A matches the measured signature.** In every one of the 4 fabrications the
  top score was *weak in absolute terms*. The floor is not a proxy for the
  failure; it is the failure's direct measurement.
- **One knob is debuggable.** With two interacting thresholds, a wrong decline
  has two possible causes and neither is attributable from the output. `fux why`
  can say "declined: best score 0.11 < floor 0.20" and that is a complete
  explanation.
- **The honest sequencing:** ship A, measure, and let B graduate on evidence of
  a residual class A cannot catch. Same discipline the supersession fork uses.

**Neither catches the hard case, and the docs must say so.** A single strong but
wrong match — a question whose vocabulary genuinely matches a passage that does
not answer it — defeats both. That is a real, permanent limit of extractive
retrieval without a model, and it belongs in the docs as a stated boundary, not
as an implied guarantee.

## The calibration rule (this is the load-bearing part)

The mechanism is safe; **the default value is the risk.** The threshold ships
only if it satisfies all of these simultaneously:

1. **Declines all 4** acme typed-unanswerable questions.
2. **Keeps declining** the gibberish control.
3. **Zero regression** on the 21-pair fixture eval gate.
4. **Zero regression** on acme's 55 answerable pairs (`answer` still answers
   every question it answers correctly today).
5. **Zero regression** on the synthetic 1k/5k/10k baselines.

If no single value satisfies 1–5, that is itself the finding: report the
best achievable trade-off with the measured cost, and **do not ship a default
that declines correct answers.** Prefer shipping the knob with a permissive
default plus the measurement over shipping an aggressive default.

## Configuration

```toml
[answer]
min_confidence = 0.0   # 0.0 = disabled (pre-0.25 behaviour); calibrated default set by M4
```

Rationale for exposing it: environments differ in how much they prefer a decline
over a guess. A regulated corpus wants the floor high; an exploratory one may
want it off. The escape hatch also makes the change trivially reversible in the
field without a release.

## Reopen-trigger

Revisit and add **B (margin)** when a corpus produces fabrications whose top
score clears the calibrated floor — i.e. evidence of the flat-but-strong pool
that A structurally cannot catch.

### Second data point — orbit-fulfillment, 2026-07-24: **B is REFUTED**

The trigger fired (orbit fabricates 4/4 on well-formed unanswerables, exactly as
acme did), so **B was measured directly** rather than left deferred
(`docs/conformance/2026-07-24-orbit-fulfillment/`, `evidence/margin-top-vs-runnerup.json`).

**A (absolute floor) — empty interval again, confirmed empirically.** Swept
`min_confidence` over the full 57-question eval set, setting the config and
observing real declines rather than assuming the comparison:

| floor | unanswerable declined | answerable false-declined |
|---|---|---|
| 0.0 (shipped) | 0/4 | 0/53 |
| 0.095 – 0.103 | 3/4 | **0/53** |
| **0.121** | **4/4** | 1/53 (zero-overlap) |
| 0.125+ | 4/4 | 2/53 |

Declining all four needs **≥ 0.121**; zero false-declines holds only to
**≤ 0.103**. Empty — structurally identical to acme's ≥0.25-vs-≤0.087.

**B (runner-up margin) — empty AND inverted.** The hypothesis was that a real
answer has a clear winner (large margin) and an unanswerable question does not.
The data points the other way:

| class | margin (top − runner-up) |
|---|---|
| unanswerable (n=4) | 0.00052 – 0.00411 |
| smallest answerable | **1e-05**, 1e-05, 7e-05, 0.00025, 0.00025 |

- Every unanswerable margin **exceeds** the six smallest answerable margins.
- A threshold declining the fabrications would first kill a `factual` and a
  `how-to` question — not merely the anticipated `cross-doc` false positives.
- **The two defects are coupled:** the smallest answerable margins come from a
  document tying with its own superseded twin. Supersession inversions are
  *manufacturing* the margin check's false-positive mode.
- The ratio variant fails identically (max unanswerable 1.0928 vs min answerable
  1.000206).

### Verdict: a documented product boundary, not an open defect

Both no-model discriminators are now refuted on two independent corpora in
unrelated domains. **Extractive answering without a model cannot separate "the
corpus answers this" from "the corpus contains topically-adjacent sentences."**

- The shipped permissive default (`0.0`) is **re-confirmed as the only value that
  false-declines nothing** — the v0.25.0 decision holds on a second corpus.
- Recommended: keep the default, expose the measured floor curve as an opt-in
  knob with its false-decline cost stated, and **write this down as a product
  limit** rather than carrying it as a defect awaiting a fix.
- A model in the answer path would be the only mechanism left, and the
  constitution forbids it on the maintenance path. That is a deliberate,
  documented trade.

**No further no-model mechanism is proposed.** This line of investigation is
closed unless a materially different discriminator is invented.

### The de-confounded re-measurement — 2026-07-24, v0.26.0

The refutation above carried one caveat that had to be discharged before it could
be called final: **the smallest "answerable" margins came from documents tying
with their own superseded twins**, so Finding 1 was manufacturing this check's
false-positive mode. Phase 7's down-rank penalty removed those ties, and the
margin was re-measured on both corpora at penalty 15
([`../conformance/2026-07-24-supersession-penalty-calibration/ANALYSIS.md`](../conformance/2026-07-24-supersession-penalty-calibration/ANALYSIS.md) §M4).

**The confound was real. It was not the cause.**

| orbit — smallest answerable margins | penalty 0 | penalty 15 |
|---|---|---|
| 1st | 1e-05 `factual` | 1e-05 `stale-vs-current` |
| 2nd | **1e-05 `how-to`** | **1e-05 `how-to`** (unmoved) |
| 3rd | 7e-05 `zero-overlap` | 7e-05 `zero-overlap` |

- The previously-minimal `factual` question **did** improve — de-confounding
  worked.
- **A `how-to` question sits at 1e-05 before and after.** Two documents genuinely
  agree; no supersession involved.
- **acme is identical before and after**, its minimum held by a `cross-doc`
  question — supersession was never implicated there at all.
- Unanswerable margins are unchanged in both (0.00052 – 0.00411).
- `max(unanswerable) = 0.00411` still exceeds `min(answerable) = 1e-05` by two
  orders of magnitude.

**The residual false-positive mode is exactly the one this document predicted
before anything was measured** — *"when several documents genuinely agree on an
answer, their scores are legitimately close. A margin check declines precisely
there."* acme's minimum being `cross-doc` is that sentence, measured.

### Final verdict: closed as a product boundary

**B is refuted on its own merits, not as an artifact of the staleness defect.**
The caveat is discharged; there is nothing left to re-measure. Three no-model
discriminators — absolute floor, runner-up margin, margin ratio — are empty
across two independent corpora, one de-confounded.

- The permissive default (`0.0`) stands, now on three measurements.
- **The reopen-trigger above is retired.** It fired, B was measured, B failed.
  Re-opening requires a *materially different* discriminator — not another
  threshold over the same scores.
- This belongs in the docs as a **stated limit of extractive answering without a
  model**, not as an open defect awaiting a fix.

## References

- Measured: [`../conformance/2026-07-22-acme-payments/report.md`](../conformance/2026-07-22-acme-payments/report.md) §Finding 3.
- Margin refuted: [`../conformance/2026-07-24-orbit-fulfillment/ANALYSIS.md`](../conformance/2026-07-24-orbit-fulfillment/ANALYSIS.md) §Finding 2.
- The 0.23–0.26 dense noise band and the retained zero-candidate early return:
  [`../adr/0010-fuxvec-binary-dense-search.md`](../adr/0010-fuxvec-binary-dense-search.md).
- On abstention being preferable to a confident wrong answer in retrieval QA:
  Rajpurkar et al., *Know What You Don't Know: Unanswerable Questions for SQuAD*
  (ACL 2018) — establishes unanswerable-question handling as a first-class
  metric rather than an edge case.
