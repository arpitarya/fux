---
type: Report
name: 2026-08-25-rank-flip-susceptibility
classification: informed
description: "How large must a score perturbation be to change a fux ranking? At the 1.907e-06 the cross-arch run measured, ZERO flips in 297 queries x 50 trials, in both arms — no adjacent top-5 pair anywhere in the sample is even within 2x it. The knee is at ~1e-4, 52x higher. Separately: 4.38 % of queries already contain an EXACT top-5 tie, so fux's own tie-breaking is a larger source of arbitrary ordering than the drift would be."
timestamp: 2026-08-25T00:00:00Z
---

# Rank-flip susceptibility — what it takes to actually change a ranking

**A characterisation, not a gate.** No prediction was pre-registered and nothing
is adjudicated here. The method was written before any number existed:
[`evidence/METHOD.md`](evidence/METHOD.md).

## Authorship

**Classification: `informed`** (ADR-RS decisions 11 and 13).

| artifact | author | evaluation material reachable |
|---|---|---|
| the question, the method, the harness, the analysis | this session | everything |
| the query set | generated from the corpus's own vocabulary, seeded `20260825` | n/a — no goldens exist for this corpus |

**No blind option existed and none is claimed.** The same session proposed the
measurement, wrote it, and read it. ⚠ Same decision-12 scope conflict as
[the model-removal run](../2026-08-25-model-removal/report.md): this states
deltas and there is no evaluation set to be contaminated by. Disclosed, not
resolved — [W-81](../../open/W-81-the-sealed-set-and-the-two-controls.md) §3.

## Why this ran

[ADR-RERANK](../../../docs/adr/0041_rerank.md) veto 1 condition 2 refuses the
cross-encoder on cross-architecture float drift, citing
[the cross-arch run](../2026-08-24-crossarch-drift-and-declared-supersession/report.md):
**82.9 % of elements differ, max |Δ| = 1.907e-06**, read against `rank()`'s
`round(score, 9)` as *"roughly two thousand times the rounding"*.

**That is element drift. A ranking only changes when drift exceeds the gap
between two adjacent documents' scores.** Nobody had measured that gap.

## Method

Corpus: this repository as committed, **495 indexed local documents**. Queries:
**297** usable, drawn from the corpus's own vocabulary (mid-frequency terms,
1–3 terms per query) — the method `2026-08-23-fork3-per-field-bound` used.
Perturbation applied independently per document, uniform in `[−δ, +δ]`,
**50 trials per query per δ**, swept over twelve decades.

Two arms, because they are different score geometries: **A** BM25F alone (the
shipped default), **B** BM25F + the proximity reranker at `rerank_weight = 1.0`.

**Exact ties are separated out and reported apart.** A query whose top-5
contains two identical scores flips under *any* nonzero perturbation, including
`1e-12`, because the tie is broken by document index. Folding those in produces
a flat 6.4 % floor across seven decades that hides the actual signal — the first
run of this harness did exactly that, and the flatness is what exposed it.

## Result — the curve

`order-flip` = the top-5 came back in a different order. `member` = a document
entered or left the top-5.

| δ | A at-risk | A order | A member | B at-risk | B order | B member |
|---|---|---|---|---|---|---|
| **1e-12 → 5e-05** | **0.00 %** | **0.00 %** | **0.00 %** | **0.00 %** | **0.00 %** | **0.00 %** |
| 1e-04 | 0.35 % | 0.35 % | 0.00 % | 0.35 % | 0.35 % | 0.00 % |
| 5e-04 | 2.46 % | 2.11 % | 0.35 % | 1.77 % | 1.41 % | 0.00 % |
| 1e-03 | 3.52 % | 2.82 % | 0.70 % | 2.12 % | 2.12 % | 0.00 % |
| 5e-03 | 17.25 % | 14.79 % | 3.52 % | 15.90 % | 14.13 % | 3.18 % |
| 1e-02 | 29.93 % | 26.76 % | 8.10 % | 26.15 % | 23.32 % | 6.01 % |
| 1e-01 | 87.32 % | 84.51 % | 45.42 % | 82.33 % | 77.39 % | 40.28 % |

## The findings

**1 — At the drift the veto quotes, nothing moves.** `1.907e-06` sits inside the
zero band. Not merely *no flips observed* — **`at-risk` is also 0.00 %**, and
at-risk is a deterministic property of the sample, not a Monte Carlo outcome:
**no adjacent top-5 pair in 297 queries is within 2 × 1.907e-06 of another.**
The median adjacent gap is **0.27**, five orders of magnitude above the drift.

⚠ **Stated as a zero should be stated.** 0 events in 297 queries puts the
95 % upper bound at roughly **1 % of queries** (rule of three). "Zero" here
means "below what 297 queries can resolve", not "impossible".

**2 — The knee is at ~1e-4, about 52x the measured drift**, and meaningful
damage needs **1e-2**, about **5 200x** it.

**3 — And the bigger source of arbitrary ordering is fux's own.**
**4.38 % of queries (13 of 297) contain an EXACT tie inside the top-5** — 16
tied adjacent pairs. Those orderings are decided by **document index position,
not by relevance**. They are deterministic, so they break no law and threaten no
cross-machine agreement; they are simply arbitrary. **Fux's tie-breaking
introduces more ranking arbitrariness than the cross-ISA drift would**, by a
margin of 4.38 % against a measured 0 %.

**4 — The reranker slightly REDUCES susceptibility.** Arm B is at or below arm A
at every δ (e.g. 23.32 % vs 26.76 % at 1e-2). Proximity uplift spreads adjacent
scores apart rather than compressing them.

## What this does NOT establish, and it is the important half

**This is a LOWER BOUND on a cross-encoder's flip rate, not an estimate.**

- **The score-level drift is unknown.** `1.907e-06` is one element of an
  intermediate tensor after **one** encoder block. A six-layer model compounds;
  a final scalar may average. **Nobody has measured the drift on a score.** If
  it reached `1e-3`, this curve says ~2.8 % of queries flip; at `1e-2`, ~27 %.
- **A cross-encoder's score geometry is probably tighter than BM25F's.** It
  reranks ~20 already-similar documents, which is exactly the regime that
  produces near-ties. Its own adjacent gaps could be far smaller than the 0.27
  median here, and the flip rate correspondingly higher **at the same δ**.
- **One corpus, one query distribution, no goldens.** 495 documents of this
  project's own prose. Nothing here says what happens at the 10 000-document
  design point.

**So the honest conclusion is narrow:** *the number the veto quotes, taken at
face value against this scorer on this corpus, changes no rankings.* The number
that would settle the question is the **score-level** drift of an actual
reranker, and it has never been measured.

## Reproduce

```bash
cd work/regression/2026-08-25-rank-flip-susceptibility
python evidence/flip_rate.py     # needs a built index; writes evidence/results.json
```
