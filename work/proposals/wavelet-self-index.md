---
type: Proposal
title: Wavelet-tree self-index (research note)
description: The theoretically maximal unification — postings and forward index as one succinct structure; evaluated for v0.30 and rejected for interpreted-decode cost. Kept as the marker for a future native-extension era.
status: proposed
timestamp: 2026-08-09T00:00:00Z
---

# Wavelet-tree self-index — research note

**The idea.** A wavelet tree over the doc-term sequence answers *both*
directions from one structure: `select` = postings (docs containing t),
`access`/`rank` = forward index (terms of d, with counts), in ~n·log σ
bits — the inverted and forward index become the same object (Navarro,
*Wavelet Trees for All*, CPM '12; FM-index lineage, FOCS '00). TerminusDB
runs its triple store on this family.

**Why rejected for v0.30** (keyspace-unification compare): every operation
is bit-level rank/select — native-speed in C, hopeless in interpreted
Python; the MST keyspace delivers "one thing" at the container level
without the decode tax.

**Why kept.** Two futures reopen it: (1) Python ships a usable
bit-manipulation fast path or Fux ever admits a compiled extension for the
runtime plane (a *law change*, needing its own debate); (2) the runtime
segment inflation cost (P5) ever becomes the bottleneck — a self-index
needs no inflation, the wire IS the runtime.

**Graduation trigger.** Either future above, plus a benchmarked prototype
showing ≤ 2× the mmap segments' query latency.

**References.** Navarro CPM '12 · Ferragina–Manzini FM-index ·
[`../compare/keyspace-unification.compare.md`](../compare/keyspace-unification.compare.md)
(option C, the rejection this note preserves) · paper §4.
