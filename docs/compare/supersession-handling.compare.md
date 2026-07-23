---
type: Compare Doc
title: Supersession Handling
description: How Fux should treat a document its author marked superseded — annotate and let answer prefer the current doc, versus down-ranking superseded chunks in fusion. Proposed verdict is annotate-first; the fusion penalty stays deferred.
status: accepted
timestamp: 2026-07-23T00:00:00Z
tags: [retrieval, staleness, ranking]
---

# Supersession Handling — Comparison

> **Verdict (accepted 2026-07-23, Arpit):** **Parse supersession at ingest;
> annotate it in output; make `answer` prefer the current document. Do NOT add
> a fusion down-rank penalty yet.**
> **Status:** ✅ Accepted · **Confidence:** High on the
> split, Medium on whether annotation alone moves the user-visible number.
> **Honest caveat:** annotation does not change `find` ordering, so an agent
> that reads only the top result *and ignores the annotation* still gets the
> stale document. That residual is real, stated, and measurable.

## Context

The acme-payments run measured the product's core promise and found it failing:

- The **superseded** document outranked the still-true one in **9 of 12** pairs —
  usually stale at rank 1, current at rank 2.
- **All three supersession markers fail identically:** `superseded_by:`
  frontmatter, a dated inline "*Superseded 2026-03*" note, and no marker at all.
- Cause: BM25F length normalization favors the terser legacy document, and the
  dense plane cannot break a tie between topically near-identical docs. The
  fused margin is razor-thin (settlement: 0.04892 vs 0.04813, Δ 0.00079).

Nothing in the pipeline **knows** one document supersedes another. The markers
are plain text it counts, not a signal it acts on.

evidence: `../conformance/2026-07-22-acme-payments/evidence/staleness-inversions.json`
· proposal: [`../proposals/staleness-ranking-ignores-supersession.md`](../proposals/staleness-ranking-ignores-supersession.md)

## The fork

The proposal's sketch lists both, without choosing. They differ in one way that
matters more than their mechanics: **how much evidence each one needs before it
can honestly ship.**

### Option A — Annotate + `answer` prefers current

- Parse `status: superseded` / `superseded_by:` frontmatter at ingest → a
  `superseded` flag on the document in the substrate.
- `find` / `ask` **ordering is unchanged**; results carry
  `"superseded": true, "superseded_by": "<doc-id>"` in `--json` and a marker in
  human output.
- `answer` **prefers the un-superseded source** when a superseded document and
  its named successor are both in the candidate pool.
- `fux why` surfaces the flag, so an inversion explains itself.

### Option B — Down-rank superseded chunks in fusion

- Everything in A, plus a fixed penalty applied to superseded documents during
  RRF, so the current document overtakes the stale one in `find` too.

### Option C — Do nothing yet; gather a second corpus first

- Treat the whole finding as unresolved until a second realistic corpus
  reproduces it.

## Comparison matrix

| | A — annotate | B — down-rank | C — wait |
|---|---|---|---|
| Fixes rank-1 inversions in `find` | ✗ (consumer's job) | **✓** | ✗ |
| Fixes `answer` returning the retired answer | **✓** | ✓ | ✗ |
| Requires a tuned magic number | **no** | **yes** (penalty size) | — |
| Evidence needed to justify honestly | **one corpus is enough** | second corpus + tuning | — |
| Reversible if wrong | **✓ additive** | ✗ changes every ranking | ✓ |
| Can regress existing evals | **no** (ordering untouched) | **yes** | no |
| Respects the run's own do-not-do | **✓** | ✗ | ✓ |
| Leaves the product broken meanwhile | partly | no | **yes** |

## The debate

**The case for B (down-rank), stated fairly.** The measured user harm is at
rank 1 of `find`, and that is exactly what A does not touch. An engine that
knows a document is retired and still ranks it first is knowingly serving a
wrong answer. Annotation offloads the fix to every consumer, and consumers that
ignore the field — most of them, at first — see no improvement at all. If the
promise is "surface the answer that is still true," B is the only option that
delivers it.

**Why A wins anyway — the asymmetry is in the evidence, not the mechanism.**

- **A is not a heuristic.** Honoring `superseded_by: 0031` is reading a
  declaration the author wrote, deterministically. It needs no corpus evidence
  to justify, because it is not a statistical judgment about what ranks better.
  **B is a heuristic** — the penalty magnitude is a tuned number, and tuning it
  on one corpus is exactly what this run's `ANALYSIS.md` forbids.
- **The repo's own filed proposal already set this gate.** It says the finding
  "graduates via a compare doc + ADR **once a second realistic corpus confirms
  the effect and the penalty is tuned against real inversions**." A clears that
  gate; B does not. Writing a handoff for B would mean overriding a condition
  set by the measurement itself, one day after it was set.
- **B can regress what currently works.** `why` / `how-to` / `factual` all
  scored hit@5 = 1.00 on acme. A penalty applied across the corpus puts that at
  risk for a benefit measured on 12 questions. A cannot regress anything,
  because it does not reorder.
- **A makes B measurable.** Once the flag exists in the substrate and in `why`,
  the penalty becomes a small, well-instrumented follow-up with a clean
  before/after — instead of a guess shipped blind.

**C is rejected.** It treats "we can't fix all of it" as a reason to fix none of
it. `answer` fabricating the retired policy is fixable *today*, deterministically,
with no tuning. Waiting also leaves the substrate with no supersession field, so
the second corpus would produce the same finding with no new information.

## Known limits (accept explicitly, do not paper over)

- **Only frontmatter-marked supersession is reachable.** The dated-inline and
  unmarked cases need NLP, which the no-model constraint forbids. Of the 12
  measured pairs roughly a third carry machine-readable frontmatter — so the
  expected recovery is **partial**, and the handoff must measure it rather than
  claim it. **Measured post-ship** (`docs/conformance/2026-07-23-supersession-recovery/`):
  5 of 12 carry a marker, only 3 of the original 9 `find`-inversions do, and at
  the `answer` level the fix fully corrects 1 and de-cites the retired doc in a
  2nd — smaller than "roughly a third" might suggest.
- This is a **reason to prefer the frontmatter convention**, and the docs should
  say so: `superseded_by:` is the contract Fux can act on.
- **Residual risk:** if annotation alone does not move behaviour for real agent
  consumers, B becomes justified — with data, which is the point.

## Reopen-trigger

Revisit and ship **B** when *either*:

1. a second realistic corpus reproduces the inversion rate (≥ 8/12-equivalent),
   **and** a penalty magnitude can be tuned without regressing hit@5 on the
   fixture gate, acme, and the synthetic tiers; **or**
2. post-ship measurement shows consumers demonstrably ignore the annotation and
   the rank-1 harm persists.

## References

- Measured: [`../conformance/2026-07-22-acme-payments/report.md`](../conformance/2026-07-22-acme-payments/report.md) §Finding 1.
- Supersession as a docs-as-code convention: Nygard, *Documenting Architecture
  Decisions* (2011) — `superseded_by` is the established machine-readable marker,
  which is why leaning on frontmatter is a convention Fux can adopt rather than
  invent.
- The do-not-do this respects: [`../conformance/2026-07-22-acme-payments/ANALYSIS.md`](../conformance/2026-07-22-acme-payments/ANALYSIS.md) §Do-not-do.
