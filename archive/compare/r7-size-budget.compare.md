---
type: Compare Doc
title: "R7's size budget — what shape should it have at a design point that moves?"
description: "The 250 MB @100k row died with the design point. Five shapes for its successor: an absolute at 10k, a ratio to the indexed corpus, a per-document allowance, a clone-time bound, or retiring R7. Proposed verdict: the SHAPE is a ratio; the NUMBER is Arpit's, and this document deliberately does not pick it."
status: retired
timestamp: 2026-08-22T00:00:00Z
---

# R7's size budget — Comparison

> ## RETIRED 2026-08-22 — the question was dissolved, not answered.
>
> **Arpit retired R7 outright**: *"remove that promise, it's not needed…
> nothing related to fifty thousand or hundred thousand should be tested or
> committed, or have rules or promises for it."*
>
> **There is no size budget, and no successor is owed.** This document asked
> *what shape should the threshold have* and proposed **B, a ratio**, leaving
> the number for Arpit. He removed the requirement for a number at all, which
> makes the shape question moot — you cannot pick a good shape for a promise
> nobody is making.
>
> **It is kept, not deleted, for two reasons.** The reasoning survives if a size
> promise is ever wanted again — and §6's contamination argument (that whoever
> has already seen the measurements cannot honestly pick the threshold) is a
> general lesson about this project's pre-registration discipline, not a fact
> about R7.
>
> **The index size is still measured.** ADR-POSTINGS and ADR-INDEX-LIFECYCLE
> both keep a check that prints it — as **information, never as a gate**. Watch
> the number; read no verdict off it.
>
> **Reopen only if** Arpit asks for a size promise again. It would be a **new
> prediction with a new id at 10 000 documents** — never a revival of R7, whose
> id is retired and not reused.

---

## §1 · For humans — the short version

R7 asked: **is the committed index small enough?** Its threshold was
`≤ 250 MB packed at 100 000 documents`, derived from the paper's §5 model.

Two things then happened. The design point moved to **10 000 documents**
(2026-08-21), and W-26 said the old row is *"history, not a divisor"* — **not**
25 MB. And T2, the tier R7 was originally gating, was **measured and declined**
([R9](../regression/2026-08-22-r9-t2-at-10k/VERDICT.md), 2026-08-22).

So R7 needs a new threshold, and the interesting question turned out not to be
*what number* but *what kind of number*. **An absolute budget has to be
re-derived every time the design point moves** — which is exactly what just
happened, and what will happen again at 50 000. A budget expressed as a ratio
does not.

> **⚠ 2026-08-22 — Arpit's measurement ceiling cuts against this document's own
> main argument, and that is recorded here rather than quietly ignored.** The
> case for a *ratio* over an *absolute* rests on **"an absolute has to be
> re-derived every time the design point moves — and it will move again at
> 50 000."** Arpit has now closed 50 000 and 100 000 to measurement until the
> tool is built out, so **that re-derivation is deferred indefinitely** and the
> ratio's headline advantage is worth much less *today* than when this was
> written. It is not worthless: the re-derivation still lands whenever the
> ceiling lifts, and a ratio is still the shape that survives it.
> **The verdict is not changed here** — whoever rules on it weighs this, in the
> same change, the way the hook-at-scale doc required of its own ruler.
> **The blocker is unaffected either way**: the *number* was always Arpit's, and
> the contamination problem (§6) does not care what size is in scope.

**One fact makes this urgent rather than tidy.** The committed index is
currently **larger than the content it indexes** — 141 % of corpus bytes on a
synthetic 10 000-document corpus, **211 %** on this repository's real prose.
Compressed, 23 % and 76 %. Whatever shape is chosen, a reader deserves to know
that the artefact fux commits is not a small annotation on the corpus; at real
prose density it is comparable to carrying the corpus twice.

## §2 · Context

### What R7 was

| | |
|---|---|
| threshold | `committed @100k target-density ≤ 250 MB git-packed; tier-auto correct` |
| where it came from | the paper's §5 model — `≈ 220–290 MB at 10⁶`, re-anchored to 100k |
| status | **CLOSED unmeasured** 2026-08-21 (Arpit), re-derivation owed to M6 |

### What retired it, and what it now gates

- **The design point moved** to 10 000 documents. A threshold frozen against
  10⁵–10⁶ measures a system nobody is shipping.
- **T2 is no longer downstream of it.** R7 originally gated M6's tier work;
  [the T2 proposal](../proposals/t2-segments.md) declined T2 on
  *latency*, measured, and said in as many words that *"a T2 decision taken on
  latency says nothing about size"*.
