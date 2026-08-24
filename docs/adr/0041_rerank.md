---
type: ADR
name: ADR-RERANK
title: "ADR-RERANK (0041) — proximity reranking, and the cross-encoder that was refused"
description: "BM25F is a bag of words and cannot see where terms are. The reranker adds coverage, minimum span and adjacency over the refer plane's own passages, in stdlib arithmetic. The 17-32M cross-encoder W-76 Phase 6 specified was refused: onnxruntime is not byte-identical across architectures, and cross-machine determinism is the product. Measured 28 -> 32 of 50 goldens, 4 fixed / 0 broken, +8 ms p95 at 10 000 documents."
status: proposed
timestamp: 2026-08-24T00:00:00Z
---

# ADR-RERANK: proximity reranking

- **Name:** `ADR-RERANK` — cite this everywhere; never cite the number
- **Status:** proposed
- **Date:** 2026-08-24
- **Feature:** reranking — W-76 Phase 6
- **Owns:** `src/fux/query/rerank.py`
- **Laws:** **L1, L3 and L4 all HELD** — that is decision 1, and it is the record

## 1 · Examples

```console
$ fux ask "what is the current decision for east west traffic" --top 2
# rerank_weight = 0            # rerank_weight = 1.0
8.0130  ADR-0007 (superseded)  13.2718  ADR-0019 (current)
6.6359  ADR-0019 (current)     11.7391  ADR-0007 (superseded)
```

ADR-0007 wins on BM25F because both documents are dense in the same vocabulary
and **the superseded one is shorter**, so the length normaliser prefers it. The
sentence that settles the question — *"This is the current decision for
east-west traffic."* — is a fact about **adjacency**, and BM25F cannot see
adjacency.

## 2 · Context

### Decision 1 — the cross-encoder is REFUSED, and not on cost

W-76 Phase 6 specified *"17–32 M cross-encoder over the top-50 fetched
passages. Optional dependency (`onnxruntime`)."* That is not built. Three
reasons, in the order they matter:

