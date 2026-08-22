---
type: Compare Doc
title: Cache Policy
description: Replacement policy for the refer-plane content cache — LRU vs ARC.
status: accepted
timestamp: 2026-08-09T00:00:00Z
---

# Content-cache replacement policy — Comparison

> **Verdict: ARC** (Adaptive Replacement Cache), keyed `(locator, sha)`,
> byte-budgeted, barred by construction from changing any result.
> **Status:** ✅ accepted 2026-08-09 · **Confidence:** high (well-published
> result; expired patent) · **Reopen when:** measured hit-rate at M5 shows
> no advantage over LRU on real Fux workloads (then take the simpler code).

## Context

The v0.26 lean profile shipped a plain LRU with a monotonic-counter clock.
The refer model raises the stakes: a cache miss is now a 0.5–2 s network
fetch, and maintenance operations (hook-driven re-index after a big merge)
are exactly the bulk scans that flush an LRU's hot set.

## Options

- **A — ARC** *(verdict)*: self-tuning between recency and frequency,
  **scan-resistant**, no tuning knob, ~2× LRU hit ratio across published
  workloads; ~150 LOC from the FAST '03 paper; IBM patent expired. ZFS
  precedent.
- **B — LRU** (carry v0.26's forward): simplest; scan-flushable; a knob-free
  workload mismatch costs live fetches.
- **C — 2Q/TinyLFU-class**: comparable gains, more tuning surface, weaker
  fit for a 150-LOC stdlib target.

## Matrix

| criterion (weight) | A ARC | B LRU | C 2Q/TinyLFU |
|---|---|---|---|
| scan resistance (H) | **yes** | no | partial |
| miss cost sensitivity (H) | best fit | poor | good |
| tuning burden (M) | **none** | none | knobs |
| LOC / audit surface (M) | ~150 | ~40 | ~200+ |
| determinism (H) | safe — cache cannot change results; recency via monotonic counter (v0.26 rule carried) | same | same |

## Consequences

M5 implements ARC with the v0.26 no-wall-clock rule; a differential test
(cache-on vs cache-off, identical results) is part of M5's DoD. If the
reopen-trigger fires, downgrade to LRU is a drop-in (same interface).

## References

Megiddo & Modha, FAST '03 · ARC overview (Wikipedia) · archived ADR-0011
(the lean LRU + monotonic-counter rule this inherits).

## Reopen-trigger

See verdict block; measured at M5.

> **2026-08-22 — evaluated against R4, not fired.** R4 (2026-08-20) measured
> ARC vs LRU on a synthetic trace. Against the pre-registered 2-pt bar, the
> original metric did not clearly clear it, so a second metric was chosen
> **after** seeing that number — post-hoc by definition — and showed +0.91
> pts overall / +2.50 pts on hot requests. The trigger's own text asks for a
> *real* Fux workload; this was synthetic. **Arpit reviewed the post-hoc
> reasoning directly and ruled: ARC wins, ship it as-is.** This closes the
> question against R4 specifically — it does not retire the trigger itself.
> A future measurement on real traffic showing no advantage over LRU would
> still reopen this record (see [ADR-CACHE](../../docs/adr/0034_cache.md)
> veto condition 6, the owning record since 2026-08-21).