- **What R7 gates now is [ADR-POSTINGS](../../docs/adr/0013_postings.md)'s
  compact encoding** — BIC postings, an MPH dictionary, front-coded ledger;
  proposed and unbuilt. That is a live question, so R7 is **not** pointless.
  It has a different consumer than it had in August.

### The measured position — read §6 before using these

**Post-hoc characterisation, not a verdict.** Every number here was taken
*before* any threshold was chosen, which is the problem §6 is about.

| corpus | documents | index raw | vs corpus raw | index packed | vs corpus raw |
|---|---|---|---|---|---|
| synthetic ([R9](../regression/2026-08-22-r9-t2-at-10k/report.md)) | 10 000 | 14.2 MB | **141 %** | 2.3 MB | 23 % |
| this repo, real prose | ~176 files | 4.7 MB | **211 %** | 1.7 MB | 76 % |
| this repo, 2026-08-21 analysis | 345 | 4.1 MB | — | 1.7 MB | — |

**91.3 % of raw index bytes are `terms`** — postings stored as
`"<16-hex>": [f, f]` inside JSON, which is roughly a 2× blow-up over a packed
binary key before any docid-delta or impact quantisation
([the analysis](../regression/2026-08-21-r7-preliminary-analysis/ANALYSIS.md)).
**That is the gap ADR-POSTINGS exists to close**, and it is why a FAIL here
would motivate building an encoder rather than condemning the architecture.

## §3 · Options

- **A — An absolute budget at 10 000 documents.** *"≤ X MB packed at 10k."*
  The same shape as the retired row, re-derived at the new size.
- **B — A ratio of committed index to indexed corpus** *(proposed shape)*.
  *"Packed index ≤ X % of the packed corpus it indexes."* Scale-invariant by
  construction: it never needs re-deriving when the design point moves.
- **C — A per-document allowance.** *"≤ X packed bytes per document."* What
  the paper's §1.3 already implies with `~250 B/doc`, and what the 2026-08-21
  analysis measured against.
- **D — A clone-time bound.** *"The index adds ≤ X seconds to `git clone` on a
  stated connection."* Ties the budget to the experience it exists to protect.
- **E — Retire R7 without a successor.** The tier it gated is declined; let
  ADR-POSTINGS' own veto carry the size question instead.

## §4 · The matrix

Weights: **(H)** decides · **(M)** matters · **(L)** tiebreak.

| criterion | A · absolute @10k | **B · ratio** | C · per-doc | D · clone time | E · retire |
|---|---|---|---|---|---|
| **survives the next design-point move (H)** | **no** — re-derive at 50k | **yes** | yes | yes | n/a |
| **derivable without seeing the engine's numbers (H)** | no — needs a size in mind | **yes** — "must not cost more than the content" | partly | yes | yes |
| **fair across corpus density (H)** | no — 10k RFCs ≠ 10k tweets | **yes** | **no** — the worst axis | yes | n/a |
| checkable by one command (M) | yes | **yes** | yes | **no** — machine and network dependent | n/a |
| still gates ADR-POSTINGS (M) | yes | **yes** | yes | weakly | **no** |
| matches how the paper argues (M) | yes | no | **yes** | no | no |
| a user recognises the quantity (M) | somewhat | **yes** — "it doubles my repo" | no | **yes** | n/a |
| precedent in this repo (L) | the retired row | ADR-CACHE's disk bound | paper §1.3 | none | — |

**Why C loses despite matching the paper.** A per-document allowance is
insensitive to the one variable that actually drives index size: document
length, through vocabulary. The two corpora above differ by **18× in bytes per
document**, and a single per-document budget would call one of them wrong for a
reason that has nothing to do with fux's efficiency. It is scale-invariant in
the wrong dimension.

**Why D loses.** Latency is machine- and network-specific, and this project
already refuses machine-dependent thresholds — fux-lab's TEST-PLAN §2 says a
re-run on another surface is a new measurement, not a confirmation. A budget
nobody can check the same way twice is not a budget.

**Why E loses.** R7's consumer changed; it did not disappear. ADR-POSTINGS is
proposed-and-unbuilt, and the honest gate for building it is *"the committed
index is too big"* — which is a measurement, which needs a threshold.

**Why A loses, and it is the important one.** It is the shape that just failed.
An absolute number is frozen against a corpus size, so it dies the moment the
corpus size the project cares about changes — which has now happened twice
(10⁶ → 10⁵ → 10⁴). Choosing it again means re-running this exercise at 50 000.

