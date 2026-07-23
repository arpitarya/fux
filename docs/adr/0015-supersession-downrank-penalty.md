---
type: ADR
title: Supersession down-rank penalty
description: A configurable rank offset applied in RRF fusion to author-marked superseded documents — built default-off, calibrated across four eval sets, enabled at 15 on measured evidence. Also records the margin check's independent refutation.
timestamp: 2026-07-24T00:00:00Z
tags: [retrieval, staleness, ranking, fusion, honest-decline]
---

# ADR-0015: Supersession down-rank penalty

- **Status:** accepted
- **Date:** 2026-07-24
- **Feature:** phase 7 — supersession down-rank + margin re-measure (v0.26.0)

## Context

ADR 0013 taught the engine to **recognise** a superseded document. It
deliberately did not let it **act** on that in `find` — Option A in
[`../compare/supersession-handling.compare.md`](../compare/supersession-handling.compare.md),
chosen because a down-rank penalty needs a tuned magnitude, and tuning on one
corpus is what this project forbids.

Two independent realistic corpora then measured the consequence:

- **acme-payments: 9/12** stale-vs-current pairs put the retired document above
  the still-true one. **orbit-fulfillment: 8/12** — an independently-authored
  corpus in a deliberately disjoint domain.
- **The engine annotates the document it ranks first.** On orbit, 6/6
  frontmatter-reachable superseded docs carry `superseded`/`superseded_by` in
  `find --json`, and **5 of those 6 still outrank their replacement**, most at
  rank 1.
- **Mechanism:** in 6 of 8 inversions the current document **wins BM25F
  outright** — sometimes 2× the score — and loses on a dense-similarity edge as
  thin as **0.0006 cosine**, which RRF converts into a rank flip. Superseded
  documents here are short and state the old fact plainly, so the whole document
  is on-topic; current documents are longer and cover more ground, so their
  embedding is diluted.

That met the reopen-trigger's first clause exactly (≥8/12). Arpit reopened
Option B on 2026-07-24 for a **default-off, calibrated test** — explicitly not
for shipping it enabled.

## Decision

**A rank offset applied in RRF fusion to the author-marked superseded set,
`[engine.hybrid] supersession_penalty`, defaulting to 15.**

Four sub-decisions, each load-bearing:

### 1. A rank offset, not a score subtraction

A penalised chunk contributes `1/(k + rank + N)` instead of `1/(k + rank)`.

The sweep unit is **ranks**, which is scale-free — independent of `rrf_k`,
corpus size, and how many lists fire. A magnitude calibrated on a 900-document
corpus therefore means the same thing on a 100k one. An absolute subtraction from
the fused score would have been entangled with all three.

