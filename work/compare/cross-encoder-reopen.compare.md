---
type: Compare Doc
title: Reopen the Cross-Encoder, or Confirm the Refusal — with the Literature Read
description: "W-78 ruling 1, with a literature review behind it. The 2021 BM25+CE number everyone quotes has never been re-run for a small cross-encoder; reranking falls BELOW retriever-only in ~half of measured configurations; the metadata alternative has a +32pp precedent on exactly this corpus type. Recommendation: CONFIRM, on a rewritten reason. UNRULED."
status: accepted
timestamp: 2026-08-24T00:00:00Z
---

# Reopen the cross-encoder, or confirm the refusal

> ## Verdict: condition 1 VACATED, condition 2 RESTATED, refusal STANDS — Arpit, 2026-08-25, on delegation
>
> **The recommendation below (§6, "confirm on a rewritten reason") was NOT
> taken, and the difference matters.** Its lead leg argues value from other
> people's corpora about a weaker model than the record specifies (§0c).
> **Condition 1 was vacated instead** — withdrawn, not replaced — because
> substituting a second unmeasured claim for the first is precisely the error
> W-78 documents. This record now holds **no position on the cross-encoder's
> value**, which is correct, because there is none.
>
> **Condition 2 was restated, not confirmed.** The `5e-10` bar was derived from
> `round(score, 9)`, which is not the binding constraint;
> [measurement](../regression/2026-08-25-rank-flip-susceptibility/report.md)
> puts the median adjacent gap at `0.27` and the flip rate at the quoted drift
> at **0.00 %**. The new bar is **score-level drift below the target corpus's
> adjacent-gap floor** — falsifiable, and unmet only because **nobody has
> measured the quantity**.
>
> **Reopen-trigger:** both of (1) score-level drift measured below that floor,
> and (2) value measured on the target corpus with its own goldens. ⚠
> **Undeclared negation is deliberately NOT a trigger** — it argues a problem
> exists, not that this is the solution.
>
> **Superseded framing below.** What follows was the evidence, the
> recommendation, and the two
> places the recommendation could be wrong.

## 0 · Two corrections to fux's own record, first

**0a. "`onnxruntime` is not byte-identical across x86-64 and arm64" is true but
the stated cause was too general.** Arm's own cross-platform guidance says
**basic IEEE-754 operations produce identical results on Arm and x86**. The
divergence [we measured](../regression/2026-08-24-crossarch-drift-and-declared-supersession/report.md)
comes from three things above the arithmetic layer:

1. **per-ISA GEMM microkernel selection** in onnxruntime's MLAS — different
   blocking and SIMD width, therefore different reduction order;
2. **FMA contraction** — one rounding step instead of two;
3. **libm** differences in `exp`/`erf`/`tanh` inside softmax and GELU.

None of the three is touched by `intra_op_num_threads=1` or by disabling graph
optimisations, which is why our most-deterministic configuration still
diverged. **The finding stands; the explanation is sharper.**

**0b. And it is worse than we said, in the useful direction.** onnxruntime
maintainers, asked by a CERN/ATLAS user for a reproducibility guarantee,
declined and suggested **~1e-5 absolute/relative** as acceptable tolerance.
Our measured `1.9e-06` sits **inside their tolerance**. The runtime is
behaving to spec while breaking fux's promise. `use_deterministic_compute`
exists but targets threading, not ISA — **it would not help.**

**0c. ⚠ THIS DOCUMENT ARGUED AGAINST THE WRONG MODEL, and Arpit caught it.**

Everywhere below that says *"a 22M MiniLM"* was **my gloss, not the record's**.
The record specifies neither MiniLM nor 22M. `ADR-RERANK` decision 1 quotes
W-76 Phase 6 as *"17–32 M cross-encoder"*, and
`proposals/ideal/README.md` (archived 2026-08-25) names the source:
**Ettin**, whose reranker line is **17.6M / 32.8M** — which is exactly where
the record's "17–32M" comes from.

**And Ettin was chosen precisely because it beats MiniLM.** Its authors report:

| model | params | MTEB Retrieval nDCG@10 | CPU (i7-13700K) |
|---|---|---|---|
| **Ettin-17M** | **17.6M** | **0.5576** | **267.4 pairs/s** |
| `ms-marco-MiniLM-L12-v2` | 33M | 0.5066 | — |
| `ms-marco-MiniLM-L6-v2` | — | — | 143.9 pairs/s |

