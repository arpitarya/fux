# Method — written before any number existed

**Not a gate.** No prediction is pre-registered and nothing is adjudicated. This
is a **susceptibility characterisation**, filed because ADR-RERANK's veto 1
condition 2 quotes a drift figure at a level of abstraction that does not
answer the question the veto turns on.

## The question

The cross-arch run measured **82.9 % of elements differ, max |Δ| = 1.907e-06**
in an intermediate tensor after **one** encoder block. The veto reads that
against `rank()`'s `round(score, 9)` and concludes ~2000x the rounding.

**That is element drift, not ranking drift.** A ranking only changes when the
drift exceeds the gap between two adjacent documents' final scores. Nobody has
measured that gap.

## What CANNOT be measured, stated first

**There is no cross-encoder in fux, so its flip rate cannot be measured.** Two
things are unknown and are not guessed at here:

1. **The score-level drift.** The 1.907e-06 is one element of an intermediate
   tensor after one block. A final scalar could be smaller (averaging) or
   larger (six layers compounding). **Unknown.**
2. **A cross-encoder's score geometry.** It reranks ~20 already-similar
   documents, which plausibly produces *more tightly clustered* scores than
   BM25F over a whole corpus — which would make flips **more** likely.

**Therefore this run produces a CURVE, not a verdict**: flip rate as a function
of perturbation magnitude. Whoever later measures the true score-level drift
reads their answer off it.

⚠ **Read as a LOWER BOUND on a cross-encoder's flip rate**, for reason 2.

## What IS measured

Corpus: this repository, as committed. Queries drawn from the corpus's own
vocabulary — the method used by `2026-08-23-fork3-per-field-bound`.

Two score distributions, because they are different geometries:

- **A — BM25F alone.** The shipped default path.
- **B — BM25F + the proximity reranker** (`rerank_weight = 1.0`). A real
  reranker's output over top-20 on this corpus; the closest available analogue
  to "what a reranker's scores look like here".

Three metrics per perturbation magnitude δ:

| metric | definition |
|---|---|
| **at-risk** | fraction of queries where *any* adjacent top-5 pair is separated by ≤ 2δ. **An upper bound** on the flip probability — a pair further apart than 2δ cannot swap |
| **order flip** | top-5 ids returned in a different ORDER, under a random perturbation of each score, uniform in [−δ, +δ] |
| **membership flip** | the SET of top-5 ids changes — a document enters or leaves. Strictly worse than a swap, and counted separately |

δ swept over `1e-12 … 1e-1`, twelve decades, so the curve does not depend on
picking the "right" δ in advance.

Monte Carlo: **50 independent perturbations per query per δ**; the reported rate
is over query-trials. Perturbation is applied to the final score, independently
per document, which is the pessimistic assumption (correlated drift flips less).

## Reproduce

`python evidence/flip_rate.py` from the run directory, against a built index.