## §5 · The proposed verdict — shape B, and no number

**Adopt the ratio shape.** *The committed index must not cost more to carry
than a stated fraction of the content it describes.*

That sentence is derivable from first principles by someone who has never seen
a fux measurement, which is the property that matters here. It is also the
form a user recognises: *"installing fux roughly doubles my repository"* is a
statement someone can have an opinion about, where *"the index is 14.2 MB"* is
not.

**Three details the shape needs, and they are cheap:**

1. **Packed against raw, or packed against packed?** Recommend **packed index
   against packed corpus** — both sides measured the way git actually stores
   them, since clone weight is what the budget protects. The table in §2 shows
   packed-against-*raw* because a packed corpus figure was not measured; that
   is a gap to close when the threshold is set, not a reason to prefer it.
2. **Measured on which corpus?** Recommend **a real-prose corpus**, because the
   synthetic one understates the ratio by ~3×. The honest problem is that
   [W-56](../../work/IMPLEMENTATION.md) lost the RFC corpus, so the largest real
   one available is this repository at ~176 documents.
3. **The ratio still needs the population curve reported beside it**, per the
   discipline every other pre-registration here uses.

**What this document deliberately does not do: pick X.**

## §6 · The contamination, stated plainly

**This is the reason the threshold is blank rather than proposed.**

The rule is that a threshold is written before the number exists. That is
already impossible for R7: the 10 000-document index size was measured on
2026-08-22 as characterisation for the paper's §5 rewrite, and it is in §2 of
this document. **Whoever picks X now picks it knowing the engine sits at 23 %
synthetic and 76 % real.**

- Proposing **≤ 100 %** would be proposing a threshold the engine passes.
- Proposing **≤ 50 %** would be proposing one it fails on real prose.

Both are defensible in the abstract and neither is defensible *from here*. An
agent choosing between them after reading the measurement is doing exactly what
W-26's *"do not pick the number to fit the engine"* forbids, in whichever
direction it chooses.

**What is not contaminated is the shape.** "The index should not cost more than
the content" is a product statement, and the argument for a ratio over an
absolute is about *re-derivability across design-point moves* — it would hold
identically if the engine measured 5 % or 500 %.

**A mitigation, if Arpit wants the stronger form:** set X from the paper's §5
model rather than from §2's table. The model projects `≈ 220–290 MB` against a
`10⁶ × ~65 KB` corpus — a **~0.4 % ratio** — which is a number derived years
of reasoning away from anything the current engine weighs. That the engine is
two orders off that is itself the finding, and it is ADR-POSTINGS' motivation
rather than a reason to move the target.

## §7 · Consequences

- **R7 stops being a moving target.** A ratio survives 50 000 and 100 000
  without re-derivation, so this fork is fought once.
- **Two accepted records currently run a veto check against a retired
  threshold** — ADR-POSTINGS and ADR-INDEX-LIFECYCLE both say
  `<= 250 MB packed @100k`. W-65 marked both as retired-with-no-successor on
  2026-08-22; **whichever shape wins, those two lines are updated in the same
  change** that sets the threshold.
- **The paper's §1.3 `~250 B/doc` contribution is a per-document claim**, i.e.
  shape C. If B is adopted, that sentence is describing a quantity the project
  no longer gates on, and should say so.
- **A ratio makes "which corpus" load-bearing** in a way an absolute does not,
  because the denominator is now part of the measurement. That is a real cost
  and it is the strongest argument for A.

## §8 · Reference

- [W-26](../../archive/open/W-26-m6-scale-t2.md) §re-scope — *"is not simply divided by
  ten"*, and the instruction that makes this Arpit's.
- [The 2026-08-21 preliminary analysis](../regression/2026-08-21-r7-preliminary-analysis/ANALYSIS.md)
  — 2.429× real git-pack compression, 91.3 % of raw bytes in `terms`, and why
  the shortfall is a representation cost rather than an architectural one.
- [R9](../regression/2026-08-22-r9-t2-at-10k/report.md) — the 10 000-document
  size numbers, filed as characterisation and labelled `index_size_POST_HOC_not_R7`.
- [ADR-POSTINGS](../../docs/adr/0013_postings.md) — the compact encoding this
  budget now gates, proposed and unbuilt.
- [the T2 proposal](../proposals/t2-segments.md) — why size and latency
  were separated, and why declining T2 left R7 open rather than closing it.
- CLAUDE.md §"A pre-registered threshold may never move" — the rule §6 is
  refusing to break.