**+0.051 nDCG at roughly half the parameters, and ~1.9x the CPU throughput.**

**What this changes:** §2's tables are `+MiniLM-L6` columns. They are therefore
evidence about a model **weaker than the one fux specified**, by its authors'
own claim. Leg 1 of the recommendation was argued at the wrong strength and is
restated in §6.

**What it does NOT change**, and this is the part that survives:

- The **distributional** findings in §2 are about *queries*, not about which
  reranker: ~40 % gain nothing, gains concentrate where the first stage is
  weak, rerankers fall below retriever-only in ~half of configurations. A
  better reranker moves the magnitude, not the shape.
- **Determinism.** Ettin ships as ONNX and runs on the same runtime. §0a and
  §0b apply unchanged.
- **The metadata alternative's +32 pts.**
- ⚠ **Ettin's numbers are self-reported by the model's authors on MTEB
  Retrieval** — not an independent BEIR re-run, and not on a SciFact-shaped
  corpus.

**And the latency is worse than it first looks.** 20 candidates at 267.4
pairs/s is **~75 ms**. Fux's measured p95 at 10 000 documents is **33.5 ms**
against R3's **150 ms** bar — so the specified reranker would consume **about
half the remaining headroom** on a machine at least as fast as an i7-13700K.
Cheap, not free.

---

## 1 · The claim the refusal was argued against

*"a 35 MB dependency targets the class enrichment already covers
deterministically and for free."* Enrichment does **not** cover that class
(W-78). So the question is open on the merits, and the merits are these.

## 2 · What reranking actually buys — and it is not the number in the folklore

**The canonical +4.2 nDCG@10 (BM25 0.421 → BM25+CE 0.463) is from BEIR, 2021.**
No 2025-26 study re-runs BEIR with a small (~20-30M) cross-encoder. The BEIR
leaderboard **deprecated its reranking sheet in January 2023**.

**Where the gains are concentrated matters more than their average.** An
ICTIR '26 adaptive-reranking study, reranking top-50 from BM25:

| dataset | BM25 | +MiniLM-L6 | note |
|---|---|---|---|
| MS MARCO | .220 | **.388** | BM25 weak — huge gain |
| FiQA | .238 | **.327** | BM25 weak — large gain |
| **SciFact** | **.658** | **.676** | **BM25 strong — +0.018** |
| NFCorpus | .314 | .330 | heavy reranker scored *worse* (.324) |

Same paper: **~40 % of queries benefit from reranking not at all**, and only
11 % benefit from a heavy reranker.

**A repo-documentation corpus with a strong lexical prior is a SciFact, not an
MS MARCO.** Fux's own playground sits at 32/50 before any reranking.

**And reranking is measured to go backwards.** Across 5 academic and 3
enterprise datasets, **53.3 % of academic and 44.4 % of enterprise experiments
had the reranker fall *below* retriever-only** at maximum K. Separately, with a
strong first stage (81.58 % nDCG@10) a 32B reranker **dropped it to 80.63 %**.

**The 2026 results that are genuinely large used 20B+ reasoning models or
commercial APIs**, not a MiniLM. On BRIGHT: BM25 0.148 → +20b rerank 0.267.
Nothing shows a 22M cross-encoder approaching that.

## 3 · The one strong argument FOR reopening: negation

It is real, severe and benchmarked. NevIR pairwise accuracy, **random = 25 %**:

| class | score |
|---|---|
| TF-IDF / sparse | **2.0 %** |
| SPLADEv2 | 8.0-8.7 % |
| dense bi-encoders | 6.8-11.1 % (best 2025: GritLM-7B 39.0) |
| ColBERT v1 / v2 | 19.7 % / 12.8 % |
| **cross-encoders** | **24.9-65.2 %** |
| listwise LLM rerankers | 11.3-77.0 % |

**Most retrievers score below random.** Cross-encoders are the only sub-LLM
class that clears it — which is a genuine, measured argument for the thing
this record refused.

**Three things blunt it.** Small cross-encoders sit at the *bottom* of that band
(MonoT5-**base** 34.9 %). Fine-tuning for negation **hurts general benchmarks**
and, of every family tested, **only one transferred** negation understanding
between two negation benchmarks. And the team that actually shipped strong
contradiction retrieval used **BM25 + a rule-based negation filter + NLI** —
2nd of 23 TREC submissions — which is a deterministic pipeline.

## 4 · The alternative, and it has a number on exactly this corpus type

