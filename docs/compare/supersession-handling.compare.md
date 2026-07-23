---
type: Compare Doc
title: Supersession Handling
description: How Fux should treat a document its author marked superseded — annotate and let answer prefer the current doc, versus down-ranking superseded chunks in fusion. Verdict is annotate-first (shipped v0.25.0); the fusion penalty was reopened 2026-07-24 for a default-off calibrated test (phase 7).
status: accepted
timestamp: 2026-07-24T00:00:00Z
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
>
> **⟳ Amended (2026-07-24, Arpit) — Option B is REOPENED for a calibrated test.**
> The caveat above was measured and it holds: orbit shows the engine emitting
> "this is superseded, here is the replacement" *about the document it ranked
> first*, in 5 of 6 frontmatter-reachable pairs. **A stands and is not being
> reverted** — B is additive on top of it. What is authorised is **building the
> penalty default-off and calibrating it**, not shipping it enabled: the default
> flips only on a proven safe interval plus a separate Arpit sign-off (phase 7,
> M5). See *Reopen — Option B, 2026-07-24* below.

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

### Second data point — orbit-fulfillment, 2026-07-24 (condition 1: HALF met)

Measured on an independently-authored corpus in a domain deliberately disjoint
from acme's (`docs/conformance/2026-07-24-orbit-fulfillment/`):

- **Inversion rate 8/12 — the ≥ 8/12-equivalent bar is MET.** Not "roughly"; it
  lands exactly on the threshold.
- **The marker split was known by construction this time** (acme's 5/12 was
  accidental): 6 of 12 superseded docs carry `superseded_by:`.
- **The annotation works and does not help ranking.** 6/6 frontmatter-reachable
  superseded docs surface `superseded` + `superseded_by` in `find --json`, and
  **5 of those 6 still outrank their current replacement**, most at rank 1. The
  engine emits "this is superseded, here is the replacement" about the document
  it just ranked first.
- **Mechanism:** in 6 of 8 inversions the current doc **wins BM25F outright**
  (sometimes 2× the score) and loses on a dense-similarity edge as thin as
  **0.0006 cosine**, which RRF converts into a rank flip. A penalty would usually
  need to overcome only a very small fusion gap.
- **Cost of the defect is now visible in aggregate quality:** hybrid
  `stale-vs-current` hit@1 is **0.333 vs lexical 0.583** on orbit.

**Status of the trigger: condition 1's first clause is satisfied; its second
clause is NOT.** No penalty magnitude has been tuned or tested — this run
deliberately changed no ranking behaviour, and nothing in it supports a specific
penalty value.

**Named next step:** a penalty-tuning experiment gated jointly on the fixture
gate, acme, orbit, and the synthetic tiers, graduating through an ADR.

## Reopen — Option B, 2026-07-24 (Arpit)

**Decision: test B via a default-off, calibrated penalty.** This supersedes the
"B stays deferred" line above; it does **not** supersede the accepted verdict's
Option A, which ships and stands.

**What changed since the deferral** — each of the three arguments that defeated B
in the original debate:

| original objection | status on 2026-07-24 |
|---|---|
| *"B is a heuristic"* | **weakened.** The penalised set is **deterministic** — exactly the docs whose author wrote `superseded_by:`/`status: superseded` (orbit: 6/6 surfaced in `--json`). Only the *magnitude* is tuned. |
| *"tuned on one corpus"* | **cleared.** acme 9/12 + orbit 8/12, independent domains. The trigger's ≥8/12 bar is met exactly. |
| *"can regress what works"* | **removed by construction.** Default `0.0` is byte-identical to v0.25.0; the penalty ships enabled only if calibration proves a safe interval across fixture + acme + orbit + synthetic. |

**What is authorised, precisely:**

- **Build** the knob (`[engine.hybrid] supersession_penalty`, default `0.0`) and
  **calibrate** it across all four eval sets.
- **Not** authorised: enabling it by default. That needs a magnitude recovering a
  majority of inversions with **zero** hit@5 regression on any gate, **and** a
  separate Arpit sign-off — because B changes `find` ordering, which is the one
  thing A deliberately avoided.
