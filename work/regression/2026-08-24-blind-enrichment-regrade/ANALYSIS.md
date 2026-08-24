---
type: Analysis
name: 2026-08-24-blind-enrichment-regrade-analysis
description: "What the blind re-grade means: the premise behind deferring the cross-encoder was measured on a contaminated number, and the comparison it rests on inverts when the contamination is removed. Not adjudicated."
timestamp: 2026-08-24T00:00:00Z
---

# Analysis — the blind enrichment re-grade

## 1 · The claim this touches, quoted before it is questioned

W-76 Phase 6 refused the specified cross-encoder and deferred it *with a stated
price rather than rejecting it*. The price was this sentence, which appears in
[`IMPLEMENTATION.md`](../../IMPLEMENTATION.md), in
[ADR-RERANK](../../../docs/adr/0041_rerank.md), and in the previous run:

> of 18 surviving failures, **18 are vocabulary gaps and 0 are ordering
> failures**, so **enrichment is worth 10 where reranking is worth 4**

**That comparison is between a clean number and a contaminated one**, and
nobody noticed at the time because both were produced in the same session.

- **reranking's +4** was measured with no knowledge of the goldens in the
  mechanism — it is arithmetic over passages, and the author of the arithmetic
  could not target a query even in principle.
- **enrichment's +10** came from text written by an author who had already read
  the failing queries.

## 2 · What the blind arm does to it

| | reranking | enrichment (contaminated) | enrichment (blind) |
|---|---|---|---|
| net | **+4** | +9 to +10 | **+1** |
| broke | **0** | 0 | **2** |

**The ordering inverts.** Blind enrichment is worth a quarter of reranking and
is the only one of the three interventions that **breaks** a query that
previously passed.

**This does not make the earlier run wrong.** It disclosed its own
contamination in §1 of its analysis, on the day, unprompted. What it could not
do is say how large the effect was. It is 8 of 9 points.

## 3 · Why zero-broken is the diagnostic, not the score

The number worth carrying out of this run is not `33` or `41`. It is that the
contaminated arm **broke nothing**.

Enrichment attaches new vocabulary to a document. On a 10-document corpus, new
vocabulary on nine documents is a large perturbation of the term statistics —
`df` moves, `avg_wlen` moves, and documents that were second become first.
The blind arm shows what that perturbation costs when it is not aimed: **two
queries regressed**.

An intervention that adds vocabulary to nine of ten documents and disturbs
**not one** of the fifty rankings has been fitted to the evaluation. That is a
structural argument, not a statistical one, and it does not need N to be large.

**The generalisation, which outlives this corpus:** *an intervention whose
error profile is implausibly clean should be suspected of having seen the test,
before it is believed.* Fux's own goldens discipline already says there is no
`--update-goldens` flag because a golden regenerated from engine output is a
screenshot with a test attached. **This is the same failure entering through
the other door** — not the goldens fitted to the engine, but the corpus
metadata fitted to the goldens.

## 4 · Specific improvements

**4.1 — A second blind author, to separate craft from contamination.**
The one thing this run cannot do is tell an 8-point contamination effect from
an 8-point difference in writing quality. One more blind author settles it: if
the second lands near `33`, contamination is the explanation; if it lands near
`40`, the first blind author was simply worse at the task.

*Repro:* re-run the protocol in the report with a fresh agent, same
prohibitions, and diff the two enrichments.

**4.2 — The enrichment gate needs a blind-authorship rule, written down.**
[ADR-ENRICH](../../../docs/adr/0040_enrich.md) governs how enrichment is
generated and pinned and says nothing about who may have seen the evaluation.
`fux enrich` cannot enforce this — the model is the author, and fux never calls
one — so it is a **measurement-protocol rule** and belongs with
[ADR-RS](../../../docs/adr/0036_predictions.md), beside the
threshold-never-moves rule it is a sibling of.

*Repro:* none; this is a rule to ratify, not a number to produce.

**4.3 — Unresolved, and stated as unresolved: is `+1` enrichment's real value,
or this corpus's?** Ten documents is small enough that the vocabulary a
searcher would plausibly use is largely already present. A larger corpus is
where enrichment should pay, and **the design point is 10 000 documents** —
which this corpus is three orders of magnitude below. Nothing here licenses a
claim about enrichment at the design point, in either direction.

*Repro:* the same three arms against a fux-lab environment at 10 000
documents, which needs a golden set that does not exist.

## 5 · What is NOT concluded here

**The cross-encoder deferral is not reopened by this document.** It was a
ruling made on a comparison, the comparison has changed, and **whether that is
enough to reopen it is Arpit's decision** — ADR-RERANK's own veto conditions
are the place it would be argued, and a session that reopened it unilaterally
would be adjudicating a fork it was handed.

Filed as: the premise moved; the ruling stands until someone rules again.