**VersionRAG** handles version and deprecation with a **version graph plus
metadata-enhanced retrieval**, no neural scorer. On 34 versioned technical
documents (Apache Spark, Bootstrap, Node.js): **90 % accuracy vs standard RAG
58 % — +32 points**, and **60 % vs 0-10 %** on implicit change detection.

That is **five to fifteen times** the delta any small cross-encoder produced in
§2, on **versioned technical documentation**, with exact arithmetic. It is also
the same shape as what
[the 2026-08-24 run](../regression/2026-08-24-crossarch-drift-and-declared-supersession/report.md)
already demonstrated in miniature: declare the fact, weight it deterministically.

## 5 · Is determinism achievable if we wanted it? Nobody ships it

- **ReproBLAS** proves order-independent reproducible summation is real
  (binned floating point, ~4x single-core cost). Existence proof, not a
  transformer.
- **RepDL** (Microsoft Research, Oct 2025) is the only project claiming
  cross-platform bitwise-reproducible deep learning. **float32 only**,
  explicitly academic/non-production, publishes no overhead numbers, and its
  README **never mentions ARM or aarch64**.
- Everyone else who attacked determinism in 2025 scoped it to **identical
  hardware** — SGLang batch-invariant kernels (34 % slowdown), llama.cpp's
  deterministic CUDA mode (**still an unmerged draft**).
- **Integer-only is a real path in principle and unsupported in practice.**
  I-BERT showed integer-only transformers with no accuracy loss (2021) — but
  **LiteRT's 8-bit spec explicitly disclaims bit-exactness** across
  implementations, and **gemmlowp declines to commit** even on overflow
  behaviour. You would have to write and own the kernels.

## 6 · Recommendation — **CONFIRM the refusal, on a rewritten reason**

The old reason was *"enrichment already covers it, for free."* That is false.
Three replacement legs, each independently sufficient:

1. **The value is unproven for corpora shaped like fux's** — and this leg is
   **weaker than §2 makes it look**, because §2's numbers are MiniLM-L6 and the
   record specifies **Ettin-17M, which its authors measure at +0.051 nDCG over
   MiniLM-L12** (§0c). What survives the correction is the *shape*, not the
   magnitude: gains concentrate where the first stage is weak, fux's is strong,
   ~40 % of queries gain nothing, and reranking goes *backwards* in roughly
   half of tested configurations. **Nobody has run Ettin on a SciFact-shaped
   corpus, and nobody has run any reranker on fux's.**
2. **The determinism cost has no supplier.** Not one shipping runtime offers
   bit-exact cross-ISA inference, and the only project that claims it is
   float32-only, academic, and silent on ARM.
3. **The failure it was wanted for has a cheaper, deterministic fix with a
   larger measured delta** — declared metadata, +32pp on this corpus type.

**Record the new reason explicitly.** A veto standing on a dead argument is
what W-78 exists to prevent, and re-confirming without rewriting would repeat
the error at a different address.

## 7 · The reopening condition, stated so it can actually fire

Not *"if enrichment turns out to be weak"* — that has already happened and it
was not enough. Reopen when **either**:

- **someone measures that UNDECLARED negation is common** in a real corpus —
  *"this approach was abandoned"*, *"do not use X"*, phrasing no `supersedes:`
  key can capture. **Nobody has ever measured this**, in fux or in the
  literature; it is the single largest gap the review found. If the number is
  large, §3's argument returns and §4's fix does not reach it; **or**
- **a deterministic reranker becomes available** — bit-exact across x86-64 and
  aarch64, integer-only or reproducibly-summed. The bar is not *"small drift"*;
  `rank()` rounds to nine places, so it is **drift below 5e-10**.

## 8 · Where this recommendation could be wrong

- **§2's evidence is about IR benchmarks, not about a 10-document fixture**,
  **and it is about the wrong model** (§0c). Fux has never measured any
  cross-encoder on its own corpus. The recommendation is an argument from other
  people's corpora, about a weaker reranker than the one specified.
- **The cheapest thing that would settle leg 1 is to run Ettin-17M once**, on
  the playground's 50 goldens, offline, ignoring determinism entirely — purely
  to learn the number. It cannot ship, but it would replace *"unproven"* with
  a measurement, and §0c means the current argument is not entitled to assume
  the number is small.
- **§3 could be underweighted.** If undeclared negation turns out to be
  common — and nobody knows — then confirming here defers a real capability on
  the strength of an unmeasured assumption, which is the exact error W-78
  documented.
