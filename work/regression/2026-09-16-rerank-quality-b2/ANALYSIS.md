---
type: Analysis
name: rerank-quality-b2-analysis
description: "Why this is a FAIL and not another VOID, what the 28-of-47 quoting-document finding means for the next contest set, and what W-154 can and cannot close on."
---

# Why this is a FAIL and not another VOID

**The VOID run and this one both returned a large negative net. They are not the
same result, and the difference is not a judgement call.**

| | VOID (2026-09-15) | this run |
|---|---|---|
| baseline reachability | **3.3 %** — nearly saturated at zero | **21.9 %** |
| regression headroom | ~4 in 120 | **118 in 538** |
| what won the breaks | **the query's own source**, 75 % | another quoting document 60 %, a genuine peer 40 % |
| could the endpoint move both ways? | **no** | **yes** |

**A negative measured where the endpoint cannot go positive is not a negative.**
That was the VOID case. Here the endpoint is right 118 times at baseline and
wrong 420 times, so both directions were open and the arm chose one.

## 🔴 The finding for whoever builds the next contest set

**28 of 47 breaks were won by a document that quotes the citing sentence.**

The cited-decision generator produces queries by lifting a citing author's own
sentence. In *this* repository that sentence is frequently **not unique**: the
same wording appears in `work/DOC-REGISTRY.md`, in a worklog entry, in an
archived work item and in the record that quotes it. Excluding one `source`
removes one of several perfect proximity matches.

**Three things follow, and none of them is "widen the exclusion":**

1. **Widening it post-hoc would be the moving-threshold failure.** The
   pre-registration excluded `source`, the run ran, and the number is the
   number. The sensitivity row exists to say what would change, not to replace
   the verdict.
2. **An exclusion set that grows until the result is clean is not an
   endpoint.** Each widening is a decision about what counts as a rival, made
   with the answer visible. The next instrument should produce **queries that
   are not lifted verbatim from any corpus document** — which is a different
   generator, not a bigger filter.
3. 🔴 **The circularity screens still cannot see this.** Both passed — 0.4141
   passage-level, 0.5273 document-level — across both runs, with the
   contamination present the whole time in two different forms. **A screen
   compares the truth against rivals it is handed and never asks what else is in
   the corpus.** That limitation is now measured twice and is the most
   transferable thing either run produced.

## What W-154 closes on, and what it does not

**Closes:** *does proximity reranking earn its latency?* — on the `ask` path, on
this corpus. **Part A** priced it at **+15 to +19 ms p50, flat in corpus size**.
**Part B** says the thing you would pay that for makes results **worse**, at
`p = 0.0000`, with both headrooms open. Together that is a complete answer to
the item's own question, and `rerank_weight` stays at `0.0` with a measured
reason rather than a held request.

**Does not close:**

- 🔴 **W-108's two-mechanism split.** `ask` never fetches. The refer plane's
  rescore is **unpriced**, and the `answer` path could not carry it on this
  contest set (0 of 120 at baseline, both criteria). That needs a generator
  whose queries are not corpus sentences.
- **Whether `rerank_weight` helps any other corpus.** `informed`, dogfood, one
  tree.

## What this cost

~25 minutes and ~1 080 subprocesses for the arm, plus ~5 minutes for the
reachability check that scoped it and ~1 minute for the who-won diagnostic.

⚠ **The reachability check is what made the 25 minutes worth spending.** Without
it the `answer` path would have run too — another ~1 080 subprocesses to file an
`INCONCLUSIVE` that was knowable in advance.
