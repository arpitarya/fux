---
type: Compare Doc
title: Reopen the Cross-Encoder, or Confirm the Refusal — with the Literature Read
description: "W-78 ruling 1, with a literature review behind it. The 2021 BM25+CE number everyone quotes has never been re-run for a small cross-encoder; reranking falls BELOW retriever-only in ~half of measured configurations; the metadata alternative has a +32pp precedent on exactly this corpus type. Recommendation: CONFIRM, on a rewritten reason. UNRULED."
status: proposed
timestamp: 2026-08-24T00:00:00Z
---

# Reopen the cross-encoder, or confirm the refusal

> **UNRULED. This is Arpit's call** — [W-78](../open/W-78-enrichment-was-measured-against-its-own-answers.md)
> ruling 1. What follows is the evidence, the recommendation, and the two
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

1. **The value is unproven for corpora shaped like fux's.** The gains
   concentrate where the first stage is weak; fux's is strong. Reranking is
   measured to go *backwards* in roughly half of tested configurations.
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

- **§2's evidence is about IR benchmarks, not about a 10-document fixture.**
  Fux has never measured a cross-encoder on its own corpus at all. The
  recommendation is an argument from other people's corpora.
- **§3 could be underweighted.** If undeclared negation turns out to be
  common — and nobody knows — then confirming here defers a real capability on
  the strength of an unmeasured assumption, which is the exact error W-78
  documented.
