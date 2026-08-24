---
type: Regression
title: "2026-08-24 — the playground has goldens again, and Phase 6 is built and measured"
description: "The first graded run since W-56 destroyed queries.jsonl on 2026-08-20. Baseline 28/50. The proximity reranker takes it to 32 (4 fixed, 0 broken); enrichment takes it to 38; both together 41. The finding that decides the cross-encoder question: of the 18 goldens surviving the reranker, 18 are vocabulary gaps and 0 are ordering failures."
status: filed
timestamp: 2026-08-24T00:00:00Z
---

# Rerank, enrich, and the first graded run in four days

**Arpit, 2026-08-24:** *"You will have to create the goldens if needed. You
will have to test them and then build out the reranker. All is on you. Make a
call on it."*

## §1 · What ran

| | |
|---|---|
| corpus | `fux-playground`, 10 documents, copied to `/tmp/pg` |
| goldens | 50, written from the corpus before any query ran |
| grader | `check.py`, rank-only, `--top 5` |
| engine | this working tree (W-76 phases 0–5, 7–9 + Phase 6) |
| latency corpus | `fux-lab/2026-08-22-r9-t2`, 10 000 real documents |

## §2 · The headline

| configuration | pass | fixed | broken |
|---|---|---|---|
| BM25F alone | **28 / 50** | — | — |
| + reranker (`rerank_weight = 1.0`) | **32 / 50** | 4 | **0** |
| + enrichment, no reranker | **38 / 50** | 10 | 0 |
| + enrichment + reranker | **41 / 50** | 4 | 1 |

**Reranker alone: 4 fixed, 0 broken** — `q013`, `q015`, `q020`, `q026`.
**On top of enrichment: 4 fixed, 1 broken** (`q044`), net +3.

## §3 · The finding that decides the cross-encoder question

Of the **18** goldens still failing after reranking, every one was checked for
whether the target document contains the query's analyzed terms at all:

```
vocabulary gap (target document never says some of the searcher's words):  18
pure ordering  (every term present, merely ranked too low):                 0
```

**The reranker fixed every ordering failure the corpus had.** What is left is
not a ranking problem and no reranker of any kind can reach it — the document
does not contain the words. `q006` is the clean example: *"what happened during
the checkout outage"* against a postmortem titled *"checkout unavailable for 47
minutes"* that **never uses the word "outage"**. Other documents link to it as
"the checkout outage"; it never says so itself.

That is why enrichment is worth 10 points here and reranking 4, and it is the
whole argument in ADR-RERANK veto 1.

## §4 · Cost

10 000 real documents, accelerator path, 60 queries × 6 repeats:

| | p50 | p95 | max |
|---|---|---|---|
| rerank off | 16.50 ms | **33.87 ms** | 41.14 ms |
| rerank on | 20.16 ms | **41.87 ms** | 48.71 ms |

**+8 ms p95 against a 150 ms bar.** O(depth), not O(corpus): 20 documents are
read per query whatever the corpus size.

⚠ **Separately observed, not a regression from this work:** the *reference
scan* at 10 000 documents is **237 ms p95**, over the bar. Only the accelerator
path is inside it. That is what the Phase 0 `fux build` recommendation exists
for, and it is the first time the number has been written down.

## §5 · The differential law

240 accelerator-vs-scan comparisons — 12 queries × 4 depths × 5 weights
(0.0, 0.3, 1.0, 1.5, 3.0) — **0 divergent**. Both paths read the same live text
and agree byte for byte.

## §6 · Two defects found by using the features

**1. `fux ingest --full` could not perform the migration it documents.** See
D26 and ADR-INDEX-LIFECYCLE decision 10's amendment. Shipped in 1.0.0.

**2. `fux enrich --plan` printed a sha that could not be used.** It printed
`sha[:12]` while `validate()` compares the full value, so every enrichment
written by correctly following `ENRICH-SKILL.md` came back `STALE` — and the
message rendered as `STALE (was c84a92145ee9)` directly beneath
`sha c84a92145ee9`. The line whose only job is to show a difference showed two
identical strings. Fixed; ADR-ENRICH decision 11.

Both were found by *running the feature end to end as its own documentation
instructs*, not by a test. Neither had a failing test before or a passing one
that would have caught it.

## §7 · Verdict

**Phase 6 is built, measured and PASSES its gate** (failure rate on the
goldens, top-20 → top-5: 22 → 18 unenriched, 12 → 9 enriched), at a cost 18×
inside the latency bar, with the differential law intact and no new dependency.

**It ships `off` by default** — ADR-RERANK decision 7. The reason is a property
and not a hedge: the reranker reads the working tree, so its output is not a
pure function of the committed index.

**The cross-encoder is deferred with a price attached**, not rejected on
principle. ADR-RERANK veto 1 names the two conditions that reopen it.
