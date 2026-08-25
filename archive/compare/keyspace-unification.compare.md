---
type: Compare Doc
title: Keyspace Unification
description: Six separate index planes vs one MST keyspace vs a succinct wavelet-tree self-index.
status: accepted
timestamp: 2026-08-09T00:00:00Z
---

# Index unification — Comparison

> **Verdict: One MST keyspace.** All six components are key prefixes
> (`L/ P/ D/ V/ E/ M/`) in a single content-addressed Merkle Search Tree:
> one physical format, one CRDT join, one O(diff) diff, **one root hash
> naming the entire corpus state**. The wavelet-tree self-index is recorded
> as a research note, not built.
> **Status:** ⚠ **SUPERSEDED 2026-08-09 (same day)** by
> [`index-format.compare.md`](index-format.compare.md): the committed plane
> became sharded canonical JSONL, where **git itself supplies the Merkle
> tree** — content addressing, O(diff) history, and a single tree hash —
> so the custom MST substrate is not built. Every goal in this verdict
> (one format, one merge, one corpus-state hash) is still met, by git.
> The MST idea survives as tier-T2 internals if ever needed.
> *(Original status: ✅ accepted 2026-08-09 · Confidence: high.)*
> **Reopen when:** T2 needs a content-defined chunk store that git blobs
> cannot provide.

## Context

Arpit's question: "can all the components in index merge into 1?" Separate
planes mean separate format versions, separate merge logic, separate diff
stories — five chances to disagree.

## Options

- **A — One MST keyspace** *(verdict)*: prefixes over one ordered,
  content-chunked (~4 KB, rolling hash), history-independent tree [MST,
  SRDS '19]. Precedent: Dolt/FoundationDB "everything is one ordered KV".
- **B — Six sharded planes** (v1 sketch): simplest individually; 6× the
  merge/diff/version surface.
- **C — Wavelet-tree self-index**: postings and forward index become one
  succinct structure (rank/select duality, ~n·log σ bits) [Navarro CPM '12;
  FM-index]. Theoretically maximal unification; bit-level ops per query are
  interpreted-Python-hostile.

## Matrix

| criterion (weight) | A MST keyspace | B six planes | C wavelet |
|---|---|---|---|
| merge/diff/version surfaces (H) | **1** | 6 | 1 |
| corpus state identity (H) | **one root hash** | none | one |
| query decode speed (H) | native (values are the wire blocks) | native | slow in Python |
| implementation risk (M) | one non-trivial structure (M2) | low | high |
| determinism story (H) | **structural** (unique representation) | by discipline | structural |

## Consequences

M2 builds the store once; every later component is rows, not formats.
"Same index?" between machines = hash compare. `fux diff` (proposals/
knowledge-diff) gets its substrate for free. Risk concentrated in one
component → M2 carries the heaviest property-test budget in the plan.

## References

Paper §4 · Auvolat & Taïani (MST) · ForkBase (POS-tree precedent) · Dolt
storage engine · Navarro, *Wavelet Trees for All* + FM-index (option C,
also filed as [`../proposals/wavelet-self-index.md`](../proposals/wavelet-self-index.md)).

## Reopen-trigger

See verdict block; measured continuously from M2's DoD onward.
