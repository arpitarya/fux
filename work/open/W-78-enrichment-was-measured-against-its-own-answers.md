---
type: OpenItem
id: W-78
title: "W-78 — enrichment's value was measured by an author who had read the answers, and the ruling it justified is still standing"
description: "The blind re-grade put enrichment at +1 against the +9 recorded on 2026-08-24. The comparison that deferred the cross-encoder was between a clean number and a contaminated one. Two things are owed and both are Arpit's: whether ADR-RERANK's veto 1 reopens, and whether the measurement discipline gains a blind-authorship rule."
status: open
lane: arpit
timestamp: 2026-08-24T00:00:00Z
---

# W-78 — the number that justified a ruling was contaminated

## The one-line version

**Enrichment is worth `+1` when its author has not seen the goldens, and `+9`
when they have.** The ruling that deferred the cross-encoder rests on the `+9`.

## What was measured

[The run](../regression/2026-08-24-blind-enrichment-regrade/report.md), three
arms, same corpus and engine and goldens, one variable:

| arm | pass | net | fixed | **broke** |
|---|---|---|---|---|
| no enrichment | 32 / 50 | baseline | — | — |
| **blind enrichment** | **33 / 50** | **+1** | 3 | **2** |
| enrichment as committed | 41 / 50 | +9 | 9 | **0** |

Both previously-recorded numbers **reproduced exactly**, which is what makes
this a comparison rather than a different experiment.

## Why it matters, stated as the structural argument rather than the score

**The diagnostic is the zero.** Enrichment attaches new vocabulary to nine of
ten documents — on a ten-document corpus that is a large perturbation of `df`
and `avg_wlen`. The blind arm shows what it costs unaimed: **two regressions**.

An intervention that perturbs that much and disturbs **not one** of fifty
rankings has been fitted to the evaluation. That argument does not need N to be
large, which is fortunate, because N is 1.

**Fux already has this rule in the other direction.** There is no
`--update-goldens` flag, because a golden regenerated from engine output is a
screenshot with a test attached. **This is the same failure entering through
the other door** — not the goldens fitted to the engine, but the corpus
metadata fitted to the goldens. Nothing forbade it, so nothing caught it.

## Owed — two rulings, both Arpit's

**1. Does [ADR-RERANK](../../docs/adr/0041_rerank.md) veto 1 reopen?**

It refuses the cross-encoder on two conditions, and condition 1 was argued as
*"enrichment is worth 10 points and reranking 4, and a 35 MB dependency targets
the class enrichment already covers deterministically and for free."*
**Blind, that reads +1 against +4, and the class is not covered.**

- The record has been **amended to stop asserting the contaminated number as
  today's evidence**, and deliberately **not** reopened — a ruling made on a
  comparison is reopened by the person who made it.
- ⚠ **Condition 2 is independent, and it is now MEASURED rather than assumed.**
  Identical graph and input, same `onnxruntime`, single-threaded, optimisations
  off: **82.9 % of elements differ, max `1.907e-06`** after one encoder block,
  against a `round(score, 9)` sort — **~2000x the rounding**
  ([run](../regression/2026-08-24-crossarch-drift-and-declared-supersession/report.md)).
  The cross-encoder stays refused on determinism **whatever is decided here**.
  Reopening condition 1 licenses an argument, not a build.
- **And the argument itself got weaker in a useful way.** `q015` — the failure
  that put condition 1 back on the table — **now has a deterministic fix that
  needs no cross-encoder**: declare `supersedes:` offline, let
  `superseded_weight` demote. **`q015` recovers in both blind arms.** So the
  case for reopening can no longer lean on it. ⚠ It covers **declared**
  relations only; every other kind of negation a document can express is
  untouched, and nobody has counted them.

**2. Does the measurement discipline gain a blind-authorship rule?**

[ADR-ENRICH](../../docs/adr/0040_enrich.md) governs how enrichment is generated
and pinned and says nothing about who may have seen the evaluation. `fux
enrich` **cannot** enforce it — the model is the author and fux never calls one
— so it is a **measurement-protocol rule**, and its home is
[ADR-RS](../../docs/adr/0036_predictions.md), beside the
threshold-never-moves rule it is a sibling of.

Proposed wording, for acceptance or rejection rather than as a decision taken:

> **An artifact whose author has seen the evaluation set is not evidence about
> that evaluation set.** Where fux cannot enforce this — anything a model
> writes — the run states who authored the artifact and what they had read, or
> the number is an upper bound and must be labelled one.

## ~~Agent-closable~~ — DONE 2026-08-24, and the answer is not ambiguous

**A second blind author was run.** The prediction was written before it:
*"if the second lands near `33`, contamination is the explanation; near `40`,
the first blind author was simply worse at the task."*

**It landed at `31`.**
[The run](../regression/2026-08-24-blind-enrichment-second-author/report.md).

| arm | pass | net | broke |
|---|---|---|---|
| no enrichment | 32/50 | baseline | — |
| blind #1 | 33/50 | **+1** | 2 |
| **blind #2** | **31/50** | **−1** | 2 |
| contaminated | 41/50 | +9 | **0** |

**And the decisive evidence is not the score.** Both blind authors broke the
**same two queries**, `q015` and `q021`; the contaminated author broke neither.
Two independent agents with different stated strategies producing *identical*
casualties is a property of the task, not of craft. **The confound is closed.**

**The mechanism is one word.** `q015` asks *"what is the **current** decision
for east west traffic"* and wants the current ADR. All three authors correctly
marked the superseded ADR as retired — but the blind ones wrote
*"no-longer-**current**"* and *"replaced by the **current** decision"*, while
the contaminated one wrote *"retired and replaced"* and never used the token.
**BM25F cannot see negation**: honest metadata about a retired document ranks it
as a live one. The blind authors wrote the better documentation and were
punished for a token collision.

⚠ **Fux's own answer to this is inert on the fixture.** `[ranking]
superseded_weight` demotes a document another declares it supersedes — but
`superseded_ids` reads a **frontmatter** `supersedes:` key (*declared, never
inferred*), and the playground declares its supersession in prose only. The
flag is never set, so the prior has never been graded by anything.

## Not in scope

**Whether enrichment is worth more at the design point.** Ten documents is
small enough that a searcher's plausible vocabulary is largely already present;
enrichment should pay more at 10 000. Nothing here licenses a claim in either
direction, and the golden set that would test it does not exist.

## Definition of done

- [ ] ADR-RERANK veto 1: reopened, or confirmed standing with the new number
      named in the confirmation.
- [ ] The blind-authorship rule is accepted into ADR-RS, rewritten, or refused.
- [x] ~~A second blind author~~ — **done 2026-08-24**, `31/50`, and both blind
      authors break the same two queries. The confound is closed.
- [ ] Optional, and NOT a precondition for either ruling: make the playground
      declare its supersession in frontmatter so `superseded_weight` is
      exercised at all. ⚠ It re-shas ADR-0019 and stales every arm's
      enrichment for that document — do it once, deliberately, outside a
      comparison.
