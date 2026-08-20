---
type: Compare Doc
title: Maintenance Trigger — Keeping the Index and Graph Plane Fresh
description: How a source-doc change reaches the committed index and the derived runtime/graph plane without a human remembering to run `fux ingest`/`fux build` — git hooks, CI rebuild, a local watch daemon, or the status quo (manual).
status: accepted
timestamp: 2026-08-20T00:00:00Z
---

# Maintenance trigger — Comparison

> **Verdict: A — git hooks (`post-commit`/`post-merge`/`post-checkout`)
> driving delta ingest**, exactly as scoped in
> [W-25](../open/W-25-m5-maintenance.md) / `ADR-MAINTENANCE` (reserved). A
> hook re-emits only the changed lines into the committed index — not a full
> rebuild — and the existing write-if-different + per-shard-sha discipline
> ([ADR-INDEX-LIFECYCLE](../../docs/adr/0009_index-lifecycle.md)) does the
> rest. Rejected: **B — CI-triggered rebuild** (a bot commits over the
> human's diff, defeating the doc-major diffable design the committed index
> exists for); **C — a local watch daemon** (solves live-edit latency but not
> the merge story W-25 already scopes, and is an always-on process this
> architecture has never needed elsewhere); **D — manual, status quo**
> (today's actual state — nothing updates the committed index automatically).
> **Status:** ✅ accepted (Arpit, 2026-08-20). **Next: implement W-25.**
> **Open sub-decision, not yet ruled on:** should the hook also call `fux
> build` so `.fux/runtime/graph.json` refreshes immediately, or is the
> existing stale→scan fallback ([ADR-INDEX-LIFECYCLE](../../docs/adr/0009_index-lifecycle.md)
> decision 7) sufficient and the rebuild left on its current manual/CI
> trigger? Fold the answer into `ADR-MAINTENANCE` when it's written.
> **Reopen when:** R5 (20-doc commit < 1 s) or R6 (three-tier merge harness)
> fails once measured — see W-25's DoD — or a hook is found to leave a
> half-written committed shard on failure.

## Context

Two layers need to stay fresh, and they are not the same problem:

1. **Source docs → committed index** (`.fux/index/*.jsonl`, via `fux
   ingest`). **Zero automation exists today.** A document can change on disk
   and the committed index simply does not know, until someone remembers to
   run `fux ingest`.
2. **Committed index → derived runtime, including the graph plane**
   (`.fux/runtime/`, via `fux build`). This layer **already self-protects**:
   the runtime manifest pins a sha per committed shard
   ([ADR-INDEX-LIFECYCLE](../../docs/adr/0009_index-lifecycle.md) decision
   7), and on drift `ask`/`explain`/`graph`/`path` fall back to a full scan
   rather than trust a stale accelerator or a stale graph plane
   ([ADR-GRAPH](../../docs/adr/0030_graph.md)). It is never *wrong*,
   only slow when stale — so the open problem for this layer is triggering a
   rebuild promptly, not correctness.

This isn't new ground: [ADR-INGEST](../../docs/adr/0007_ingest.md)'s
consequences section already named the target — **"re-ingest is safe to run
on a hook, which is what M5 depends on"** — and
[W-25](../open/W-25-m5-maintenance.md) is the open item that was scoped to
build it: hooks → delta ingest, a line-wise last-writer-wins merge driver via
`.gitattributes`, and `meta: hashed` enforcement at write time. W-25 is
**unblocked and next in queue**. This document is not proposing a new idea —
it is comparing W-25's already-scoped approach against the plausible
alternatives, so the choice is on record rather than assumed.

## The fork

**A — Git hooks + delta ingest (W-25 as scoped).** `post-commit` /
`post-merge` / `post-checkout` re-emit changed lines through the same
canonical encoder and write-if-different path `fux ingest` already uses. Runs
locally, on every machine, for every contributor, with no server
dependency. Merge safety comes from a dedicated line-wise LWW driver on
`(ver, sha)` — machine planes never conflict; human-authored snapshot files
conflict normally, on purpose.

**B — CI-triggered rebuild.** A GitHub Action runs `fux ingest && fux build`
on push and commits the result back. Centralizes the work, but a bot commit
racing a human's own next commit is exactly the merge-conflict problem the
committed index's doc-major format was built to avoid — and it adds a
round-trip (push → CI → bot commit → pull) where the local-hook approach is
synchronous.

**C — Local watch daemon.** `watchdog`/`fswatch` re-ingests on every file
save, live during editing. Lowest latency of any option, but: doesn't touch
the merge-conflict problem at all (two branches still collide the same way
without W-25's driver), requires an always-on background process this
codebase has never needed before, and does nothing for a contributor who
edits over SSH or on a machine where the daemon isn't running.

**D — Manual (status quo).** Someone remembers to run `fux ingest` /`fux
build`. Zero implementation cost, and it's what's running today — the
failure mode is exactly what motivated this research: an index or graph
plane that's silently behind what a person believes it reflects, discovered
only by `fux doctor` or a stale-answer fallback if someone thinks to check.

## Matrix

| | A — git hooks (W-25) | B — CI rebuild | C — watch daemon | D — manual |
|---|---|---|---|---|
| Latency | < 1 s target (R5), on commit | minutes, on push | instant, on save | unbounded — human-dependent |
| Works offline | yes | no | yes | yes |
| Always-on process required | no | no (but needs CI minutes) | yes | no |
| Merge-safe across branches | yes — dedicated driver | no — bot commit vs human commit races | no | no |
| Fits committed-index architecture (doc-major, diffable, write-if-different) | yes | fights it | orthogonal | trivially, because nothing runs |
| Implementation cost | scoped, medium (W-25) | low-medium, but ongoing CI cost | low, but ongoing process to run/manage | none |

## Consequences

- This is the blueprint for building W-25, not a new spec — W-25's own file
  is still the source of truth for what ships.
- The open sub-decision (does the hook also call `fux build`) should be
  answered explicitly when `ADR-MAINTENANCE` is written, not left implicit.
  Leaving it implicit risks two people assuming opposite defaults.
- A watch daemon (C) is not eliminated forever — it's a plausible *later*
  layer on top of A for live-edit latency, not a replacement for the
  merge-safety work A does. Not scoped now; would be its own proposal if
  revisited.

## Reopen trigger

**R5 or R6, once measured, fails** — the 20-doc-commit-under-1s target
misses, or the three-tier merge harness shows machine planes conflicting or a
human conflict silently resolved instead of preserved. Separately, **not a
reopen, a revisit**: once the hook exists, decide the `fux build`
sub-question above and fold it into `ADR-MAINTENANCE` rather than letting it
default silently.

## References

- [W-25 — M5: maintenance](../open/W-25-m5-maintenance.md) — the item this
  document backs
- [ADR-INGEST](../../docs/adr/0007_ingest.md) — "re-ingest is safe to run on
  a hook, which is what M5 depends on"
- [ADR-INDEX-LIFECYCLE](../../docs/adr/0009_index-lifecycle.md) — the
  write-if-different + per-shard-sha staleness mechanism layer 2 already has
- [ADR-GRAPH](../../docs/adr/0030_graph.md) — the derived graph plane
  this rebuild refreshes
