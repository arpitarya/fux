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

## References

- Measured: [`../conformance/2026-07-22-acme-payments/report.md`](../conformance/2026-07-22-acme-payments/report.md) §Finding 3.
- The 0.23–0.26 dense noise band and the retained zero-candidate early return:
  [`../adr/0010-fuxvec-binary-dense-search.md`](../adr/0010-fuxvec-binary-dense-search.md).
- On abstention being preferable to a confident wrong answer in retrieval QA:
  Rajpurkar et al., *Know What You Don't Know: Unanswerable Questions for SQuAD*
  (ACL 2018) — establishes unanswerable-question handling as a first-class
  metric rather than an edge case.
