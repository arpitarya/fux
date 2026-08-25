---
type: Verdict
name: DENSE-CHUNK
title: "DENSE-CHUNK — does the per-chunk dense lane reach >= 3-fixed / 0-broken, the bar for leaving `mode = off`?"
description: "FAIL. 0 fixed and 2 broken at every setting that fires. The lane never fixes a single graded query, and the reason is structural: the bundled embedding is a MEAN-POOL of static token vectors, so it is as order-blind as BM25F."
status: final
verdict: FAIL
prediction: DENSE-CHUNK
pre_registration: src/fux/query/dense.py
timestamp: 2026-08-24T00:00:00Z
---

# DENSE-CHUNK — the dense lane's own gate, run

**FAIL**, and not narrowly.

## The bar, written before the measurement

[`src/fux/query/dense.py`](../../../src/fux/query/dense.py) and
[ADR-CLI](../../../docs/adr/0002_cli-surface.md) both carry it:

> the 3-fixed/9-broken result must become **>= 3-fixed / 0-broken** on the
> frozen questions before `[dense] mode` moves off `off`

The document-level lane it replaced fixed 3 and broke 9. Phase 7's claim was
that the **unit** was the defect — one vector per document instead of per
chunk — and that per-chunk vectors would clear the bar.

## The ruling

| setting | pass | fixed | **broke** |
|---|---|---|---|
| `off` (control) | **32 / 50** | — | — |
| `gated` t=0.5 w=0.25 | 32 / 50 | 0 | 0 — *the gate never fires* |
| `gated` t=8.0 w=0.25 | 31 / 50 | 0 | **1** (`q020`) |
| `always` w=0.25 | 30 / 50 | 0 | **2** (`q015`, `q020`) |
| `always` w=0.5 | 30 / 50 | 0 | **2** (`q015`, `q020`) |

**0 fixed at every setting.** The bar needs 3.

**`gated` is NOT dead code**, and an earlier reading of this sweep said so
wrongly. It did not fire at `t = 0.5` or `t = 2.0` because the top lexical
score on this corpus is ~8.08 and the gate is `score < threshold`. At
`t = 8.0` it fires on some queries and at `t = 100` on all of them — and every
time it fires, it costs a query. The gate works; what it lets in does not.

## Why — and this is the part that outlives the number

**The bundled embedding is a mean-pool of static token vectors.**
`src/fux/embed/model.py::embed` tokenizes, looks each token up in a packed
table, sums, and divides. **There are no transformer layers and no attention.**

So the dense lane is **as order-blind as BM25F**. *"current"* and *"no longer
current"* pool to nearly the same point, which is precisely the failure
[the blind-author runs](../2026-08-24-blind-enrichment-second-author/report.md)
identified on `q015` — and `always` mode **breaks `q015` itself**, which is the
single query a semantic lane was most expected to rescue.

**This does not make Phase 7 wrong about the unit.** Per-chunk is a better unit
than per-document, and the vectors are committed and cost nothing at rest. It
means the unit was **not the binding constraint**. The pooling is.

## What this rules out, and what it does not

- **Rules out:** switching `[dense] mode` off `off` on this corpus. The bar is
  unmet by a wide margin and the lane is a net negative wherever it fires.
- **Does NOT rule out:** the vectors themselves. They stay committed, they are
  0 bytes of query cost while `mode = off`, and a better pooling would reuse
  them unchanged.
- **Does NOT rule out** a rebuild — but see the analysis: every rebuild that
  could fix `q015` needs to read word order, which is the capability
  [ADR-RERANK](../../../docs/adr/0041_rerank.md) veto 1 condition 2 refuses on
  determinism grounds. **The rebuild path and the cross-encoder path converge.**

## Scope

- One corpus, 10 documents, 50 queries. A FAIL this wide is unlikely to be
  corpus-specific, but nothing here measures the lane at the design point.
- The threshold sweep is coarse (5 settings). It does not need to be finer: no
  setting fixed **anything**, so there is no promising region to bracket.
