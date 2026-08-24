---
type: Analysis
title: "2026-08-24 — what this run does NOT establish"
description: "Four things weaken the headline: the goldens were written by the agent that then optimised against them, the enrichment was written by an author who had already seen the queries, the corpus is ten documents, and the reranker's constants were picked after seeing the score. Each is stated with what it would take to remove it."
status: filed
timestamp: 2026-08-24T00:00:00Z
---

# What this run does not establish

The report says 28 → 41. This file is why that number should be read with four
specific reservations, and what each would cost to remove.

## §1 · ⚠ The enrichment was written by an author who had seen the queries

**This is the most serious one and it is not fully mitigable after the fact.**

The 10 enrichment files were written by me, following `ENRICH-SKILL.md`, *after*
I had already run the 50 goldens and read the 22 failures. The skill's own
instruction is *"name what kind of question this document answers"* — which is
what I wrote — but I cannot prove I was not steering toward known queries, and
I probably was, at least unconsciously.

**Therefore: the enriched numbers (38, 41) are an UPPER BOUND, not a
measurement.** Treat them as *"enrichment can reach this"*, never as *"a team's
enrichment will reach this."*

The unenriched reranker numbers (28 → 32) are **not** affected: the reranker
was written and swept before any enrichment existed, and its inputs are the
documents, not the enrichment.

**To remove it:** have enrichment written by an author who has not seen
`queries.jsonl`, and re-grade. That is one clean session and it is the single
highest-value follow-up in this whole area.

## §2 · The goldens were written by the agent that then optimised against them

`goldens/README.md` forbids goldens derived from the engine's output, and these
are not — ground truth was fixed by reading the corpus before any command ran,
which is the [graph-acceptance](../2026-08-22-graph-acceptance/) precedent's
standard. But the *author* of the goldens is the same agent that then tuned
`COVERAGE_POWER` and `WEIGHT` against them.

Two things limit the damage, and neither eliminates it:

- **The constants came off a plateau, not a peak.** The 4×5 sweep scores 30–32
  everywhere. A number picked from a flat region is far less overfit than one
  picked from a spike — but 50 queries is 50 queries.
- **`known_failure` was stripped before the first run**, so the baseline is a
  measurement and not a prediction. My nine predictions were **5 right, 4
  wrong**, which is itself the argument for having stripped them.

**To remove it:** a second corpus with goldens someone else wrote. `fux-lab`'s
`graph-acceptance` set is the nearest candidate and has the same provenance
problem.

## §3 · Ten documents is not a corpus

Every ranking number here comes from a 10-document set. Corpus statistics —
`df`, `avg_wlen`, the length normaliser — behave very differently at 10 and at
10 000, and BM25F's length normalisation is exactly what the reranker is
compensating for.

Only the **latency** figures used the 10 000-document corpus. Quality at 10 000
is unmeasured, because `fux-lab` has no goldens.

**To remove it:** goldens over the lab corpus. That is a bigger job than this
one was, and the honest reason it has not been done is that nobody has written
them.

## §4 · One golden regressed and I have not explained it

`q044` (*"why not use ebpf instead of a proxy"*) passes with enrichment and
fails with enrichment **plus** reranking. It is reported in the table and it is
not diagnosed. A single regression inside a net +3 is a reasonable trade, but
"reasonable trade" is a judgement I made and did not test.

## §5 · What IS solid

- **4 fixed / 0 broken, unenriched.** No contamination path — the reranker
  never sees enrichment.
- **18 of 18 survivors are vocabulary gaps, 0 ordering.** A mechanical check of
  term membership, not a judgement. This is the load-bearing finding for
  ADR-RERANK veto 1 and it does not depend on the goldens being *right* — only
  on the target documents genuinely lacking those words, which is a fact about
  the corpus.
- **The differential law: 240 comparisons, 0 divergent.** A property, not a
  score.
- **+8 ms p95 at 10 000 documents.** Real corpus, real measurement.

## §6 · The prediction I got wrong, recorded

I predicted nine `known_failure`s from reading the corpus. Five were right
(`q018`, `q020`, `q027`, `q035`, `q050`). **Four were wrong — and all four were
my "vocabulary gap" predictions** (`q042`, `q045`, `q046`, `q048`), which
passed. I over-estimated how badly BM25F handles a vocabulary gap when the
corpus is small and the target document is short.

Seventeen failures I did not predict at all.

**The lesson is procedural and it generalises: a prediction written into a test
fixture is not evidence, and stripping the nine before the first run is the
only reason this file can report the error rate instead of hiding it.**