*(This deviates from the handoff's `−X` wording; recorded in IMPLEMENTATION.md.)*

### 2. A penalty, never a filter

Superseded documents stay retrievable — they rank lower. A question genuinely
*about* the retired decision still reaches its answer. Measured: at penalty 15
the retired same-day-cutoff ADR moves from **rank 1 to rank 17** and remains in
the result set.

### 3. The penalised set is deterministic

Exactly the documents whose frontmatter carries `status: superseded` /
`superseded_by:`, resolved into chains at ingest. **Nothing is inferred from
prose.** A document that merely says "superseded" in its body is never touched.

This is what made Option B shippable where a content heuristic never would be:
**only the magnitude is tuned, not the set.** The original debate scored B as
"a heuristic"; that objection applies to the number alone.

### 4. Default 0 was the landing gear; 15 is the measurement

The knob shipped at `0` first — exact identity, every golden byte-identical to
v0.25.0 — so the code could land before it was safe to enable. The default moved
to 15 only after calibration and a separate human sign-off.

**The calibration** (`docs/conformance/2026-07-24-supersession-penalty-calibration/`),
swept across all four eval sets:

| eval set | inversions | hit@5 | hit@1 |
|---|---|---|---|
| orbit (53) | **8 → 3** | 0.887 → 0.887 | 0.566 → **0.698** |
| acme (55) | **9 → 6** | 0.855 → 0.855 | 0.491 → **0.564** |
| fixture (21) | n/a — no markers | 1.000 flat | 0.810 flat |
| synthetic 1k/5k/10k | n/a — no markers | identical | identical |

- **Safe interval `[11, ∞)`**, swept to 500. Zero hit@5 regression on any gate,
  at any value, in **any question kind**.
- **100% of frontmatter-reachable inversions recovered** on both corpora
  (orbit 5/5, acme 3/3). Every residual inversion is an **unmarked** document.
- **15** sits inside the plateau, clear of the 11 boundary.

## Alternatives considered

- **Keep Option A (annotation only).** Rejected on measurement, not principle:
  the annotation demonstrably works and demonstrably does not move rank. An
  engine that knows a document is retired and still ranks it first is serving a
  wrong answer to every consumer that does not read the field.
- **Absolute RRF score subtraction.** Rejected — not scale-free (see §1).
- **A multiplicative factor** (`score × (1−p)`). Rejected: demotion strength
  would vary with the document's own score, so the same marker would demote
  unequally.
- **Filtering superseded documents out.** Rejected — destroys the "what did we
  used to do?" query, which is a legitimate and common question of a knowledge
  corpus.
- **Ship the knob but keep the default at 0** pending a third corpus. A real
  option, presented at M5 with its trade-off. Arpit chose to enable: two
  independent corpora is the bar this project set, and the measured downside was
  nil.
- **Inferring supersession from prose** (dated "*Superseded 2026-03*" notes, of
  which both corpora have several). Forbidden by the no-model constraint, and
  not revisited.

## Consequences

**Easier**

- The default `find` ordering now reflects what the author said is current. The
  measured rank-1 harm is fixed for every consumer, not only those that read the
  annotation field.
- `hit@1` improves materially on both realistic corpora, with `stale-vs-current`
  roughly doubling (orbit 0.333 → 0.667).
- `fux why` explains the demotion:
  `superseded → rrf penalised by 15 ranks (rank 1→17)`.

**Harder / owed**

- **`find` ordering now changes with a config value.** Option A's clean "we
  never reorder" property is gone. `0` restores pre-0.26 behaviour exactly, and
  that escape hatch is tested.
- **The unmarked residual is permanent.** 3/12 (orbit) and 6/12 (acme)
  inversions carry no machine-readable marker and cannot be reached without a
  model. **The remaining lever is documentation, not engineering** — this is the
  concrete reason to evangelise `superseded_by:` as a convention.
- **No upper bound is proven.** Values to 500 showed no harm on three marked
  corpora, but no real corpus exercises "a superseded document is the best answer
  to an unrelated query." A unit test covers the shape; a corpus does not.
- **The graph re-fusion path is deliberately un-penalised.** `_fuse_graph`
  re-fuses an already-penalised ordering; applying the offset again would demote
  twice by an amount varying with whether graph expansion fired, making the
  calibration curve non-comparable across queries. Accepted consequence: a
  superseded document reached *only* by graph expansion is not penalised. No
  corpus here exhibits it; if one does, that is evidence for extending the
  penalty, not a reason to guess now.
- **Lean must honour the penalty too**, and does — it reads the marker from its
  committed state flags. Otherwise lean and full rankings would be identical only
  while the knob was off, weakening the df-sidecar parity law from *provably* to
  *usually*.

## The margin re-measurement (Finding 2) — refuted independently

This phase existed partly to de-confound a separate question. The orbit run
refuted the runner-up **margin check** as a fabrication discriminator, but
flagged the refutation as confounded: the smallest "answerable" margins came from
documents tying with **their own superseded twins**. Finding 1 was manufacturing
Finding 2's false-positive mode.

Re-measured at penalty 15 on both corpora:

- **The confound was real** — orbit's previously-minimal `factual` question
  improved.
- **It was not the cause.** A `how-to` question sits at **1e-05 before and
  after, unmoved** — two documents genuinely agree, and no supersession is
  involved. acme is **identical** before and after, its minimum held by a
  `cross-doc` question.
- Unanswerable margins are unchanged (0.00052 – 0.00411) in both corpora.
- `max(unanswerable) = 0.00411` still exceeds `min(answerable) = 1e-05` by two
  orders of magnitude.

**The residual failure mode is precisely the one the compare doc predicted
before anyone measured it:** *"when several documents genuinely agree on an
answer, their scores are legitimately close. A margin check declines precisely
there."*

**Verdict: fabrication on well-formed out-of-scope questions is a permanent
product boundary of extractive answering without a model.** Three no-model
discriminators — absolute floor, runner-up margin, margin ratio — are refuted
across two independent corpora, one de-confounded. **No fourth mechanism is
proposed**, and inventing one to force a fix would be the wrong move. See
[`../compare/answer-decline-floor.compare.md`](../compare/answer-decline-floor.compare.md).

## References (required)

- **The calibration:**
  [`../conformance/2026-07-24-supersession-penalty-calibration/ANALYSIS.md`](../conformance/2026-07-24-supersession-penalty-calibration/ANALYSIS.md)
  — the four-eval-set sweep, the reachable-recovery split, the margin
  re-measurement, with repro commands.
- **The two corpora that justified reopening:**
  [`../conformance/2026-07-22-acme-payments/ANALYSIS.md`](../conformance/2026-07-22-acme-payments/ANALYSIS.md) §Finding 1 ·
  [`../conformance/2026-07-24-orbit-fulfillment/ANALYSIS.md`](../conformance/2026-07-24-orbit-fulfillment/ANALYSIS.md) §Finding 1.
- **The fusion baseline this modifies:** Cormack, Clarke & Buettcher,
  *Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning
  Methods* (SIGIR 2009) —
  https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf. RRF's premise is
  that rank position, not score, is the transferable signal across rankers; a
  **rank offset** is therefore the modification that stays inside the method's
  own coordinate system, which is why it transfers across corpus scales.
- **The `superseded_by` convention:** Nygard, *Documenting Architecture
  Decisions* (2011) —
  https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions.html
  — establishes the machine-readable marker Fux honours rather than invents.
- **Unanswerable questions as a first-class metric:** Rajpurkar, Jia & Liang,
  *Know What You Don't Know: Unanswerable Questions for SQuAD* (ACL 2018) —
  https://aclanthology.org/P18-2124/ — the framing under which "declines
  correctly" is a measured property, and under which this ADR reports the
  no-model boundary rather than hiding it.
