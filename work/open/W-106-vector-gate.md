---
type: OpenItem
id: W-106
title: "W-106 — the vector gate: does a contextual embedder clear DENSE-CHUNK's frozen bar on the vocabulary-gap failures?"
description: "A scratch measurement, no fux code. The dense lane failed 0/2 with a static mean-pooled model; a contextual model has never been measured here. Run DENSE-CHUNK's frozen >= 3 fixed / 0 broken on the 50 playground goldens, judged on the vocabulary-gap failures, with both embedder implementations and two architectures. PASS unblocks W-112; FAIL closes the vector plane with evidence."
status: measured-no-verdict
lane: agent
timestamp: 2026-09-04T00:00:00Z
---

# W-106 — the vector gate

**Model: Opus** — calling a gate is Opus work by CLAUDE.md's rule, and the
analysis has to separate *vocabulary-gap* wins from *negation* non-wins
without being told which is which by the score.

## The spec this implements

[`../proposals/search-v3.md`](../proposals/search-v3.md) §5 and §8 (W-106).
The bar is [DENSE-CHUNK](../regression/2026-08-24-dense-lane-gate/VERDICT.md)'s,
**frozen and not restated here**: `>= 3 fixed / 0 broken` on the 50 goldens
against today's `ask`. ⚠ **Judged on the vocabulary-gap failures** (18 of 18
survivors in [rerank-and-goldens](../regression/2026-08-24-rerank-and-goldens/ANALYSIS.md) §5).
Negation queries (`q015`, `q021`) are reported and **not expected** —
NevIR puts bi-encoders at 7–11 % on negation (search-v3 §9.5). An earlier
draft named `q015` the litmus; that was wrong and is withdrawn.

## Goal

One number Arpit can rule on: does a contextual, locally-run, int8-quantised
embedder fused with today's BM25F by RRF fix ≥ 3 vocabulary-gap goldens and
break 0? Plus the discordant count between two architectures' query vectors.

## Outcome — measured 2026-09-05, **no verdict filed**

🔴 **Arpit ruled on 2026-09-05: measure and file WITHOUT a verdict.**
[DENSE-CHUNK's bar was not tested](../regression/2026-09-05-vector-gate/report.md) —
`fux-playground`'s committed index is `fux.index.v1` (this engine refuses to
read it) and its ten enrichment files were **never committed**, so *today's
ask* grades **28 / 50** against that control's **32 / 50**. Four more failing
queries makes `>= 3 fixed` strictly easier, and a PASS would be a moved
threshold arriving through the corpus.

- **Retrieval:** both correctly-configured arms **net zero** — `cls`/q8 in Node
  6 fixed / 6 broken, `sentence-transformers` 5 / 5 — and each moves **1 of the
  9** vocabulary-gap failures. Neither reaches 0 broken.
- 🔴 **The finding is reproducibility, not retrieval.** Two implementations of
  one model, both correctly configured, agree to **cosine 0.9964** and share
  **0 of 125 identical int8 vectors**, with **41 / 50** top-5 dense orderings
  discordant. int8 is **not** the cause (0.9962 within one implementation).
  **W-112's determinism claim can only ever be *"same clone + same embedder
  build"*.**
- ⚠ **This item's own DoD prescribed `pooling: 'mean'`, which is WRONG for
  BGE** (`BAAI/bge-small-en-v1.5` declares `cls`), and **the misconfigured arm
  scored best** — 10 fixed / 4 broken. Kept and filed, because that is how a
  misconfiguration becomes a result.

**Still owed:** the **two-architecture arm** (x86-64 + arm64 — only arm64
exists on this machine), and a corpus that can carry the bar
([W-87 Part B](../OPEN-WORK.md)).

## Definition of done

- [x] `tools/vector-gate/` (dev extra, **never imported by `src/fux/`**; the
      import-fence test stays green): chunk the 10 playground documents with
      `fux.refer._chunk.chunk`; embed chunks + 50 queries; per-vector int8
      (`scale = 127 / max|x|`); max-sim per document; RRF `k = 60` with the
      BM25F ranks `fux ask --json` produces today.
- [x] **Three** embedder arms (the two asked for, plus the misconfigured one as evidence): `@huggingface/transformers` (Node, `dtype: 'q8'`,
      `pooling: 'mean'`, `normalize: true`) and `sentence-transformers`, same
      model (`BAAI/bge-small-en-v1.5`, revision pinned).
- [ ] 🔴 **NOT RUN — arm64 only on this machine.** Two-architecture arm for the **query** vectors (x86-64 + arm64):
      discordant count of top-5 orderings.
- [x] Filed as [`2026-09-05-vector-gate`](../regression/2026-09-05-vector-gate/report.md), **without `VERDICT.md`** per Arpit's ruling. Originally: filed under `work/regression/<date>-vector-gate/` per the per-run
      contract: `report.md` with `classification: informed` (the goldens are
      known) and the Authorship block; `VERDICT.md` naming DENSE-CHUNK's bar;
      **per-query rows** for every arm; `ANALYSIS.md` separating
      vocabulary-gap from negation outcomes.
- [ ] `OPEN-WORK.md` row updated with the verdict; W-112's row unblocked or
      deleted accordingly; this file to `archive/open/`.

## Blockers

- `arpit` lane: ratification of search-v3 §8. Nothing else — this is scratch.

## Hazards

- 🔴 **Do not touch `src/fux/`.** The lane was deleted on 2026-08-25; a gate
  that lands code before the verdict is the failure the lifecycle exists to
  stop.
- 🔴 The score is not the finding; **which class of query moved** is. Report
  fixed/broken by class.
- The playground is 10 documents. A PASS licenses W-112's *build*, not a
  claim at 10 000; say so in the verdict.
- Model download happens in the scratch environment only (fux-lab), never in
  CI.

## Out of scope

Any fux code. Any default. The Node reader. A compare doc (that is the
PASS outcome's next step, not this item).
