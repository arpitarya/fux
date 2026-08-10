---
type: ADR
title: ADR-0010 — FuxVec, a stdlib binary vector engine
description: Sign-quantized 256-bit codes, a full-corpus Hamming scan, and exact int8 rerank — removing the candidate-only ceiling ADR 0006 recorded, with zero dependencies.
timestamp: 2026-07-22T00:00:00Z
---

# ADR-0010: FuxVec — binary codes, full-corpus scan, exact rerank

- **Status:** accepted
- **Date:** 2026-07-22
- **Feature:** Dense-global retrieval (handoff 0004, M5)

## Context

[ADR 0006](0006-bundled-model.md) shipped hybrid retrieval with an honest
limitation, recorded at the time: the dense pass only re-scored **BM25F's
candidates**, so a document sharing no vocabulary with the question was
unreachable no matter how close it was semantically. The eval set contained one
such case — *"what technology stores rows on disk"*, whose answer
(`docs/decisions/adr-001.md`) never uses those words — and ADR 0006 stated
plainly that dense "cannot rescue [it] by design".

Removing that ceiling means scoring *every* document against the query. Adopting
a vector database to do it was never open: dependencies are excluded, and ANN
approximates a problem this corpus size does not require approximating.

## Decision

**Sign-quantize at ingest.** Each 256-dim int8 vector becomes a **256-bit code**
(bit *i* = component > 0): 32 bytes per document, cheap enough that the committed
lean plane carries them.

**Scan the whole corpus per query.** Hamming distance is
`(q ^ c).bit_count()` — big-integer XOR and `int.bit_count()` are C-speed
primitives, so a linear scan needs no index structure and no tuning.

**Rerank exactly.** The top `prefilter_width` (default 500) by Hamming are
re-scored with the shipped int8 cosine. The codes only *select*; the final
ordering is exact. Ties in the prefilter break on doc id, so the candidate set
is reproducible.

**Fuse as a third list.** `dense_global` joins RRF beside BM25F and
dense-over-candidates. Fusion is keyed on `(file, ordinal)` rather than object
identity, because a rescued chunk was never in the candidate set.

### Measured: the gate (handoff DoD 6)

| engine | hit@1 | hit@5 | MRR |
|--------|-------|-------|-----|
| lexical v1 | 0.762 | 0.952 | 0.833 |
| v0.22 hybrid (ADR 0006) | 0.762 | 0.952 | 0.833 |
| **hybrid + dense_global** | **0.810** | **1.000** | **0.873** |

The gate asked for ≥ v0.22 hybrid on hit@5 and MRR. It is **beaten, not tied**,
and the specific miss ADR 0006 named is rescued — hit@5 reaching 1.000 *is* that
document being retrieved. `--lexical-only` still measures exactly
0.762 / 0.952 / 0.833, and its four goldens are byte-identical.

### Measured: throughput (proposal flagged this for build-time verification)

`int.bit_count()` over 256-bit codes, best of 3, this machine:

| corpus | scan | rate |
|--------|------|------|
| 10k | 0.4 ms | 27.5 M cmp/s |
| 100k | 3.5 ms | 28.7 M cmp/s |
| 1M | 38.5 ms | 26.0 M cmp/s |

The proposal predicted "~tens of ms over 100k, <1 s over 1M". Measured is
**~10× better at 100k and ~26× better at 1M**. The claim is verified and was
conservative.

### IVF: not built

The handoff authorised deterministic k-means IVF **only if** the 100k scan
exceeded 150 ms. Measured in situ at 100k: **well under** that (see
[ADR 0011](0011-profiles-lean-state.md) for the in-corpus figure; the isolated
scan above is 3.5 ms). IVF is therefore **not implemented** — building an index
structure to accelerate an operation already two orders of magnitude inside
budget would add determinism surface for nothing. The threshold and the
benchmark stay committed as the reopen instrument.

### Decision: `dense_global` does not fire when BM25F returns zero candidates

