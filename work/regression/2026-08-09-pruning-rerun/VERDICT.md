---
type: Verdict
name: P1-RERUN
title: P1-RERUN — the pruning-quality gate, re-run — FAIL
description: "The pruning gate, re-run on a corpus that can actually test it (8872 RFCs, median 967 distinct terms/doc), gated on recall@20 at matched retention. No selector comes within 2 points of the unpruned index at any retention rung; the best is 35.9 points short at 6%. Option E applies: full postings, permanently."
verdict: FAIL
prediction: P1
pre_registration: tools/pruning-eval/PRE-REGISTRATION-v2.md
timestamp: 2026-08-09T00:00:00Z
---

# P1-RERUN — the pruning-quality gate, re-run: **FAIL**

> **This is a verdict, not a decision record.** It was written as an ADR and
> converted on 2026-08-18, because it is not a decision anyone can supersede —
> it is the ruling of a pre-registered measurement against its frozen
> threshold. A verdict is **cited**, never replaced. It lives with its evidence.
>
> **This is the P1 measurement of record.** It supersedes
> [P1-GATE](../2026-08-09-pruning-eval/VERDICT.md) *as the measurement* —
> which is **not** modified, because it was a correct refusal and this run is
> the one it asked for.

- **Name:** `P1-RERUN` — cite this by name
- **Verdict:** **FAIL** — option E applies: the committed index carries full
  postings, permanently
- **Prediction under test:** **P1** — keeping only each document's top-k
  KL-ranked terms preserves ranking quality
- **Date:** 2026-08-09
- **Pre-registration (frozen before the first gating number):**
  [`../../../tools/pruning-eval/PRE-REGISTRATION-v2.md`](../../../tools/pruning-eval/PRE-REGISTRATION-v2.md)
  (commit `3892c55`)
- **Evidence:** [`evidence/`](evidence/) and [`ANALYSIS.md`](ANALYSIS.md), in
  this directory
- **The harness:** [`tools/pruning-eval/`](../../../tools/pruning-eval/README.md)
  — owned by [W-38](../../open/W-38-m8-deferred.md)
- **What now depends on this verdict:**
  [ADR-POSTINGS](../../../docs/adr/0013_postings.md) (postings are never
  pruned) and [ADR-INDEX-LIFECYCLE](../../../docs/adr/0009_index-lifecycle.md)

---
## Headline

**FAIL.** On a corpus that can actually exercise the treatment, **no selector
comes within 2 points of the unpruned index at any retention rung.** The best
arm at the 6 % budget the size model depends on is **35.9 points** short.

| | |
|---|---|
| gating corpus | **rfc** — 8 872 documents, median **967** distinct terms/doc |
| gate metric | recall@20, abstract-derived queries (n=703) |
| ceiling (no pruning) | **0.986** |
| best arm @ 6 % retention | arm 1 (KL) **0.627** → **−35.9 pts** |
| best arm @ 15 % | arm 1 **0.755** → −23.0 pts |
| best arm @ 30 % | arm 1 **0.859** → −12.7 pts |
| pre-registered bar | within **2 pts** |

This is not a marginal call. The gaps are 7–27× the sampling standard error
(1.3–1.9 pts), and every validity check passed.

## Context

[P1-GATE](../2026-08-09-pruning-eval/VERDICT.md) returned INCONCLUSIVE: its corpora had
32–46 distinct terms per document, so "keep the top 128" removed nothing and
the threshold was met by a treatment that never happened. It asked for three
things, and this run delivers all three:

1. **A corpus that can be pruned.** 8 872 RFCs, median 967 distinct terms per
   document (p90 1 850, p99 3 236) — the regime the paper's §5 size model
   assumes. A 6 % budget keeps 58 terms and discards **94 %**.
2. **The right metric.** The index is a *candidate generator*: Fux ranks,
   fetches the top-k, then re-scores passages on the fetched bytes. A document
   falling from rank 1 to rank 8 costs nothing, so the gate is **recall@20**,
   not the index's own hit@5.
3. **The right comparison.** Five arms at **matched retention**, because
   comparing criteria at a fixed *k* would repeat P1-GATE's error one level up.

