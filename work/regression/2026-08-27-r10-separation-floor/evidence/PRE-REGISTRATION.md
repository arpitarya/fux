---
type: PreRegistration
name: PRE-REG-R10-SEPARATION-FLOOR
description: "Frozen before any number existed. What separation value is the grounded/weak boundary, and what may that number honestly be called — given that `separation` is ordinal and Chow's rule assumes a probability."
timestamp: 2026-08-27T00:00:00Z
---

# R10 — the separation floor. Frozen before the run.

**Ruled by Arpit, 2026-08-27 (Cowork):** *measure the curve, then declare it a
heuristic.* This document is the half that must exist first;
[ADR-RS](../../../docs/adr/0036_predictions.md) is why.

## ⚠ The gap this run does NOT close, stated before any number

[ADR-CONFIDENCE](../../../docs/adr/0045_confidence.md) decision 6 binds
`SEPARATION_FLOOR` to [ADR-QUALITY](../../../docs/adr/0044_quality-contract.md)'s
confidence target `t = 0.75`, by Chow's rule.

**Chow's rule assumes a calibrated probability. `separation` is not one.** It is
`(top1 - top2) / top1` — an **ordinal** signal: higher means *more separated*,
and nothing more. There is no sense in which `separation = 0.30` means *30 %*
of anything.

**So the number this run produces is an EMPIRICAL THRESHOLD, not a calibrated
one.** Chow's rule *motivates* where to look; it does not license calling the
result a probability. **Any report from this run that describes the floor as
"calibrated" is wrong**, and the wording is fixed here so a later session cannot
quietly upgrade it.

⚠ **Calibration was considered and refused for this run.** Fitting isotonic or
Platt on 50 queries would produce a mapping that *looks* principled and is fit
to noise — **worse than an honest heuristic, because it hides its own
uncertainty**. If a calibration is ever fitted it needs its own pre-registration
and a sample that supports it.

## Common conditions

- Corpus: **`fux-playground`**, the committed 50 goldens, unmodified.
- ⚠ **`fux-playground` is NOT on the build machine.** This run cannot start
  until it exists — it is W-87 P1's blocker, and this run inherits it.
- **Every arm runs UNENRICHED** (`.fux/enrich` absent) and with
  `.fux/tune.toml` at defaults, so the only variable is the threshold being
  read off the data.
- `fux ingest --full && fux build` once; **the run reads one index.** No arm
  changes a byte of it — this measures a boundary over fixed output, so
  re-ingesting per arm would add variance with no possible gain.
- **Classification: `informed`.** Whoever runs this will have read this
  document and the goldens. There is no blind option and none is pretended;
  ADR-RS decision 11 labels it, and decision 12 permits reporting the
  *distribution* because it is not a delta between arms.

## The measurement

For each of the 50 goldens, record `(separation, correct)` where **`correct`**
means the golden's target document appears at rank ≤ its `max_rank`. Bin by
`separation` and plot observed `P(correct)` per bin.

**The floor is the lowest `separation` at which observed `P(correct)` reaches
`t = 0.75` and stays at or above it for every higher bin.**

⚠ **"and stays above" is load-bearing.** A single bin crossing 0.75 and falling
back is noise on 50 queries, and picking that crossing would be fitting the
threshold to a wobble.

## Frozen verdict rules

| outcome | what it means | what ships |
|---|---|---|
| **A crossing exists and is monotone above it** | the signal orders correctness | `SEPARATION_FLOOR` moves to that value, **described as an empirical threshold on an ordinal signal** |
| **No bin reaches 0.75** | the signal cannot support `t` at all | the floor **stays 0.10 and is declared a heuristic outright**; decision 6's binding is reported as unachievable and reopens |
| **Every bin exceeds 0.75, including the lowest** | `weak` is unreachable on this corpus | **no change**, and the report says the corpus was too easy to locate a boundary — not that the floor is right |
| **Crossing exists but is non-monotone** | too noisy to read | **no change.** Report the curve; do not pick a value from it |

⚠ **Three of the four outcomes change nothing.** That is deliberate: the run
exists to find out whether a number is *findable*, and the most likely honest
answer on 50 queries is *not yet*.

## The bins, fixed now

`separation` is clamped to `[0.0, 1.0]`. **Ten equal bins of 0.1.**

⚠ **Fixed before seeing the data, because bin choice is the easiest way to
manufacture a crossing** — the same freedom `p`-hacking exploits. Any report
that re-bins must say so and may not compare its number to this one.

⚠ **`separation == 1.0` is a documented special case**: exactly one document
scored, so nothing competes with it. It lands in the top bin and **must be
reported separately as well**, because it is a structural fact rather than a
measurement of ordering.

## Power, stated rather than assumed

**50 queries across 10 bins is ~5 per bin.** A bin's observed rate has a 95 %
interval roughly ±0.4 wide at that size. **This run cannot resolve a boundary to
better than about ±0.2 in `separation`**, and the report must publish per-bin
counts beside every rate so a reader can see the interval rather than trust the
point.

**That is the honest reason three outcomes change nothing.**

## What this run cannot establish

Fifty queries, ten documents, one corpus — three orders of magnitude below
[CLAUDE.md](../../../CLAUDE.md) §Litmus's 10 000-document design point. **Nothing
here generalises**, and a floor read off this corpus is a starting value with
evidence, not a validated one. `CLAUDE.md` §Conformance runs' *"never ship a
ranking/behaviour change off a single corpus"* applies: **a crossing yields a
recommendation plus the named blocker, not a shipped constant.**

⚠ `tests/query/test_confidence.py` asserts the **rule** relative to
`SEPARATION_FLOOR` and never its value, so whatever this run concludes lands
without editing a test — which is what stops the test from being quietly
rewritten to fit the number.