Found during M5 and worth recording, because the first instinct was wrong. The
early return looked like it was blocking the rescue case, so it was removed —
which made the honest **"No confident matches"** answer unreachable, since a
binary prefilter always has a nearest neighbour.

Measured on the fixture corpus:

| query | top cosine |
|-------|-----------|
| true rescue (*"what technology stores rows on disk"*) | **0.34** |
| noise (*"zzzz qqqq xyzzy nonsense"*) | 0.23 |
| noise (*"flibbertigibbet quantum wombat"*) | 0.26 |

The ranges **overlap**, so any absolute floor separating them is a magic number
that only degrades as the corpus grows and more documents get a chance to be
someone's nearest neighbour.

Re-reading ADR 0006 resolved it: *"zero lexical candidates"* there means the
**correct document** had no lexical overlap — not that the query matched nothing
(that query does return `docs/guide.md`). So the rescue path is the third RRF
list, which always has candidates, and honest emptiness is preserved. The early
return stays.

## Alternatives considered

- **Adopt a vector DB (FAISS / sqlite-vec / LanceDB)** — closed by the `$0`
  stdlib law, and unnecessary: brute force over 32 B codes is fast enough that
  approximation buys nothing at this scale.
- **Store float or int8 vectors for the global scan** — 8–32× the bytes for an
  ordering that gets exactly re-scored anyway.
- **A similarity floor on dense_global** — measured above; the noise and signal
  ranges overlap, so a floor would be a corpus-specific constant pretending to
  be a principle.
- **Build IVF now** — rejected on measurement, not opinion (3.5 ms vs a 150 ms
  budget).

## Consequences

**Easier.** The candidate-only ceiling is gone: a semantically relevant document
is reachable regardless of vocabulary overlap. Storage cost is negligible —
32 B/doc, ~5 MB at 100k.

**Harder.** Two hybrid goldens changed and were regenerated deliberately with
the eval table above as justification. Codes are tied to the bundled model's
256 dims; a model change means one cheap re-quantize pass.

**Owed.** Binary quantization can miss a neighbour whose signs disagree. Fux's
mitigation is a very wide prefilter — 500 candidates for a top-5 query is a
**50–100× oversampling ratio**, against the ~4× used in the reference
implementation cited below — plus the eval gate as the standing check.

## References (required)

- [Embedding Quantization — Sentence Transformers](https://sbert.net/examples/sentence_transformer/applications/embedding-quantization/README.html) —
  **verified at build time** (the proposal flagged this citation as unverified):
  *"By applying this novel rescoring step, we are able to preserve up to ~96 % of
  the total retrieval performance, while reducing the memory and disk space usage
  by 32x"*. Their demo rescores 40 candidates for a top-10 query (4× oversampling);
  Fux rescores 500 for a top-5 (100×), and its final ordering is exact int8
  cosine rather than an approximate score — so the ~96 % figure is a **floor**
  for this design, not a target (accessed 2026-07-22).
- [Binary Quantization & Rescoring (MongoDB)](https://www.mongodb.com/blog/post/binary-quantization-rescoring-96-less-memory-faster-search) —
  independent corroboration: ~96 % memory reduction while retaining up to 95 %
  search accuracy with rescoring (accessed 2026-07-22).
- [Binary Quantization — Qdrant](https://qdrant.tech/articles/binary-quantization/) —
  the production envelope brute-force codes are measured against (accessed 2026-07-22).
- [Billion-scale similarity search with GPUs — Johnson, Douze, Jégou (arXiv:1702.08734; IEEE TBD 7(3):535–547, 2019)](https://arxiv.org/abs/1702.08734) —
  **verified at build time** (also flagged in the proposal): the FAISS IVF
  design whose partitioning scheme Fux would adopt if the scan ever exceeded
  budget. It does not, so it is cited as the deferred path, not the implemented one.
- Internal: [ADR 0006](0006-bundled-model.md) (the recorded miss class this
  removes) · [ADR 0007](0007-rrf-hybrid-fusion.md) (the fusion it joins) ·
  [`../proposals/knowledge-substrate.md`](../proposals/knowledge-substrate.md) §6.
