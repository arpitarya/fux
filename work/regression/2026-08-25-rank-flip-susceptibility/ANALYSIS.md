---
type: Analysis
name: 2026-08-25-rank-flip-susceptibility-analysis
description: "What the curve does to ADR-RERANK veto 1 condition 2: the quoted drift changes no rankings, but it was never the right quantity, and the right one is still unmeasured. Plus a finding nobody asked for — 4.38 % of top-5 orderings are already decided by document index rather than relevance."
timestamp: 2026-08-25T00:00:00Z
---

# Analysis — rank-flip susceptibility

## 1 · What this does to the veto, precisely

Veto 1 condition 2 is **not refuted**, and it is **not confirmed**. It is shown
to rest on a quantity that does not answer it.

| the veto says | this run says |
|---|---|
| max element drift `1.907e-06` is *"~2000x the rounding"* | true, and **the rounding was never the binding constraint** — the binding constraint is the gap to the next document, whose median is `0.27`, five orders of magnitude larger |
| therefore two developers would see different orderings | **at that magnitude, on this corpus: no.** 0 of 297 queries, and no pair even within 2δ |

**The argument that survives is different and narrower:** *a reranker's
score-level drift is unknown, and if it exceeds ~1e-4 it begins to reorder
results.* That is a real objection. It is also a **measurable** one, which the
current wording is not.

⚠ **This does not license building a cross-encoder**, and nothing here touches
condition 1 or the value question. What it licenses is **restating condition 2
in terms of the quantity that decides it.**

## 2 · The finding nobody asked for — and it may matter more

**4.38 % of queries have an exact tie inside the top-5.** Those orderings are
decided by `docidx`, which is stable, deterministic, and **has nothing to do
with relevance**.

Set the two side by side:

| source of arbitrary top-5 ordering | rate |
|---|---|
| cross-ISA float drift at the measured magnitude | **0.00 %** |
| **fux's own tie-breaking** | **4.38 %** |

The project has spent a filed measurement, a veto condition and a standing
refusal on the first. The second was discovered by accident, in a harness
written to study the first, **because the flat 6.4 % floor across seven decades
was too flat to be real.**

**Neither is a determinism bug.** Ties break identically on every machine. But
"the same arbitrary answer everywhere" is exactly the thing worth noticing when
the objective is *the right answer*, not *the same answer*.

**2.1 — What to do about it, stated as options rather than a decision.**
Nothing here rules on this; it is a fork, and a small one.

- **Leave it.** 4.38 % of queries have two documents fux genuinely cannot
  separate. Index order is as good as anything and costs nothing.
- **Break ties on a declared signal** — recency, or `superseded`, or path
  priority. Turns an arbitrary choice into a stated one, and every input is
  already in the record.
- **Surface it.** A tie is information: *"these two are indistinguishable to
  the scorer."* Today the caller cannot tell a decisive 1st place from a
  coin-flip.

*Repro:* `evidence/flip_rate.py` prints the tied-query count per arm.

## 3 · Specific improvements

**3.1 — Restate condition 2 in the quantity that decides it.** The bar should
not be *"drift below 5e-10"* (derived from the rounding, which is not binding).
It should be **score-level drift below the corpus's adjacent-gap floor**, and
this run supplies the floor for one corpus: nothing happens below `~5e-5`.
*Repro:* the curve.

**3.2 — Measure the score-level drift, which is the actual open question.**
Run *any* small ONNX reranker on two architectures and diff the **final
scores**, not an intermediate tensor. That is the same shape of experiment the
cross-arch run already did, one layer of abstraction up, and it would settle
condition 2 on its own terms. ⚠ **It is also a prerequisite for reading this
curve usefully** — without it, this measures susceptibility to a perturbation
of unknown size.

**3.3 — Re-run at the design point before quoting the zero widely.** 495
documents of one project's prose. Adjacent gaps shrink as a corpus grows and
more documents compete; the zero band could narrow at 10 000.

## 4 · Unresolved, and stated as unresolved

**Whether a cross-encoder's own score geometry is tighter than BM25F's.** The
report calls this the reason the result is a lower bound. It is an argument
from how rerankers work, **not a measurement**, and it would be settled by the
same experiment as 3.2.
