---
type: ADR
title: ADR-0006 — the bundled ≤10 MB embedding model (distillation recipe + eval numbers)
description: Re-packed potion-base-8M, int8 per-vector quantization, stdlib WordPiece + mean-pool inference, vector cache — and the measured eval results.
timestamp: 2026-07-21T00:00:00Z
---

# ADR-0006: bundled static-embedding model + stdlib inference

- **Status:** accepted
- **Date:** 2026-07-21
- **Feature:** handoff 0003 M2–M4 — the packaged model and its runtime

## Context

Engine v2 needs semantic recall with **no external model or service, ever**
(packaged-model compare doc): a static-embedding model built into the wheel at
≤10 MB, inferred with pure stdlib (numpy vendoring disproven in the compare
doc). The eval harness (M1) is the gate and the reopen-instrument.

## Decision

- **Ship re-packed `minishlab/potion-base-8M`** (Model2Vec static embeddings
  distilled from bge-base-en-v1.5; MIT, license-checked in the pipeline).
  *Open question 1 resolved:* distilling our own docs-flavored model needs a
  large in-domain corpus we don't have — Anton's future corpus is the reopen
  trigger; the recipe is ready in `tools/distill/`.
- **Quantization:** int8 per-vector symmetric (`scale = max|v|/127`), packed
  with `struct` into `model.bin` — **7.93 MB** (vocab 29,528 × 256 dims),
  sha256-pinned (`21cbd6d1…`) and asserted by tests; format documented in
  `tools/distill/README.md`.
- **Stdlib runtime (`fux.embed`)**: the teacher's tokenizer reimplemented —
  BertNormalizer (clean/CJK/lowercase/accent-strip) + Bert pre-tokenization +
  WordPiece with atomic special tokens — with **exact token-id parity**
  verified against distill-exported samples; mean-pool with the mean folded
  into the scale; similarity = exact int8 dot (sum in int, scale once) so
  results are bit-identical across platforms. Long chunks truncate at 1024
  tokens. Lazy singleton: lexical paths never load it.
- **Chunk-vector cache** `.fux/index/vectors.bin` — one packed file (*open
  question 2:* shards buy nothing; the set rewrites from memory anyway),
  invalidated on (source sha, fidelity) exactly like the chunk index, so
  `--advanced` upgrades re-embed. All-OOV chunks store a None flag.
- **Vectors are derived data** (*open question 3:* lean-corpus leaning
  adopted): commit `.fux/cache/` + `manifest.jsonl`; `.fux/index/` (chunk index
  + vectors) is regenerable and safe to gitignore. Both modes work — the
  README documents the recommendation; Arpit can override at review.
- **Degradation contract:** bundle missing (source installs) → hybrid quietly
  unavailable, engine reports `bm25f`; bundle corrupt → `FuxError` with the
  rebuild hint; `--lexical-only` always works.

## Measured results (the gate, DoD 5)

Fixture eval set (21 pairs incl. deliberate zero-overlap paraphrases), top-10:

| engine | hit@1 | hit@5 | MRR |
|--------|-------|-------|-----|
| lexical v1 | 0.762 | 0.952 | 0.833 |
| hybrid v2 | 0.762 | 0.952 | 0.833 |

**The gate (hybrid ≥ lexical on hit@5 and MRR) passes as a tie — hybrid ships
enabled.** Honest reading: on a 9-file corpus, file-level metrics saturate;
rank-level rescues are real (e.g. *"cadence of pushing measurements
downstream"* → correct file at rank 1 with sim 0.079 vs noise ≤0.052; *"how
long does reverting…"* → rank 1). The single remaining @5 miss (*"what
technology stores rows on disk"*) has **zero lexical candidates**, which dense
cannot rescue by design — the accepted candidate-only trade (compare-doc math;
keeps stdlib inference sub-millisecond). The Anton eval (harness README) is
the instrument that can reopen this and the no-reranker decision.

Performance, measured: model load 10 ms · warm hybrid query 0.2 ms (<100 ms
requirement) · wheel 6.98 MB total (≤15 MB budget).

## Alternatives considered

- Distill-our-own on a docs corpus — deferred (no corpus yet; recipe ready).
- float16/product quantization — unnecessary: int8 fits the budget with exact
  integer dot products, which PQ would sacrifice.
- tiktoken-style BPE reimplementation — moot; the teacher is WordPiece.

## Consequences

Easier: paraphrase recall with zero new dependencies and zero network; the
embed runtime is ~300 lines of auditable stdlib. Harder: the model is
English-biased (non-English text degrades toward lexical — noted limitation);
ingest pays a one-time embedding cost (pure-Python ~1–2 s per ~100 chunks,
incremental thereafter).

## References (required)

- Packaged-model compare doc (verdict + no-numpy proof + candidate-only math):
  [../compare/packaged-model.compare.md](../compare/packaged-model.compare.md)
- Model2Vec (static-embedding distillation): https://github.com/MinishLab/model2vec
- potion-base-8M model card (MIT): https://huggingface.co/minishlab/potion-base-8M
