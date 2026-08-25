---
type: Compare Doc
title: Wire Format
description: One on-disk format vs a committed-wire / local-runtime split; posting codec and dictionary structure choices.
status: accepted
timestamp: 2026-08-09T00:00:00Z
---

# Committed wire format — Comparison

> **Verdict: Split the formats.** Git carries a decode-once, bit-packed
> **wire** format (BIC postings + 4-bit quantized impacts; sorted-hash
> dictionary + Elias-Fano offsets; front-coded ledger); hooks inflate it
> locally into byte-aligned mmap **runtime** segments (block-max, decoded
> via `memoryview.cast` at native speed). MPH dictionary deferred to M8.
> **Status:** ✅ accepted 2026-08-09 · **Confidence:** high (codec rates are
> published measurements) · **Reopen when:** P2 misses ≤ 300 MB @1M, or BIC
> inflate time pushes P5 past 5 min.
>
> ⚠ **That trigger is unreachable, so it is not a live condition (W-65, 2026-08-22).**
> It is keyed to **1M documents** — a deferred target since 2026-08-21 — and to
> **P2**, retired with plan revision 1. P2's successor R7 is itself *closed
> unmeasured* and awaiting re-derivation at 10 000 ([W-26](../../archive/open/W-26-m6-scale-t2.md)).
> A veto written as an event nobody is waiting for never fires; re-deriving
> this one belongs with whatever decides T2's future, not here.

## Context

One format must serve two masters: clone weight (compression) and query
speed (decode). They conflict — the best codecs are bit-packed and
Python-hostile to decode per-query. Git's own packfile/working-tree split
is the precedent: compress the transported artifact, inflate the working
one.

## Options

- **A — Split formats** *(verdict)*: wire = BIC (~4.5 bits/docid measured
  on Gov2 [6,7]; <1 bit on clustered lists — doc-id assignment by ledger
  order aims there) + 4-bit impacts; runtime = byte-aligned 128-entry
  blocks, per-block max-impact + skip. Decode cost paid once per clone.
- **B — One byte-aligned format** (v1 of this design): ~700 MB committed
  @1M; no inflate step; 3× the clone weight.
- **C — One bit-packed format**: smallest clone, but every query decodes
  bit-packed postings in interpreted Python — kills P3.

Dictionary sub-fork: sorted u64-hash array (8 B/key, binary search, zero
build risk) now; RecSplit/PtrHash-class MPH (~2 bits/key, ~15 MB saving)
as a pure-win M8 upgrade once correctness is proven.

## Matrix

| criterion (weight) | A split | B byte-aligned | C bit-packed only |
|---|---|---|---|
| committed size @1M (H) | **~220–290 MB** | ~700 MB | ~200 MB |
| query decode speed (H) | **native (cast)** | native | interpreted, slow |
| clone→first-answer (M) | + inflate minutes (P5) | immediate | immediate |
| complexity (M) | two formats, one direction | one | one |

## Consequences

The inflate step becomes part of clone UX (hooks; P5 ≤ 5 min gate). Wire
encoders can be slow-but-simple pure Python — correctness over speed.
Format version lives in the keyspace root; wire and runtime version
together.

## References

Paper §5, Figure 4 · Moffat & Stuiver 2000 (BIC) · Pibiri & Venturini
survey (gap clustering: "50% of gaps are 1") · Ottaviano & Venturini
SIGIR '14 (PEF baseline) · RecSplit / PtrHash (MPH, deferred).

## Reopen-trigger

See verdict block; measured at M3 (P2) and M7 (P5).
