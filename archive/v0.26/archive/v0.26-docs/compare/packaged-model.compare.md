---
type: Compare Doc
title: Packaged Model (≤10 MB, no external service)
description: Bundled static-embedding model, distilled offline, pure-stdlib inference (numpy resolved out); extractive-only synthesis.
status: accepted
timestamp: 2026-07-21T00:00:00Z
---

# Packaged Model (≤10 MB, no external service) — Comparison

> **Verdict:** **Ship a bundled static-embedding model (Model2Vec / "Potion"-class),
> distilled offline and quantized to ≤10 MB, with **pure-stdlib inference — no numpy
> anywhere on the runtime path** (resolved below).** Use it for semantic retrieval (engine v2) and
> for **extractive** answer synthesis (output v3). Do **not** attempt a from-scratch
> *generative* model — a ≤10 MB model cannot write reliable prose; "synthesis without
> an LLM" means *selecting and ordering the source's own sentences*, not generating
> new text.
> **Status:** ✅ Accepted (Arpit, 2026-07-20) · **Confidence:** Medium-High ·
> numpy sub-decision **resolved: stdlib-only** (see "Resolved — no numpy" below).

## Context

Arpit's constraint: **no external model or service** — but a model *built and packaged
inside this package* is allowed, if it's small (≤10 MB) and dependency-light, and runs
internally when a CLI command fires. Two jobs want a model: (1) semantic retrieval for
paraphrase (engine v2), (2) "synthesize and answer without an LLM" (output v3). This
doc settles **what kind of model is actually feasible in ≤10 MB**, and separates the
part that's realistic (semantic *selection*) from the part that isn't (fluent
*generation*).

## What's feasible in ≤10 MB (researched)

- **Static / distilled embeddings are the sweet spot.** Model2Vec distills a
  sentence-transformer into a table of one fixed vector per token; inference is just
  *tokenize → look up token vectors → mean-pool* — no neural forward pass, ~500× faster
  than the teacher on CPU. The **Potion** family: `potion-base-8M` ≈ **8–10 MB on
  disk**, `potion-retrieval-32M` (best static retrieval, ≈ 82 % of MiniLM's retrieval
  quality) ≈ 30 MB. So a **≤10 MB retrieval-usable static model exists today**, and we
  can hit the budget precisely by trimming vocab and **int8-quantizing** the matrix
  (≈4× smaller than float32).
- **"From scratch, as part of the package"** = we run the distillation **offline at dev
  time** (heavy toolchain, allowed as build/dev tooling), then **bundle only the
  resulting vector table + tokenizer** in the wheel. At runtime there is no training,
  no download, no service — just a lookup table the CLI loads. That satisfies "built
  and packaged inside; runs internally on CLI trigger."
- **Generation is not feasible in ≤10 MB.** A model that small cannot produce coherent,
  faithful open-domain answers; it would hallucinate. This is the honest limit.

## The two jobs, and how the bundled model does them

### Job 1 — semantic retrieval (engine v2)
Embed each chunk (offline, cached alongside the ingest cache) and the query; cosine-rank;
fuse with BM25F via RRF. The static model is enough here — retrieval only needs *good
enough relative ordering*, which Potion-class models deliver.

### Job 2 — answer synthesis **without an LLM** (output v3)  →  *extractive*
This is the key reframing. "Synthesize an answer" with a tiny bundled model means
**extractive synthesis**, not generation:
1. Retrieve the top passages (engine).
2. Split into sentences; score each by **semantic similarity to the question** (bundled
   embeddings) blended with **centrality** (TextRank/LexRank — a PageRank-style graph
   over sentences, pure algorithm, no model).
3. Select and order the best 2–4 sentences into a compact answer, each carrying its
   source `file:line`.

The result reads like a short answer, is **100 % traceable to source text**, is
**deterministic**, hallucinates nothing, and needs **no generative model**. It won't
paraphrase or fuse ideas into new wording the way an LLM does — that's the trade for
zero-hallucination and offline `$0`.

## Options

- **A — Bundled static embeddings + TextRank extractive answers.** *(verdict)*
- **B — Bundled tiny generative LM (≤10 MB) for abstractive answers.** Rejected —
  incoherent/hallucinatory at that size.
- **C — No bundled model; BM25F + TextRank only.** Viable, fully stdlib, but weaker
  paraphrase handling than A. Good fallback if the dependency question below goes
  "stdlib-only, no exceptions."

## Comparison matrix

| Criterion (weight) | A: Static embed + extractive | B: Tiny generative | C: BM25F + TextRank |
|--------------------|------------------------------|--------------------|---------------------|
| ≤10 MB feasible (H, hard) | ✓ (~8 MB) | ✓ size / ✗ quality | ✓ (no model) |
| No external service (H, hard) | ✓ | ✓ | ✓ |
| Answer faithfulness (H) | High (extractive) | Low (hallucinates) | High (extractive) |
| Paraphrase handling (M) | Good | — | Weak |
| Determinism (M) | Full | Poor | Full |
| Runtime deps (M) | numpy optional | heavier | **none** |
| **Fit** | **Verdict** | Rejected | Stdlib-purist fallback |

## Resolved — no numpy. Pure stdlib inference. (Arpit, 2026-07-20)

Arpit asked: *what if I do not use numpy?* Answer: **it works, and at our scale the
cost is acceptable.** What inference actually is, without numpy:

