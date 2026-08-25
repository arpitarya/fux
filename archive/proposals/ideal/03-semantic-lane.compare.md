---
type: Compare Doc
title: "The semantic lane — what to embed, with what, and where it ranks"
status: proposed
filed: 2026-08-21
laws_bracketed: [L1, L3]
---

# The semantic lane — what to embed, with what, and where it ranks

## What exists

- A bundled 7.6 MB static token table (a distilled WordPiece→int8 lookup),
  mean-pooled over `title + body` **truncated at 1024 tokens**, then
  **sign-quantized to 256 bits per document**.
- Hamming prefilter (width 100) → RRF with lexical. **Default off** because on
  the 50 goldens it fixed 3 and broke 9.
- Costs **92 % of ingest time** (pure-Python mean-pool).

## Why it loses today (diagnosis, not opinion)

1. **Doc-level** code: one 32-byte code for a 40 KB runbook. Truncation
   drops everything after ~1024 tokens; the mean over a long mixed doc is
   mush.
2. **Sign quantization without rescore**: the docs say "candidates are
   re-scored with exact int8 cosine", but the hybrid path fuses the Hamming
   ranking directly. 1-bit codes are a *prefilter*, and sqlite-vec's own
   guidance is retrieve `k×8` binary then rescore with full vectors
   ([sqlite-vec](https://alexgarcia.xyz/sqlite-vec/guides/binary-quant.html)).
3. **Unconditional RRF**: fusing a weak lane into a strong one at equal
   weight demotes correct lexical answers. Hybrid beats either lane *when
   both lanes are competent* ([Elastic hybrid](https://www.elastic.co/search-labs/blog/improving-information-retrieval-elastic-stack-hybrid)).

## Options

| | A · today (doc sign codes) | B · static embeddings per chunk (model2vec / ST static) | C · small transformer (MiniLM/bge-small via ONNX int8) | D · learned sparse (SPLADE/ELSER-class) | E · late interaction (ColBERT-small) |
|---|---|---|---|---|---|
| model size | 7.6 MB | 8–30 MB ([model2vec](https://github.com/MinishLab/model2vec)) | 20–45 MB int8 | ~100 MB+ | ~130 MB |
| CPU embed speed | slow in pure Python | ~100k sentences/s ([HF](https://huggingface.co/blog/static-embeddings)) | ~1.7k sentences/s | slower (transformer fwd) | slower |
| quality (NanoBEIR nDCG@10, indicative) | below any of these | 0.50 | 0.56 (MiniLM) – 0.64 (bge-base) | ELSER +17 % over BM25 avg on BEIR ([Elastic](https://www.elastic.co/search-labs/blog/elastic-learned-sparse-encoder-elser-retrieval-performance)) | highest of the lot |
| runtime deps | none | numpy (or pure-Python fallback) | onnxruntime + numpy | onnxruntime | onnxruntime + a lot of RAM |
| bit-reproducible across machines | yes (int) | yes with int8 table + int sums | **no** (float non-associativity) | no | no |
| storage per doc (10 chunks) | 32 B | 10 × 256 × 1 B int8 = 2.5 KB (+32 B binary prefilter each) | same | sparse vector, fits the **existing postings format** | 10 × ~32 tokens × 128 d — large |
| fits hashed meta / ACL leak | yes | yes | yes | **terms are visible** — needs hashing | yes |
| offline | yes | yes | yes | yes | yes |
| query-time cost | 1 XOR/doc | 1 XOR/chunk then int8 dot on k×8 | same + model fwd on the query | inverted-index lookup (fast) | MaxSim over candidates |

## Debate

- **B is the honest upgrade of A.** Same idea (static table, mean-pool), done
  right: per-heading chunks, keep int8 vectors for rescore, binary codes only
  to prefilter. Ingest cost drops ~100× if numpy is allowed (int arithmetic
  stays exact, so the result can still be asserted identical to the
  pure-Python path — the differential law survives). `potion-retrieval-32M`
  is the strongest static retrieval model available.
- **C** buys ~+6 nDCG over B at ~60× the embed cost and loses
  reproducibility. For a tool whose *ingest* runs in hooks and CI, B's speed
  matters more than C's quality — and doc 04's reranker recovers more
  quality than C would, at the point where it is cheapest (top-20 only).
- **D is the most interesting fit for Fux specifically.** A learned sparse
  vector *is* a posting list. It drops into the existing postings/block-max
  machinery, stays hashed-meta compatible after hashing the expansion terms,
  and gives the "synonym" class of gain without a second index. Cost: a
  transformer forward pass at ingest (no worse than C), and expansion terms
  are model output (doc 04's pinned-text rule applies).
- **E** is overkill for this corpus shape and memory profile.

## Proposed verdict

**B now; D as the second lane once a model is allowed in ingest (doc 04).**

1. Chunk on headings (the refer plane's chunker already exists — reuse it at
   ingest).
2. Embed each chunk with a static retrieval model (model2vec `potion-retrieval`
   class); store int8 vectors in the **derived** index (doc 01) and 256-bit
   codes beside them.
3. Query: Hamming prefilter to k×8 chunks → exact int8 rescore → max-sim per
   doc.
4. **Gated fusion**, not unconditional RRF: fuse only when the lexical lane's
   top score is below a calibrated threshold or returns < 3 candidates;
   otherwise dense acts as a *tiebreak/booster* with a lower RRF weight.
5. Retire doc-level sign codes from the committed shards (`code` field) —
   they are the one part of the committed index that earns nothing.

Also — cheapest of all, and worth measuring first: **use the static table
for deterministic query-term expansion** (nearest vocabulary neighbours of
each query token, added at low weight). It keeps everything inside the
lexical lane, costs nothing at ingest, and directly targets the
`known_failure` class 3 goldens.

## Reopen trigger

Reopen for C/E if, after B + the reranker (doc 04), the graded set still has
a failure class that is semantic rather than lexical (i.e. the gold passage
shares no stem with the query *and* the reranker never sees it in top-20).
