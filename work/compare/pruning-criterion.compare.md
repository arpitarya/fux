---
type: Compare Doc
title: Pruning Criterion
description: What decides which postings the committed index keeps — KL top-k (tested, inconclusive), impact-ranked, term-centric, or a combined rule set under an adaptive retention budget.
status: proposed
timestamp: 2026-08-09T00:00:00Z
---

# Pruning criterion — Comparison

> **Verdict (proposed): a combined three-rule selector under an adaptive
> retention budget, gated on candidate recall rather than index hit@5.**
> **A** always keep title/heading terms · **B** fill the document's budget
> by max BM25F impact · **C** sweep per-term and force-keep each term in its
> top-δ best-matching documents. Budget = `max(floor, share × vocabulary)`,
> not a constant k. Gate metric = **recall@20 of the candidate set**, because
> the index feeds a fetch-and-re-score stage and is a candidate generator,
> not the final ranker.
> **Status:** ❌ **AMENDED — the verdict above is falsified. Do not implement
> it.** Measured 2026-08-09 on 8 872 RFCs (median 967 distinct terms/doc):
> at 6 % retention the proposed selector (arm 4) scores **0.208** recall@20
> against an unpruned ceiling of **0.986** — 77.8 points down, where the
> pre-registered bar was 2. **No arm came within 2 points at any retention
> rung**, so the fallback in §Consequences ("if it fails at 6 %") applies in
> full: option E. See [P1-RERUN](../regression/2026-08-09-pruning-rerun/VERDICT.md).
>
> **The prediction failed in both halves.** Arm 4 was predicted to land within
> noise of no-pruning; it was the worst arm. Arm 1 (KL) was predicted to be the
> outlier; it was the **best** arm at every rung. KL divergence is not the
> defect this document diagnosed it as.
>
> **What survives:** the *reframe* was right and is kept — recall@20 of the
> candidate set is the correct metric for an index that feeds a re-score stage,
> and matched retention is the correct axis. Both are carried into any
> follow-up.
>
> **What is untested rather than disproven:** Rule A had a *one-term* spine on
> RFCs (plain text has no headings), so the three-rule selector was never
> exercised as designed. It is nonetheless *implicated* — see P1-RERUN's
> competition finding.
> **Reopen when:** a realistic (short, keyword-style) query workload is
> measured — the strongest remaining argument that the verdict is too harsh.

---

## §1 · For humans — the short version

The first attempt kept "each document's best 128 terms by KL divergence."
[P1-GATE](../regression/2026-08-09-pruning-eval/VERDICT.md) found the measurement couldn't
test that claim — the eval documents have 32–46 distinct terms, so keeping
128 removed nothing. But the one setting that *did* bite (k=64) exposed a
real defect in the criterion itself: KL divergence rewards terms that are
rare **across the collection**, so in a corpus where every document is about
payments, the word `payments` looks uninformative and gets discarded. The
run literally dropped `webhook` from `docs/api/webhooks.md`.

That is a structural mismatch with Fux's design point (a large, topically
homogeneous corporate corpus), not bad luck. Three changes follow:

1. **Rank terms by what the scorer actually uses** — max BM25F impact —
   rather than by divergence from the collection.
2. **Never let a term lose all its best documents.** A per-term sweep after
   per-document selection fixes the `webhooks.md` class of failure by
   construction: it asks "which documents best match `webhook`?" and keeps
   those postings regardless of each document's own budget.
3. **Stop measuring the wrong thing.** Fux ranks in the index, fetches the
   top-k, then re-scores passages on the fetched bytes. A document dropping
   from rank 1 to rank 8 costs nothing — it is still fetched and re-scored.
   The metric that matters is whether the right document reaches the
   candidate set, i.e. recall@20, not the index's own hit@5.

Point 3 is the one that may dissolve the whole problem, and it is free.

## §2 · Context

The committed index is only small if most postings can be discarded
(paper §5: ~6 % term retention gives ~115 MB of postings at 10⁶ documents;
no pruning gives roughly 0.6–1.5 GB). The criterion decides *which* 6 %.

Prior evidence, in order of weight:

- **Combinations beat single criteria.** The Bilkent comparative study finds
  the combined strategy (term popularity + document access + query views)
  roughly **twice as effective** as the best single strategy at 90 %
  pruning. Single-criterion pruning is a baseline, not a design.