- **"No safe interval exists" is a valid outcome.** Then the knob ships
  default-off with the measured trade-off curve — the same honest-permissive rule
  the confidence floor settled on.

**Penalty form (decided 2026-07-24):** a **rank offset applied before fusion** —
a superseded chunk contributes `1/(k + rank + N)` instead of `1/(k + rank)`.
Chosen over an absolute RRF subtraction because the sweep unit ("ranks") is
scale-free: independent of `rrf_k`, corpus size, and how many lists fire, so a
magnitude calibrated on orbit means the same thing on a 100k corpus. `N = 0` is
exact identity.

**Penalty, not filter.** Superseded docs stay retrievable — they rank lower, so a
question genuinely *about the retired decision* still reaches them.

**Second reason this phase exists:** the penalty de-confounds the
[decline-floor](answer-decline-floor.compare.md) margin refutation. Orbit's
smallest "answerable" margins (1e-05) came from a doc tying with its own
superseded twin — Finding 1 is manufacturing Finding 2's false-positive mode, so
fixing the first is the prerequisite to a fair verdict on the second.

Executed as **phase 7** → `docs/handoff/0007-supersession-downrank-handoff.md`.

### Result — B SHIPPED ENABLED, v0.26.0 (2026-07-24)

**The second clause of the reopen-trigger is now satisfied: a penalty magnitude
*was* tuned without regressing hit@5 anywhere.** Full evidence:
[`../conformance/2026-07-24-supersession-penalty-calibration/ANALYSIS.md`](../conformance/2026-07-24-supersession-penalty-calibration/ANALYSIS.md) ·
decision: [`../adr/0015-supersession-downrank-penalty.md`](../adr/0015-supersession-downrank-penalty.md).

| eval set | inversions | hit@5 | hit@1 |
|---|---|---|---|
| orbit | **8 → 3** | 0.887 → 0.887 | 0.566 → **0.698** |
| acme | **9 → 6** | 0.855 → 0.855 | 0.491 → **0.564** |
| fixture · synthetic 1k/5k/10k | no markers | unchanged | unchanged |

- **Safe interval `[11, ∞)`**, swept to 500 — zero hit@5 regression on any gate,
  at any value, in any question kind. Shipped default **15**.
- **100% of frontmatter-reachable inversions recovered** (orbit 5/5, acme 3/3).
  Every residual inversion is **unmarked**.
- **The matrix row "requires a tuned magic number → yes" was the right worry and
  the wrong prediction.** The number turned out to have a wide plateau, not a
  sharp optimum — every value from 11 to 500 performs identically. A knob with a
  broad safe basin is not the fragile magic number the debate feared.
- **"Can regress existing evals" — measured false.** Not one kind regressed on
  either corpus. `why`/`how-to`/`cross-doc`, the classes the debate worried
  about, are untouched.

**What the debate got right, and keep:** the insistence that B needed a second
corpus *and* a tuning experiment before shipping. Had B shipped with the original
proposal, it would have been a guessed magnitude justified by one corpus. The
delay cost one release and bought a measured interval.

**The known limit is unchanged and now quantified.** Only frontmatter-marked
supersession is reachable: 3/12 (orbit) and 6/12 (acme) inversions carry no
machine-readable marker and are permanently unfixable without a model.
**`superseded_by:` is the contract Fux can act on** — that line in "Known limits"
is now the single highest-leverage thing a corpus author can do, and the docs
should keep saying so.

## References

- Measured: [`../conformance/2026-07-22-acme-payments/report.md`](../conformance/2026-07-22-acme-payments/report.md) §Finding 1.
- Second corpus: [`../conformance/2026-07-24-orbit-fulfillment/ANALYSIS.md`](../conformance/2026-07-24-orbit-fulfillment/ANALYSIS.md) §Finding 1.
- Supersession as a docs-as-code convention: Nygard, *Documenting Architecture
  Decisions* (2011) — `superseded_by` is the established machine-readable marker,
  which is why leaning on frontmatter is a convention Fux can adopt rather than
  invent.
- The do-not-do this respects: [`../conformance/2026-07-22-acme-payments/ANALYSIS.md`](../conformance/2026-07-22-acme-payments/ANALYSIS.md) §Do-not-do.