## What was measured

One scorer (archived v0.26 BM25F, unmodified), five arms, three retention
rungs. Every arm's budget share was calibrated by binary search to land on its
rung; **all twelve gating cells matched within ±0.12 pts** of target.

### The gate

| arm | rules | 6 % | 15 % | 30 % |
|---|---|---|---|---|
| **5 — no pruning (ceiling)** | — | **0.986** | 0.986 | 0.986 |
| 1 — KL only | — | **0.627** | **0.755** | **0.859** |
| 2 — impact only | B | 0.489 | 0.615 | 0.774 |
| 3 — A + B | A+B | 0.209 | 0.340 | 0.521 |
| 4 — A + B + C *(the proposal)* | A+B+C | 0.208 | 0.354 | 0.531 |

*recall@20, abstract-derived slice, RFC. Standard error 1.3–1.9 pts.*

Pooled over both query kinds the picture is the same (ceiling 0.935; arm 1
0.661 / 0.775 / 0.849). The heading-derived slice — which flatters the
spine arms by construction, and was registered as diagnostic-only for exactly
that reason — does not change any ordering.

### Validity

| check | result |
|---|---|
| corpus gate (median ≥ 500 distinct terms) | **PASS** — 967 |
| corpus integrity | 8 872 documents, **0** sha256 mismatches |
| retention matched (±1 pt) | **all 12 cells**, worst error 0.12 pts |
| prune coverage at 6 % (VOID below 50 %) | **100 %** of documents |
| ceiling identity (100 % retention = no-op) | passes, per arm |
| determinism (reordering, term-iteration order) | asserted in 50 tests |

## The pre-registered prediction was wrong, and wrong in an informative direction

Recorded before the run, from
[`pruning-criterion.compare.md` §5](../../work/compare/pruning-criterion.compare.md):

> *"Arm 4 lands within noise of arm 5 on recall@20 at 6 % retention; arm 1 is
> the outlier."*

**Measured: arm 4 is 77.8 points below arm 5, and arm 1 — the criterion
P1-GATE implicated — is the best of the four at every rung.** Both secondary
expectations also failed: impact did *not* beat KL, and the heading spine did
not help.

The counter-signal recorded in the pre-registration (from the non-gating
`repodocs` smoke run, where arm 1 also beat arms 2 and 3) **reproduced on a
completely different corpus**. That it was written down in advance is why it
counts as evidence rather than hindsight.

**The compare doc's central hypothesis is falsified.** KL divergence is not the
defect; if anything it is the least-bad of the criteria tested. P1-GATE's
`webhook`-out-of-`webhooks.md` observation was a real symptom, but the
inference drawn from it — that a better criterion would recover the loss — does
not survive measurement.

## Why the loss happens

**The dominant mechanism is the eval's query workload, and it cuts both ways.**
Every failure in every catalogue is classified `term-pruned`, and the terms
being lost are ordinary: `a`, `b`, `and`, `or`, `on`, `low`, `storage`,
`space`, `references`, `information`. The queries are verbatim sentences of
8–16 tokens, so a document is only found if *that specific sentence's* terms
survive. At 6 % retention the median document keeps 58 of 967 terms, and an
arbitrary sentence's vocabulary is mostly not in that 58.

**This makes the eval close to a worst case for pruning, and that is a real
threat to the verdict's external validity** — see §Limitations. It is stated
here rather than in a footnote because it is the strongest argument against the
conclusion.

**Rule A damages retrieval *globally*, not in the documents it touches.** This
started as an apparent contradiction and became the run's most interesting
finding.

Arms 2 and 3 keep **identical postings for 93.4 %** of documents (mean
symmetric difference 0.877 terms out of 65.72 — plain-text RFCs give the
heading spine a median of **one** term), and only **28 of 393** gold documents
differ. Yet they score 27 points apart. No per-document story can explain that.

The decisive test: restrict to the **372 of 400 queries whose gold document
keeps byte-identical postings under both arms**.

| arm | recall@20 on that slice |
|---|---|
| 2 — impact only | **0.441** |
| 3 — A + B | **0.298** |

