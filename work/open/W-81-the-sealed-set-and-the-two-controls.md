---
type: OpenItem
id: W-81
title: "W-81 — two of the six accepted measurement rules are not built: the sealed query subset, and the decoy / placebo controls"
description: "Arpit accepted the run-classification rule on 2026-08-25. Four of its six parts are protocol and took effect that day. Two are build work and did not: a sealed subset of fux-playground's goldens held by one owner, and the decoy-query and content-free-placebo control arms that separate source bias from content. Filed so ADR-RS decision 15 is not read as in force."
status: open
lane: agent
timestamp: 2026-08-25T00:00:00Z
---

# W-81 — the accepted rule's unbuilt half

## Why this exists as its own item

**A rule that is written down and not built reads as in force.** W-78 ruling 2
was accepted in the rewritten wording, and that wording has six parts. Four of
them — classification, reporting, the comparison bar, the resolution floor —
are protocol: they took effect the moment
[ADR-RS](../../docs/adr/0036_predictions.md) decisions 11-14 and
[`CLAUDE.md`](../../CLAUDE.md) §Conformance runs were written, and
[`tests/test_regression_runs.py`](../../tests/test_regression_runs.py) checks
the first two from 2026-08-25 forward.

**The other two are apparatus.** They are
[ADR-RS decision 15](../../docs/adr/0036_predictions.md), which is filed
`NOT BUILT` for exactly this reason. This item is where the building is owed.

## 1 · The sealed subset

**What decision 11 implies and does not supply.** Classification records
whether an author had access. It does not *remove* access, and on this project
access is the default: the goldens are in the repo, and every agent that reads
the repo can read them.

**What is owed:** a fixed subset of `fux-playground`'s 50 queries, held by one
owner, never shown to anyone who authors an artifact, scored on request, and
rotated when it leaks. Deltas are claimed on the sealed subset only.

⚠ **The tension this must resolve rather than inherit.** Sealing *shrinks* the
visible set, and 50 queries is already under-powered — TREC puts MAP error at
50 topics near 2.4 %, and decision 14's provisional floor is ±2 queries. Split
50 into 35 visible + 15 sealed and the sealed half's floor is worse than the
whole set's. **The honest options are: grow the golden set first, seal a
proportion of a larger set, or accept that the sealed half detects only large
effects and say so.** Picking silently is the failure mode.

⚠ **And "sealed" has to mean something mechanical.** A directory an agent is
asked not to read is not sealed; BIG-bench's canary GUID is the standing proof
that a marker placed *so that* it would be excluded gets trained on anyway. The
minimum credible version is that the sealed queries do not live in the working
tree at all.

## 2 · The two control arms

**The gap they close.** *Neural Retrievers are Biased Towards LLM-Generated
Content* (KDD 2024) shows retrievers rank LLM-written text higher
**independently of whether it informs**. Every enrichment arm this project has
filed added ~70 tokens of fluent LLM prose to nine of ten documents with no
matched control, so **text presence and text content are not separable in any
number on file**.

| arm | what it isolates |
|---|---|
| **decoy queries** | a query set the enrichment was not aimed at — catches an intervention that helps everything a little because it added prose, not because it added meaning |
| **content-free placebo** | enrichment of matched length carrying no information about the document — the direct measurement of source bias on this corpus |

⚠ **This does not threaten the conclusion it qualifies.** If source bias is
real here, the *content* contribution of enrichment is **lower** than measured,
not higher — and measured, blind, it was already below decision 14's floor. The
controls are owed because the runs cannot separate the two and **did not say
so**, which is the reporting defect, not because the finding is in doubt.

## 3 · Not in scope

- **Re-running the enrichment arms.** Those reports are frozen and stand as
  filed. New controls produce a **new** run, per decision 5's sibling rule.
- **The resolution floor's real value.** It is a placeholder in decision 14 and
  stays one until somebody measures author-to-author variance with more than
  the two samples on file. That is its own measurement and its own item.

## Definition of done

- [ ] A sealed subset exists, with a named owner, a stated size, and a written
      answer to the power tension in §1 — **not a silent split**.
- [ ] `sealed` is mechanical: the queries are not readable from the working
      tree by an agent that reads the working tree.
- [ ] A decoy query set exists for `fux-playground`.
- [ ] A content-free placebo enrichment of matched length exists.
- [ ] One run exercises all four, filed with `classification:` per decision 11
      — and **it will be `informed`**, because whoever builds this will have
      read everything. That is the correct label, not a reason to delay.
- [ ] ADR-RS decision 15 loses its `NOT BUILT` marker in the same change.