- **Which axis you prune matters, and depends on query semantics.** Same
  study: term-centric pruning beats document-centric for **disjunctive**
  queries (0.14 vs 0.20 symmetric difference at 90 % pruning) and loses
  badly for conjunctive ones (0.04 vs 0.43). Fux's BM25F path is
  disjunctive — which is the opposite of what M1 implemented.
- **Multi-stage pipelines absorb recall loss.** Mackenzie et al. report that
  pruning's recall reductions produced "no significant differences" in final
  results once a re-rank stage runs. Fux *is* such a pipeline.
- **Signatures are a speed win, not a space win.** BitFunnel measures
  11.69 bits/posting on long documents against partitioned Elias-Fano's
  6.15 — so a "keep everything in a Bloom plane" safety net costs *more*
  than the postings it protects (~2.4 KB/doc at 2 000 terms ≈ 2.4 GB at
  10⁶ docs). Ruled out on arithmetic, not on taste.

## §3 · Options

- **A — KL top-k, per document** (what M1 built): Büttcher–Clarke
  document-centric. Simple; measured inconclusive; structurally penalizes a
  homogeneous corpus's subject terms.
- **B — Impact-ranked, per document**: rank by max BM25F contribution.
  Optimizes the deployed objective directly; still per-document, so it can
  still orphan a term.
- **C — Term-centric**: keep each term's top-δ documents (Carmel et al.).
  Better for disjunctive queries; no per-document size guarantee, so a
  document can end up with nothing.
- **D — Combined A/B/C under an adaptive budget** *(verdict)*: heading floor
  ∪ impact-budget ∪ per-term backstop, budget =
  `max(floor, share × vocab)`.
- **E — No pruning**: commit every posting; ~0.6–1.5 GB; the quality
  ceiling and the fallback.
- **F — Learned sparse (SPLADE/DeepImpact/doc2query)**: strictly better
  term weighting, requires a model at ingest → AI-assisted tier only, never
  the $0 default. Out of scope here, noted so it isn't re-proposed.

## §4 · Matrix

| criterion (weight) | A KL | B impact | C term-centric | **D combined** | E none |
|---|---|---|---|---|---|
| keeps subject terms in a homogeneous corpus (H) | **no** | partly | yes | **yes** | yes |
| per-document floor guaranteed (H) | yes | yes | **no** | yes | yes |
| fits disjunctive BM25F (H) | weak | good | **best** | best | n/a |
| committed size @1M (H) | ~115 MB | ~115 MB | ~115 MB | ~115 MB | **0.6–1.5 GB** |
| implementation cost (M) | done | small | small | small (three rules over one pass + one sweep) | none |
| measured on Fux corpora (H) | inconclusive | no | no | no | no |

## §5 · The decided experiment

Five arms, **matched retention** (6 %, 15 %, 30 %), on a long-document
corpus, pre-registered before the first number:

| arm | rules | question it answers |
|---|---|---|
| 1 | KL only | continuity with P1-GATE |
| 2 | impact only | is KL the defect, or pruning itself? |
| 3 | A + B | does the heading floor alone fix it? |
| 4 | **A + B + C** | the proposed selector |
| 5 | no pruning | the quality ceiling / fallback |

**Primary gate metric: recall@20** of the candidate set (the set that would
be fetched and re-scored). Secondary, diagnostic only: recall@50, hit@5,
P@10, MRR, the rare-term slice, per-pruned-document slices.

**Pre-registered prediction (recorded before running):** arm 4 lands within
noise of arm 5 on recall@20 at 6 % retention; arm 1 is the outlier. Stating
it up front so a miss is visible as a miss.

## §6 · Consequences

**If the verdict holds.** The selector is three cheap rules over one pass
plus one global sweep; the paper's §5 size model stands; M2 unblocks. The
"pruning" vocabulary in the paper and PLAN should be amended to name the
combined rule, not KL.

**If it fails at 6 %.** Walk the retention rungs to find where arm 4 meets
arm 5 and re-budget the size model at that point. If no useful retention
survives, option E applies: the committed index is 0.6–1.5 GB, partial
clone and external-shards-only stop being optional levers and become
mandatory, and
[`storage-architecture.compare.md`](storage-architecture.compare.md) takes
a size amendment rather than a reopen.

**Either way**, P1-GATE's settled findings stand: k=64 as a global constant
is refused, and rare-term loss is not the dominant failure mode.

