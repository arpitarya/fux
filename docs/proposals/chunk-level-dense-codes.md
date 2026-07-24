---
type: Proposal
title: Chunk-level dense codes — fix the dense plane's ranking, not just its reach
description: FuxVec stores one binary code per document. Zero-overlap recall (clean dense rescue 1/6 on two corpora) and the ~4% hybrid-loses-a-lexical-hit finding share one root cause — a document-level dense signal too coarse to rank the right chunk. Proposes per-chunk codes as the structural fix. Parked; graduates to a compare doc when picked up.
status: proposed
timestamp: 2026-07-24T00:00:00Z
tags: [retrieval, fuxvec, dense, zero-overlap, findings]
---

# Chunk-level dense codes

## Context — two findings, one root cause

Two separately-filed conformance findings converge on the same defect: **the
dense plane's signal is too coarse to rank the right chunk**, because FuxVec
stores one code per *document*, not per *chunk*.

1. **Zero-overlap clean dense rescue: 1/6** on both acme and orbit
   (`docs/conformance/2026-07-24-orbit-fulfillment/` §Finding 3). Questions with
   no lexical overlap with their answer are the dense plane's whole reason to
   exist, and it rescues one in six.

2. **Hybrid loses a lexical top-5 hit ~4%** of the time on realistic corpora
   (`docs/conformance/2026-07-24-fusion-lexical-hit-loss/`). Measured in phase 9;
   the compare doc `hybrid-losing-lexical-hits` **accepted** this rather than
   guarding fusion, on the explicit grounds that *the cause is dense quality, not
   fusion* — and named this phase as the real owner.

In every realistic loss case the dense list ranked the correct document poorly
(similarity near ADR 0010's 0.23–0.26 noise band) while ranking a wrong one well.
A per-document code cannot distinguish "this document contains the answer in one
chunk" from "this document is broadly on-topic" — exactly the discrimination
these questions need.

## Sketch (not a design — that is the compare doc's job)

- **Per-chunk binary codes** instead of (or alongside) the per-document code, so
  the dense list ranks the *chunk* that answers, not the document that is nearest
  on average.
- **Budget is the hard constraint.** The committed state plane is ~200 B/doc
  today (ADR 0011). Per-chunk codes multiply that by the chunk count; the
  proposal must show it fits the committed-corpus budget or justify a derived
  (gitignored) tier.
- **The eval bar is ADR 0015's:** any ranking change gates on a four-eval-set
  sweep with zero hit@5 regression in any question kind, and `--lexical-only`
  stays byte-identical.

## Why parked, not built

- It is a **structural change to the dense index**, not a knob — it needs its own
  compare doc (codes-per-chunk vs codes-per-passage vs a two-tier doc-then-chunk
  scan) and its own ADR.
- The two findings above **establish the need**; neither establishes the design.
- Phase 9 deliberately did **not** touch it — a release-time or judgment-time
  patch to the dense index is the wrong way in.

## Graduation

When picked up: a compare doc weighing the index-layout options against the
committed-state budget, gated on the four-eval-set sweep, then an ADR. The two
conformance runs above are the evidence it inherits.

## References

- The reach failure: [`../conformance/2026-07-24-orbit-fulfillment/ANALYSIS.md`](../conformance/2026-07-24-orbit-fulfillment/ANALYSIS.md) §Finding 3.
- The ranking failure it shares a cause with: [`../conformance/2026-07-24-fusion-lexical-hit-loss/ANALYSIS.md`](../conformance/2026-07-24-fusion-lexical-hit-loss/ANALYSIS.md).
- The accepted verdict that hands this finding here: [`../compare/hybrid-losing-lexical-hits.compare.md`](../compare/hybrid-losing-lexical-hits.compare.md).
- The dense plane as built (per-document codes, the noise band): [`../adr/0010-fuxvec-binary-dense-search.md`](../adr/0010-fuxvec-binary-dense-search.md).
- The committed-state budget it must fit: [`../adr/0011-profiles-lean-state.md`](../adr/0011-profiles-lean-state.md).
