---
type: Verdict
name: R9-T2-AT-10K
title: "R9 — the T1 accelerator at the 10 000-document design point, against R3's 150 ms bar"
description: "PASS. Worst-case warm p95 is 12.46 ms against a 150 ms bar, 12x inside it. T2 is not built; ADR-T2-SEGMENTS records the decision not to. Caveat declared before the run: the corpus is synthetic and 18x lighter per document than R3's."
status: final
verdict: PASS
prediction: R9
pre_registration: tools/t2-eval/PRE-REGISTRATION.md
timestamp: 2026-08-22T00:00:00Z
---

# R9-T2-AT-10K — **PASS**

- **Prediction:** **R9** — *at the 10 000-document design point, does the T1
  accelerator answer inside R3's bar, or is a T2 tier needed?*
- **Bar:** **warm `ask` ≤ 150 ms including worst-case terms** — R3's own
  pre-registered bar, reused unchanged at a new corpus size.
- **Pre-registration:**
  [`tools/t2-eval/PRE-REGISTRATION.md`](../../../tools/t2-eval/PRE-REGISTRATION.md),
  written before the harness ran.
- **Item:** [W-26](../../open/W-26-m6-scale-t2.md) · **Closes with:**
  [ADR-T2-SEGMENTS](../../../docs/adr/0037_t2-segments.md)
- **Engine:** `9bb870e+dirty` · Python 3.14.2 · Darwin 25.3.0 arm64
- **Evidence:** [`evidence/report-10000.json`](evidence/report-10000.json) ·
  [`evidence/report-1000.json`](evidence/report-1000.json)

## The verdict

**PASS.** Worst-case warm p95 at the judged size is **12.46 ms** against a
**150 ms** bar — **12× inside it**.

| corpus | population | accel p95 | scan p95 (unjudged) |
|---|---|---|---|
| **10 000 — judged** | **worst (highest df)** | **12.46 ms** | 25.07 ms |
| 10 000 | typical | 12.54 ms | 26.01 ms |
| 10 000 | multi-term | 12.63 ms | 37.06 ms |
| 1 000 — population curve | worst | 1.25 ms | 6.20 ms |
| 1 000 | typical | 1.28 ms | 6.23 ms |
| 1 000 | multi-term | 1.30 ms | 7.30 ms |

**Consequence, per the pre-registered rule: T2 is not built.**
[ADR-T2-SEGMENTS](../../../docs/adr/0037_t2-segments.md) is written as the
record of a decision *not* to build, naming this measurement and the size it
was taken at.

## The caveat that matters, and the check that partly answers it

**The corpus is synthetic and much lighter than the one R3's bar was
calibrated on.** This was declared in the pre-registration's §5 as *"the
limitation most likely to matter"*, before the run:

| | R3 (real RFCs, 2026-08-12) | R9 (synthetic, this run) |
|---|---|---|
| documents | 8 870 | 10 000 |
| committed index | 230 MB | 14.2 MB |
| **bytes/document** | **25 930** | **1 420** |
| distinct terms | 419 627 | 11 316 |

**18× lighter per document, 37× fewer distinct terms.** The generator uses a
closed vocabulary by design, so this is a property of the instrument, not an
accident.

**Post-hoc validity check — labelled post-hoc, and it is not part of the
verdict.** The gap matters less than those ratios suggest, because the judged
quantity is not bytes-bound:

- **The scan is bytes-bound and shows the full gap**: 25.07 ms here against
  R3's 4 248.8 ms. The scan reads every byte of every shard, so an 18×
  lighter corpus is ~170× cheaper to scan. The scan is **unjudged**.
- **The accelerator is posting-list bound**, i.e. it tracks *document count*
  through `df`, not document size. The population curve confirms it directly:
  1 000 → 1.25 ms and 10 000 → 12.46 ms is **linear in corpus size**.
- **Cross-checked against R3 at comparable size**: 12.46 ms per 10 000
  synthetic documents vs 27.2 ms per 8 870 real ones — real prose costs about
  **2.5× more per document**, not 18×. Correcting this run for that gives
  ~31 ms, within 15 % of R3's measured 27.2 ms.

**What that does and does not license.** It is a consistency argument that the
instrument is not wildly mis-measuring, and it makes a 12× margin unlikely to
be an artefact of corpus lightness. **It is not a measurement on a real
10 000-document corpus, and no such corpus exists** — the one R3 used was lost
with the lab (W-56). That gap is real and is recorded as owed in
[`ANALYSIS.md`](ANALYSIS.md).

## What this run does not rule

- **Not R7.** Index size was recorded (14.2 MB raw / 2.3 MB packed at 10 000
  documents) purely as characterisation for the paper's §5 rewrite. **No budget
  was applied and none may be derived from it** — R7's re-derivation is Arpit's
  call, and a budget chosen after reading this number would be contaminated by
  it. Filed as a blocker rather than guessed.
- **Not 50 000 or 100 000.** A PASS here rules on the design point. The curve
  extrapolates linearly to ~62 ms at 50 000 and ~125 ms at 100 000, both
  nominally inside the bar — **that is arithmetic on a light synthetic corpus,
  not a verdict**, and re-asking at 50 000 is a new pre-registration.
- **Not tier-auto.** The `[index] tier = t0|t1|t2|auto` knob that *"flips by
  measurement, never by hand"* **does not exist in the code**. Nothing was
  flipped because there is nothing to flip.
- **Not portable milliseconds.** Run on the device, not in the cloud — the same
  deviation R3 declared, for the same reason.