## §7 · For AI agents — implementation contract

```
select(doc, collection_model, budget_share, floor, delta) -> set[term]

budget      = max(floor, ceil(budget_share * |distinct terms in doc|))
Rule A      spine   := terms occurring in title or any heading field
Rule B      body    := top (budget - |spine|) remaining terms by
                       max_impact(t, d) = BM25F contribution of t in d
                       at that field's weight, using PRUNED corpus stats
kept(d)     := spine ∪ body                      # per-document pass
Rule C      for each term t: for each of the top-δ documents by
                       max_impact(t, ·) not already keeping t, add t
                       # global sweep, runs AFTER every document's pass
```

Binding constraints, carried from P1-GATE and repo law:

- **Corpus statistics (`df`, `n`, field-length sums) are recomputed over the
  final kept postings**, after Rule C. Rule C changes df, so the sweep runs
  before statistics, and statistics are never borrowed from the unpruned
  index. Getting this wrong measures a system nobody ships.
- **Rule C is order-independent**: iterate terms in sorted order, break
  impact ties on doc id. Same corpus → identical kept set.
- **Retention is reported, not assumed**: every run emits actual retention
  and prune coverage per corpus. A run where coverage is near zero is void
  by construction (the P1-GATE lesson, now a harness invariant).
- **Impact uses the pruned index's own statistics** in the final build, but
  the *selection* pass necessarily uses the unpruned collection model —
  document this as a two-pass build, not as an inconsistency.
- Pure function, stdlib only, portable into `src/fux/ingest/` unchanged.

## §7a · Worked examples — what the index actually looks like

*Illustrative reconstructions of the failure [P1-GATE](../regression/2026-08-09-pruning-eval/VERDICT.md)
recorded, in the committed-index row format (`L/ P/ D/ V/ E/ M/`). The
failure itself is measured; the surrounding term scores are plausible
fill, not measured output. An executing agent should be able to check its
own output against these shapes.*

### Example 1 — `docs/api/webhooks.md`: the documented failure

96 distinct terms; the k=64 budget keeps 64.

**Before — KL top-64, per document**

```
M/ doc 41   title: "Webhooks"   phrases: ["retry backoff","signature verify"]
P/ kept 64 terms, ordered by KL score:
   exponential  tf=2   KL 0.089   ← df=3, rare in corpus → survives easily
   idempotency  tf=6   KL 0.071
   backoff      tf=4   KL 0.066
   ...
   signature    tf=9   KL 0.012   ← rank 61, just inside
   ─────────────── cut at 64 ───────────────
   webhook      tf=18  KL 0.009   ← rank 71. DROPPED.
   payload      tf=11  KL 0.007   ← DROPPED
   endpoint     tf=8   KL 0.006   ← DROPPED
```

`webhook` carries the document's highest term frequency and is cut, because
it occurs in ~40 % of an API corpus: `P(t|C)` is large, so the KL ratio is
modest. The criterion is behaving exactly as specified — the specification
is wrong for a homogeneous corpus.

**After — A + B + C at the same retention**

```
P/ doc 41, budget = max(30, 0.06 × 96) → floor applies → 30 terms
   [A spine — from H1 "Webhooks", H2 "Webhook payload", H2 "Retry backoff"]
     webhook     tf=18  impact 7.9   ← Rule A. Cannot be pruned.
     payload     tf=11  impact 5.2
     retry       tf=7   impact 4.8
     backoff     tf=4   impact 3.9
   [B budget — top 25 remaining by max BM25F impact]
     signature   tf=9   impact 4.4
     idempotency tf=6   impact 3.7
     endpoint    tf=8   impact 3.5
     ...
   [C backstop — nothing to add; doc 41 already keeps every term it leads]
   actual retention: 30/96 = 31 %
```

The corrected index keeps **fewer** terms than the broken one and is still
right — the failure was never about quantity.

### Example 2 — a long document, where the treatment is real

An RFC-scale document at 1 850 distinct terms — the case the current eval
corpora cannot produce at any k.

```
Before (k=128, fixed)          After (6 % retention, A+B+C)
──────────────────────         ─────────────────────────────
kept 128 / 1850 = 6.9 %        budget = max(30, 0.06 × 1850) = 111
all chosen by KL                 A spine   : 38 terms (headings)
                                 B budget  : 71 terms (top impact)
                                 C backstop:  5 terms (this doc leads them)
                                 ─────────────────────────
                                 kept 114 / 1850 = 6.2 %
```