- **Embedding a query** = tokenize → look up each token's vector in the bundled table
  → average them. For a 10–30-token query over 256 dims that's a few thousand float
  ops — microseconds even in pure Python.
- **Ranking** = one dot product per chunk vector. Pure-Python dot products run roughly
  1–5 M multiply-adds/sec; at 256 dims that's ~4–20 k chunks/sec. A corpus of 10 k
  chunks ranks in **~0.5–2.5 s** worst-case — noticeable but fine for a CLI; 1 k chunks
  is instant.
- **Chunk embeddings are precomputed at ingest** (the slow part happens once, offline,
  where seconds don't matter) and stored in the cache — query time only embeds the
  question and ranks.

Mitigations that keep stdlib fast enough, in order of value: store vectors as int8 in
`array`/`bytes` (4× smaller, faster to walk); rank only the BM25F candidate set
(top 100–200) instead of the whole corpus — RRF needs only the candidates anyway,
which cuts the dot products by ~50×; `math.fsum`-free tight loops; optionally
`memoryview` slicing. With candidate-only ranking, pure-stdlib query latency is
**single-digit milliseconds** — the numpy question stops mattering.

**Verdict: stdlib-only inference, no numpy anywhere on the runtime path.** The
zero-dependency promise stays intact and unqualified. (Upstream Model2Vec's *library*
needs numpy — we don't ship their library; we ship the distilled table and ~200 lines
of our own lookup/mean-pool/dot-product code. The heavy distillation toolchain remains
dev-time only.)

### Follow-up resolved — can we vendor numpy as internal files? (Arpit, 2026-07-21)

Arpit asked whether, since numpy is open source, we could copy its files into the
package as internal modules and resync each build. **No — and here's the proof, not
just the assertion:**

- **numpy is not Python files.** Its core is C (and historically Fortran-interfacing)
  extension modules compiled per platform. Python's own packaging guide is explicit
  that such binary extensions use low-level CPython/OS interfaces "that cannot be
  achieved with pure Python alone" — there are no `.py` files to copy that would do
  the work.
- **The binaries are platform-locked.** A built numpy wheel "will not install or work
  on a different platform or Python version," and relies on external shared libraries
  (BLAS/LAPACK, compiler runtimes) that must be bundled per-OS with `auditwheel` /
  `delocate` / `delvewheel`. Vendoring means shipping and maintaining a compiled
  binary per OS × architecture × Python version — a build farm, not a resync script.
- **It would blow the budget and the promise.** Each platform's compiled payload is
  multi-MB before BLAS, versus our entire model budget of 10 MB — and shipping opaque
  compiled binaries inside Fux would quietly break the auditability/air-gap story the
  `$0` law exists to protect.

**"Do what is best" = the already-resolved answer stands:** pure-stdlib inference.
The math above shows candidate-only ranking makes numpy unnecessary at our scale —
we'd be paying the vendoring cost for speed we don't need.

## References

- Internal: [`../../CLAUDE.md`](../../CLAUDE.md) — the no-external-model / dependency constraints; [`query-engine.compare.md`](query-engine.compare.md), [`query-output.compare.md`](query-output.compare.md) — the two consumers.
- External: [Model2Vec — GitHub (MinishLab)](https://github.com/MinishLab/model2vec) — distillation to static embeddings; inference = token lookup + mean-pool; numpy dep (accessed 2026-07-20).
- External: [potion-base-8M — Hugging Face](https://huggingface.co/minishlab/potion-base-8M) — ~8–10 MB static model that fits the budget (accessed 2026-07-20).
- External: [potion-retrieval-32M — Hugging Face](https://huggingface.co/minishlab/potion-retrieval-32M) — best static *retrieval* model (~30 MB) as the distillation target to shrink from (accessed 2026-07-20).
- External: [Erkan & Radev, 2004 — LexRank](http://www.cs.cmu.edu/afs/cs/project/jair/pub/volume22/erkan04a-html/erkan04a.html) — graph-centrality extractive summarization for Job 2 (accessed 2026-07-20).
- External: [Extractive vs Abstractive Summarization — experimental review](https://www.mdpi.com/2076-3417/13/13/7620) — why extractive stays faithful/traceable without an LLM (accessed 2026-07-20).
- External: [Packaging binary extensions — Python Packaging User Guide](https://packaging.python.org/en/latest/guides/packaging-binary-extensions/) — why C-extension packages can't be "copied in" as pure Python (accessed 2026-07-21).
- External: [NumPy — building redistributable binaries](https://numpy.org/devdocs/building/redistributable_binaries.html) — platform-locked wheels, BLAS/LAPACK shared-library bundling via auditwheel/delocate/delvewheel (accessed 2026-07-21).

## Additional things to look into

- **Size lever math:** on-disk ≈ vocab × dims × bytes/weight. Trim vocab + int8 quantize
  to guarantee ≤10 MB; record the exact recipe so the build is reproducible.
- **Distill our own vs ship Potion:** shipping `potion-base-8M` is fastest; distilling a
  domain-tuned model on Anton/dev docs may beat it at the same size — measure before
  committing.
- **Embedding cache:** store chunk vectors next to the ingest cache; re-embed only on
  source change (ties into the ingest manifest).
- **License check:** confirm the bundled model/vocab license permits redistribution in
  the wheel before shipping.