A 14-point loss on queries where the correct document's index entry *did not
change at all*. The damage is therefore entirely in the rest of the index: the
6.6 % of documents with large forced spines (up to 113 terms) keep
**heading-field** postings, which BM25F weights ×3.0. Those documents become
spurious high scorers across unrelated queries and push correct answers out of
the top 20.

Two other hypotheses were measured and **falsified**, which is how the search
narrowed to this one:

| hypothesis | measured | verdict |
|---|---|---|
| the unbounded spine swallows the budget | **1 document of 8 872**; spine = 0.13 % of vocabulary | falsified |
| impact ranking is heading-dominated | **1.65 %** of the top-6 % are heading terms (KL: 2.05 %) | falsified |

**The design lesson generalises beyond Rule A:** a pruning rule that forces
*heavily-weighted* postings into a minority of documents can degrade the whole
index, and a per-document evaluation would never see it. Any future rule needs
to be judged on corpus-wide ranking, not on what it does to the document it is
applied to.

**Scope limit, stated plainly:** RFCs give Rule A a one-term spine, so what
this measures is the behaviour of the *minority* of documents that do have
large headings. On a corpus of genuinely structured documents the spine would
be larger *and* more meaningful, and the sign of the effect could differ. Rule
A is **not** disproven — it is implicated, on one corpus, by a mechanism worth
testing deliberately.

## Decision

**FAIL against the pre-registered rule. Option E applies: do not build the
architecture on aggressive static pruning.**

Per the frozen rule, FAIL means: *the committed index is 0.6–1.5 GB; partial
clone and external-shards-only stop being optional levers and become mandatory;
`storage-architecture.compare.md` takes a size amendment rather than a reopen.*

**What this does and does not falsify.** It does **not** falsify
index-and-refer. Ranking from a committed index and fetching content from
source systems is untouched — what fails is the claim that the index can be
made ~16× smaller *by discarding postings* without losing candidate recall. The
architecture survives at a larger committed size.

**W-01 (the M0b scaffold) does not unblock**, because the pre-registered PASS
condition was not met. Whether to proceed at option E's size is Arpit's call,
not a consequence the measurement licenses on its own.

## Consequences

**Immediate:**

- `pruning-criterion.compare.md` → **amended, not accepted**: its prediction is
  falsified and its selector is untested (see the withdrawal above).
- The paper's **§5 size model must be re-derived** at a retention that holds
  quality, or at no pruning. Its ~6 % assumption is now *measured as
  quality-destroying* on the one corpus able to test it — a stronger statement
  than P1-GATE's "unvalidated". Paper edits are M7's, but the flag is owed now.
- **`storage-architecture.compare.md` takes a size amendment.** Its reopen
  trigger ("P1 fails at k=128") has technically fired; the verdict itself
  (index-and-refer) is not what failed, so the honest action is an amendment
  recording the larger committed footprint.
- P1-GATE gains a one-line forward pointer and is otherwise **unmodified**.

**What we now owe, in priority order:**

1. **Re-measure with a realistic query workload.** The single most likely way
   this verdict is too harsh (see §Limitations 1). Needs its own
   pre-registration; it is the highest-value follow-up available.
2. **Test Rule A on a corpus with real headings**, judged corpus-wide rather
   than per-document. RFCs gave it a one-term spine, so it is implicated but
   untested.
3. **Re-budget the size model** at whatever retention survives, or at 100 %.

**What got cheaper:** the corpus (8 872 RFCs, manifest-pinned), the harness, the
retention-matching machinery and the selector are all reusable. A follow-up is a
new query set and a new threshold file.

## Limitations — stated before anyone has to ask

1. **The query workload is close to a worst case.** Queries are verbatim
   sentences from the document, averaging 8–16 tokens including function words.
   Real agent queries are short and *salient* — "why did we choose goods-to-person
   AMRs" — made of exactly the discriminative terms pruning is designed to keep.
   **A keyword-style workload could plausibly move these numbers a long way**,
   and no part of this run tests that. It is the first thing a follow-up should
   measure, and it is why the recommendation is "re-budget", not "abandon".
