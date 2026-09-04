---
type: OpenItem
id: W-106
title: "W-106 — the vector gate: does a contextual embedder clear DENSE-CHUNK's frozen bar on the vocabulary-gap failures?"
description: "A scratch measurement, no fux code. The dense lane failed 0/2 with a static mean-pooled model; a contextual model has never been measured here. Run DENSE-CHUNK's frozen >= 3 fixed / 0 broken on the 50 playground goldens, judged on the vocabulary-gap failures, with both embedder implementations and two architectures. PASS unblocks W-112; FAIL closes the vector plane with evidence."
status: open
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

## Definition of done

- [ ] `tools/vector-gate/` (dev extra, **never imported by `src/fux/`**; the
      import-fence test stays green): chunk the 10 playground documents with
      `fux.refer._chunk.chunk`; embed chunks + 50 queries; per-vector int8
      (`scale = 127 / max|x|`); max-sim per document; RRF `k = 60` with the
      BM25F ranks `fux ask --json` produces today.
- [ ] Two embedder arms: `@huggingface/transformers` (Node, `dtype: 'q8'`,
      `pooling: 'mean'`, `normalize: true`) and `sentence-transformers`, same
      model (`BAAI/bge-small-en-v1.5`, revision pinned).
- [ ] Two-architecture arm for the **query** vectors (x86-64 + arm64):
      discordant count of top-5 orderings.
- [ ] Filed under `work/regression/<date>-vector-gate/` per the per-run
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