**1. It would break cross-machine determinism, which is the product.**
[ADR-GRAPH](0028_graph-plane.md) proved fux's float arithmetic is byte-identical
between x86-64 Linux and arm64 macOS — **for pure Python**. `onnxruntime`
dispatches to different SIMD kernels per architecture and reduces GEMMs in a
different order, so two developers on the same commit would get different
orderings from the same index. *"Clone it and run the query"* (Arpit's fork A)
stops being true, and the differential law loses its meaning: there would be no
single right answer for the accelerator and the scan to agree on.

**2. Optional-but-on breaks L4; optional-but-off is not a feature.** Either fux
fetches ~35 MB on first use — offline-by-default gone — or the lane ships dark
and nothing is measured. There is no third position.

**3. Nobody knew the number.** Nothing in the repository said whether reranking
was worth 2 points or 20. Building the cheap signal first converts the neural
question from a preference into arithmetic, and §3 is that arithmetic.

**This is a deferral with a price attached, not a rejection on principle.**
Veto 1 states exactly what would reopen it.

### Decision 2 — three signals BM25F cannot compute

| signal | what it catches | what BM25F does instead |
|---|---|---|
| **coverage** | every query term present, once each | sums per term, so 5× one term beats 1× five |
| **minimum span** | the terms occur *together* | ignores position entirely |
| **adjacency** | query bigrams occur as bigrams, in order | ignores order entirely |

Span is the standard linear sweep over per-term position lists, not an
all-pairs product: a common term in a long document has thousands of positions,
and the quadratic form is what makes naive proximity too slow to ship.

### Decision 3 — coverage MULTIPLIES; it is not a weighted addend

This is the difference between a reranker that works and one that does not, and
it is measured rather than argued. With coverage as an addend the reranker moved
**2** of 22 failing goldens, because every candidate in a corpus about one
subject scores 0.85–1.0 and an 8 % spread cannot overcome a BM25F gap.
Multiplying it — and squaring it first (`COVERAGE_POWER = 2`) — moved **4**.

It is also the right shape on the merits. Span and adjacency are claims about
terms the passage **has**; they are meaningless about a term it lacks. Scoring
them as though a missing term were a small deduction rewards a passage for the
tightness of an incomplete match — which is precisely how ADR-0007 was beating
ADR-0019 while missing the word *current*, the entire question.

### Decision 4 — a document scores as its BEST passage

`embed/chunkvec.py::max_sim`'s argument, and it matters more here. Measured over
whole documents every candidate reaches coverage 1.0 *somewhere* and the signal
flattens to noise. Chunking is the refer plane's own, so a passage the reranker
scored is a passage `answer` can cite — one chunker, not two.

### Decision 5 — it REORDERS; it never retrieves

The candidate set is exactly what the ranker produced. A document BM25F did not
find cannot be rescued here. This is what keeps the derived law true:

> The committed plane must be sufficient to answer. The derived plane may make
> an answer faster or better — never possible.

### Decision 6 — it retrieves DEEPER than the caller asked

`top-20 → top-5`, which is what W-76's gate means. A reranker that can only
shuffle the five documents already on screen cannot promote the sixth, and the
sixth is where the recoverable failures are.

### Decision 7 — DEFAULT OFF, and the reason is not timidity

`[ranking] rerank_weight` defaults to `0.0`. The measured recommendation is
`1.0`. The reason it is not the default is a property, not a hedge:

**The reranker reads the working tree at query time, so its output is not a
pure function of the committed index.** Edit a document without re-ingesting
and BM25F scores the old text while the reranker scores the new. Two clones
with identical indexes but different dirty trees rank differently.

That is defensible — [ADR-REFER](0030_refer-plane.md) already reads live text
on purpose, because *the index finds and the sources speak* — but it is a
different contract from the one `ask` has had, and it is not a change to make
silently in a released tool. The differential law is untouched: the accelerator
and the scan read the same live text and agree byte for byte (§3).

### Decision 8 — a document it cannot read keeps its score

Offline, a `url:` document has no text to rerank against. Demoting it would
make **reachability a ranking signal**, which is the failure ADR-REFER's
offline behaviour exists to avoid.

## 3 · Consequences — the measurement

50 goldens on `fux-playground`, graded on rank. **The reranker was measured
before the goldens carried any prediction about it.**

| configuration | pass | fixed | broken |
|---|---|---|---|
| BM25F alone | **28** / 50 | — | — |
| **+ reranker** | **32** / 50 | 4 | **0** |
| + enrichment (no reranker) | 38 / 50 | 10 | 0 |
| **+ enrichment + reranker** | **41** / 50 | 4 | 1 |

**The finding that matters is what was left.** Of the 18 goldens still failing
after reranking, **18 were vocabulary gaps and 0 were ordering failures** — the
target document did not contain the searcher's words at all. The reranker fixed
every ordering failure the corpus had. That is the honest ceiling of *any*
reranker on this corpus, and it is why enrichment is worth twice as much here.

**Cost**, 10 000 real documents, accelerator path: p95 **33.87 ms → 41.87 ms**,
against a 150 ms bar. The cost is O(depth), not O(corpus) — 20 documents read
per query whatever the corpus size.

**The differential law holds**: 240 accelerator-vs-scan comparisons across five
weights and four depths, 0 divergent.

Filed: [`work/regression/2026-08-24-rerank-and-goldens/`](../../work/regression/2026-08-24-rerank-and-goldens/).

## 4 · Alternatives considered

- **The cross-encoder.** Decision 1.
- **Rank fusion (RRF) between a BM25F order and a proximity order** instead of
  a bounded multiplicative uplift. Scale-free, which is attractive — but it
  gives proximity equal authority to BM25F, and proximity computed on a 2-term
  overlap is noisy. The bounded uplift keeps a real term match dominant, which
  is the same reason the dense lane boosts rather than sums.
- **Tuning to the peak of the (power, weight) surface.** The 4×5 sweep scores
  30–32 everywhere, with 32 at five different points. `(2, 1.0)` was taken from
  the middle of the plateau. A constant read off a spike is an overfit to 50
  queries.

## 5 · Reference (required)

- The goldens and how they were written — [`work/proposals/playground-goldens-draft.md`](../../work/proposals/playground-goldens-draft.md)
- The run — [`work/regression/2026-08-24-rerank-and-goldens/`](../../work/regression/2026-08-24-rerank-and-goldens/)
- W-76 Phase 6 — [`work/open/W-76-amended-architecture.md`](../../work/open/W-76-amended-architecture.md)
- The determinism result that decision 1 rests on — [ADR-GRAPH](0028_graph-plane.md)
- Tests — [`tests/query/test_rerank.py`](../../tests/query/test_rerank.py)

## 6 · Veto condition

**Veto 1 — reopen the cross-encoder when, and only when, both hold:**

1. a golden set exists that the reranker's remaining failures are **ordering**
   failures rather than vocabulary gaps (today: 0 of 18), **and**
2. a cross-encoder is available whose output is byte-identical across x86-64
   and arm64, or the differential law is formally scoped to exclude it.

Condition 1 is the live one. On today's evidence enrichment is worth 10 points
and reranking 4, and a 35 MB dependency targets the class enrichment already
covers deterministically and for free.

**Veto 2 — the reranker must never change the membership of a result set.**

```bash
grep -n "def rerank" -A 40 src/fux/query/rerank.py | grep -c "append\|extend"
# every path must return the same documents it was given; the tests assert it
```

**Veto 3 — the differential law.** If `ask --fast` and `ask --scan` ever
disagree with a non-zero `rerank_weight`, this record is wrong.

**Veto 4 — the latency bar.** Reopen if the reranker's marginal p95 cost
exceeds 25 ms at the 10 000-document design point (measured: 8 ms).
