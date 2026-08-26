---
type: OpenItem
id: W-81
title: "W-81 — two of the six accepted measurement rules are not built: the sealed query subset, and the decoy / placebo controls"
description: "Arpit accepted the run-classification rule on 2026-08-25. Four of its six parts are protocol and took effect that day. Two are build work and did not: a sealed subset of the goldens held by one owner, and the decoy-query and content-free-placebo control arms. Also carries a SCOPE DEFECT in decision 12 found on the rule's first application — it forbids an informed run from stating a delta, which as written forbids reporting a file size — and an unbuilt orphaned-module check, after three dead modules were found in two days by hand."
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

## 3 · A scope defect in decision 12, found on the rule's FIRST application

**Filed 2026-08-25, one day after the rule was ruled.**

[ADR-RS](../../docs/adr/0036_predictions.md) decision 12 says an informed run
**never supplies a delta**. The first run filed under the rule —
[the model-removal measurement](../regression/2026-08-25-model-removal/report.md)
— is `informed` by construction (one session proposed, executed and measured the
change) and **its entire content is deltas**: a wheel 30x smaller, an index
22.6 % smaller, an ingest 6.8x faster.

**The rule as written forbids reporting a file size.** That is plainly not what
was ruled.

**The distinction the wording is missing.** Decision 12 exists because an author
who has read the evaluation queries can fit an artifact to them. That hazard
needs an evaluation set to exist. **Wall-clock seconds and bytes on disk have
no evaluation set** — there are no queries to have seen, no judgments, no
per-query scores, and no mechanism by which knowing the goldens bends a byte
count.

| kind of number | can authorship contaminate it? |
|---|---|
| nDCG, pass@k, fixed/broken on a golden set | **yes** — this is what decision 12 is for |
| bytes on disk, wall-clock, wheel size | **no** — nothing to have seen |
| p95 latency on a *chosen* query set | ⚠ **partly** — the query set is a choice, and a favourable one can be picked |

⚠ **The third row is why this is not a one-line fix.** A latency number sits
between the two: the metric cannot be fitted, but the *sample* can. Any
narrowing has to say which side that falls on, and the answer is probably
*declare the query set and how it was chosen* rather than *blind or informed*.

**Not adjudicated here.** The rule is one day old and was ruled by Arpit;
narrowing it is his. The measurement applied it **as written** and disclosed the
conflict in its own report rather than quietly exempting itself.

## 4 · A check for orphaned modules — three found in two days, none by a test

**Not part of the accepted rule; filed here because it came out of the same
work and has no better home.**

Three modules under `src/` were deleted in two days for having no caller:
`query/hybrid.py`, `query/fuse.py`, and `embed/fuxvec.py`. **All three had
passing tests the whole time**, which is exactly why none was noticed: a tested
module looks alive. `fuxvec.py` had been dead since 2026-08-23 — `doc_code`,
`hamming`, `prefilter` and `CODE_BYTES` with **zero call sites** in `src/`, and
`quantize` reached only from a function nothing called.

**What would catch the fourth:** a check flagging any `src/` module with no
importer outside its own package and no caller outside its own tests.

⚠ **It needs a declared-exception list before it can be green** — entry points,
`__init__` re-exports and CLI-dispatched handlers all look orphaned to a naive
importer graph, and a check that cannot go green gets deleted.

## 5 · Not in scope

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
- [ ] **§3 is Arpit's**, not an agent's: decision 12 either gains a scope line
      distinguishing quality deltas from cost deltas, or it does not and cost
      measurements keep disclosing the conflict. Both are defensible; picking is
      not an agent's call.
- [ ] The orphaned-module check in §4, **with its exception list**, or a written
      decision not to build it.