Two readings. On long documents fixed-k and retention land in nearly the
same place, so the adaptive budget costs nothing here — it matters on
*short* documents, where fixed-k silently became a no-op. And **Rule C can
exceed the budget** (114 > 111): this is why every run must report *actual*
retention and tune δ until arms match, or the combined arm wins merely by
keeping more.

### Example 3 — the term's view, where Rule C earns its place

Rules A and B are per-document; only C reasons across documents.

**Before — postings for `webhook` after doc-centric pruning**

```
D/ blake2b64("webhook") → offset 0x2a4f, df=340
P/ webhook → [ doc 7,  doc 19,  doc 88,  doc 402, ... ]
             ↑ survivors are incidental — short documents whose 64-term
               budget happened to cover everything they had
             ✗ doc 41 (webhooks.md)       — dropped by its own budget
             ✗ doc 55 (webhook-retry.md)  — dropped by its own budget
             ✗ doc 90 (webhook-security)  — dropped by its own budget
```

Every document *about* webhooks is missing and every survivor is a passing
mention. `webhook retry policy` sent webhooks.md from rank 5 to rank 88.

**After — Rule C sweeps per term**

```
P/ webhook → [ doc 41*, doc 55*, doc 90*, doc 7, doc 19, ... ]
                  ↑ the δ best-matching documents by impact, force-kept
                    even where each document's local budget said no
             * added by the backstop sweep
D/ blake2b64("webhook") → df=343   ← recomputed AFTER the sweep
```

That `df=343` is the constraint §7 makes binding: the sweep adds postings,
which changes document frequency, so statistics are computed after it.
Computing them before scores a corpus that does not exist.

### What changed structurally

The old index asked each document one question in isolation — *which of my
terms are unusual?* The new one asks three: what the document **announces**
it is about (headings), what will **actually score** (impact), and which
documents a term most **needs** (the global sweep) — under a budget that
scales with the document.

And the metric moved with it: `webhook` at rank 8 rather than rank 1 is now
a pass, because the document still enters the fetch set and is re-scored on
its real text. Only rank 88 is a failure.

## §8 · References

- Büttcher, S., Clarke, C. *A Document-Centric Approach to Static Index
  Pruning.* CIKM 2006 — https://dl.acm.org/doi/10.1145/1183614.1183684
  (option A, implemented in M1).
- Carmel, D. et al. *Static Index Pruning for Information Retrieval
  Systems.* SIGIR 2001 — https://dl.acm.org/doi/10.1145/383952.383958
  (option C, the term-centric backstop).
- Altingovde, Ozcan, Ulusoy. *Static Index Pruning in Web Search Engines:
  Combining Term and Document Popularities with Query Views.* TOIS 30(1),
  2011 — https://dl.acm.org/doi/10.1145/2094072.2094074 ·
  https://www.cs.bilkent.edu.tr/tech-reports/2011/BU-CE-1103.pdf
  (combinations ≈ 2× single criteria; the TCP/DCP disjunctive-vs-conjunctive
  reversal; and the query-views idea filed as
  [`../proposals/query-log-pruning.md`](../proposals/query-log-pruning.md)).
- Mackenzie, J. et al. *Revisiting Document Expansion and Filtering for
  Effective First-Stage Retrieval.* SIGIR 2024 —
  https://jmmackenzie.io/pdf/mzzm24-sigir.pdf (multi-stage pipelines absorb
  recall loss — the basis for the recall@20 gate metric).
- Goodwin, B. et al. *BitFunnel: Revisiting Signatures for Search.* SIGIR
  2017 — https://dl.acm.org/doi/10.1145/3077136.3080789 ·
  https://danluu.com/bitfunnel-sigir.pdf (signatures priced out as a
  recall-insurance plane: 11.69 vs 6.15 bits/posting).
- Internal: [P1-GATE](../regression/2026-08-09-pruning-eval/VERDICT.md) (the inconclusive
  result and the failure catalogue this doc responds to) ·
  [paper §5, §8](../paper/the-fux-index-paper.md) ·
  [`storage-architecture.compare.md`](storage-architecture.compare.md).

## §9 · Reopen-trigger

See the verdict block. First measurement that can fire it: the M1 re-run.
