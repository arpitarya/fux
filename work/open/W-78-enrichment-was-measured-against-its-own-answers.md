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
- ⚠ **Condition 2 is independent and untouched.** `onnxruntime` is still not
  byte-identical across x86-64 and arm64, so the cross-encoder stays refused on
  determinism **whatever is decided here**. Reopening condition 1 does not
  license a build; it licenses an argument.

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

## Agent-closable now, if 1 is ruled either way

- **A second blind author** separates contamination from craft, which is the
  one thing this run cannot do. If the second lands near `33`, contamination is
  the explanation; near `40`, the first blind author was simply worse at the
  task. Cheap: the protocol is written down in the run's report.

## Not in scope

**Whether enrichment is worth more at the design point.** Ten documents is
small enough that a searcher's plausible vocabulary is largely already present;
enrichment should pay more at 10 000. Nothing here licenses a claim in either
direction, and the golden set that would test it does not exist.

## Definition of done

- [ ] ADR-RERANK veto 1: reopened, or confirmed standing with the new number
      named in the confirmation.
- [ ] The blind-authorship rule is accepted into ADR-RS, rewritten, or refused.
- [ ] If either ruling wants it: a second blind author, filed as a new run.
