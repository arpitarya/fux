---
type: Analysis
title: Corpus-wide coverage lets a scattered query look fully covered
description: One decoy reaches `grounded` because every term occurs somewhere, in four different documents. The fix is per-document coverage, which is a design change to an accepted record and is named rather than taken.
timestamp: 2026-08-27T17:45:00Z
---

# Analysis — the decoy control's first run

## 1 · The defect, stated precisely

**`coverage` and `missing` are corpus-wide.** A query whose terms are
**scattered across different documents** therefore reports `coverage: 1.0` and
`missing: []` — the same values a query fully answered by one document produces.

Both fact-based band clauses are then satisfied, and the band falls through to
`separation`, which measures *"can the ranking tell first place from second?"* —
a question about **ordering**, not about **whether anything answers**. A corpus
that does not discuss a topic still produces a clear winner among near-misses.

**Repro:** `evidence/validate.py evidence/decoys.jsonl`, row `d02`.

## 2 · Why raising the separation floor does not help

`d02`'s separation is **0.5808**, above the **0.5** R10's selection rule would
have picked. **Whichever way R10 is ruled, this case survives it**, and that is
worth knowing before ruling R10 rather than after.

⚠ **It also argues that `separation` is being asked the wrong question.** It
answers *"is first place clearly first?"* A corpus with one document
tangentially matching and nine matching less answers that **very clearly** while
answering the user's question not at all. **Separation measures decisiveness,
not groundedness**, and no threshold on it closes the gap the module's own
docstring opens with.

## 3 · The shape of a fix, and why it is not taken here

**Per-document coverage**: compute coverage against the *cited* document rather
than the corpus, or carry both. `d02` would then report that no single document
contains `sla`, `publish`, `payments` and `api` together, and the band would
correctly not be `grounded`.

⚠ **Not taken.** [ADR-CONFIDENCE](../../../docs/adr/0045_confidence.md) is
**accepted** and `coverage` is one of its four declared signals with a declared
shape; changing what it measures changes `output.schema.json`, the MCP result
and every consumer reading the block. **That is a decision, not a defect fix**,
and `CLAUDE.md` is explicit that choosing a plausible default and continuing is
how work lands on the wrong side of a call nobody made.

⚠ **And no test was added pinning the current behaviour as correct.** Pinning a
defect is how it becomes the contract — the failure this repo has already
recorded twice in tests that "passed" while proving nothing.

## 4 · What the run does NOT say

- **Not that the confidence plane is broken.** Fourteen of fifteen behaved
  correctly and named their absent terms in `missing`. The plane works; one
  band boundary has a hole.
- **Not a rate.** One in fifteen on a hand-authored set is not a measured
  false-`grounded` rate, and it is not a delta. A rate would need a
  pre-registration, a larger decoy set, and a corpus that is not ten documents.
- **Not generalisable.** Ten documents is three orders of magnitude below the
  design point, and scattering is *more* likely in a small corpus, where few
  documents must carry every term.

## 5 · Unresolved

- **Whether coverage becomes per-document.** Arpit's; see §3.
- **The placebo arm has not been RUN**, only built. Running it means grading the
  playground three ways — real enrichment, placebo, none — and comparing, which
  is a **delta between arms** and therefore needs the blind/informed question
  answered before it produces a number anyone may cite.
- **The sealed subset is still not built**, so ADR-RS decision 15 keeps its
  `NOT BUILT` marker.