2. **Known-item, not judged relevance.** No human relevance judgments exist for
   these corpora; gold is the source document.
3. **One gating corpus.** `repodocs` (median 425), `acme` (32) and `orbit` (36)
   all failed the corpus gate. RFCs are technical specifications — plausibly
   close to enterprise documentation in register, but it is one register.
4. **RFCs have no Markdown headings**, so Rule A is nearly inert on this corpus
   (median spine: 1 term). What the run measures is the effect of the *minority*
   of documents that do carry large headings; the rule itself is implicated but
   not tested at the scale it was designed for.
5. **Document-level impact** (a document's field counts aggregated over its
   chunks), because production prunes a document's entry, not a chunk's.
6. Lexical only; `δ ∈ {1,2,3}`, `floor = 8`, three rungs. No wider sweep.

## Alternatives considered

| option | why it lost |
|---|---|
| **Report PASS or PARTIAL** | Nothing is within 2 pts at any rung. The nearest result is 12.7 pts short at a retention (30 %) that only shrinks the index ~3×, not ~16×. |
| **Move the gate to 30 % retention and call it PARTIAL** | Threshold-moving after seeing numbers. PARTIAL was pre-registered as "within 2 pts at 15 % or 30 %" — 12.7 pts does not qualify. |
| **Blame the query workload and withhold a verdict** | The workload concern is real (§Limitations 1) but was knowable in advance and *was* declared in the pre-registration. Refusing to call a pre-registered measurement because its result is unwelcome is the failure mode the pre-registration exists to prevent. It is recorded as a limitation and as the first follow-up. |
| **Report the arm 2/3/4 ordering without the mechanism** | The ordering alone would have implied "Rule A is bad", when the measured mechanism is narrower and more useful: forced heavily-weighted postings in a *minority* of documents degrade the *whole* index. Reporting the number without the mechanism would have been true and misleading. |
| **Declare VOID** | Every VOID condition was checked and none fired: corpus gate passed, coverage 100 %, retention matched. The run is evidence. |

## References (required)

- **The pre-registration**, frozen before the first gating number —
  [`tools/pruning-eval/PRE-REGISTRATION-v2.md`](../../tools/pruning-eval/PRE-REGISTRATION-v2.md).
- **The prior refusal this run answers** — [P1-GATE](../2026-08-09-pruning-eval/VERDICT.md).
- **The design under test** —
  [`../../work/compare/pruning-criterion.compare.md`](../../work/compare/pruning-criterion.compare.md).
- **Corpus:** RFC Editor, `https://www.rfc-editor.org/rfc-index.txt` and
  `rfc{n}.txt`; 8 872 documents pinned by sha256 manifest, acquired once by
  `tools/pruning-eval/fetch_rfc.py`.
- **Büttcher, S., Clarke, C.** *A Document-Centric Approach to Static Index
  Pruning.* CIKM 2006 — https://dl.acm.org/doi/10.1145/1183614.1183684 (arm 1).
- **Carmel, D. et al.** *Static Index Pruning for Information Retrieval
  Systems.* SIGIR 2001 — https://dl.acm.org/doi/10.1145/383952.383958 (arm 3's
  term-centric backstop).
- **Altingovde, Ozcan, Ulusoy.** *Static Index Pruning in Web Search Engines.*
  TOIS 30(1), 2011 — https://dl.acm.org/doi/10.1145/2094072.2094074 (the
  "combinations ≈ 2× single criteria" result this run does **not** reproduce).
- **Mackenzie, J. et al.** *Revisiting Document Expansion and Filtering for
  Effective First-Stage Retrieval.* SIGIR 2024 —
  https://jmmackenzie.io/pdf/mzzm24-sigir.pdf (the basis for gating on
  recall@20 rather than hit@5; its "no significant differences after re-ranking"
  finding is **not** reproduced at these retention levels on this workload).
- **On pre-registration as a defence against outcome-dependent analysis:**
  Nosek, B. et al., *The preregistration revolution*, PNAS 115(11), 2018 —
  https://doi.org/10.1073/pnas.1708274114.
