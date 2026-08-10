---
type: ADR
title: ADR-0013 — Supersession awareness (annotate, don't reorder)
description: Frontmatter status:superseded/superseded_by parsed at ingest, persisted in the substrate and .fux/state/, surfaced in find/ask/why, and preferred by answer — without touching find's ranking.
timestamp: 2026-07-23T00:00:00Z
---

# ADR-0013: Supersession awareness

- **Status:** accepted
- **Date:** 2026-07-23
- **Feature:** Trust & currency, supersession half (handoff 0006, M2/M3/M5)

## Context

The acme-payments realistic corpus (`docs/conformance/2026-07-22-acme-payments/`)
measured Fux's core promise failing: the **superseded** document outranked the
still-true one in **9 of 12** planted stale-vs-current pairs, usually stale at
rank 1. All three supersession markers tried — `superseded_by:` frontmatter, a
dated inline prose note, and no marker at all — failed identically, because
nothing in the pipeline *knew* one document superseded another; the markers
were plain text the index counted, not a signal it acted on.

Two designs were on the table (`docs/compare/supersession-handling.compare.md`):
annotate the flag and let `answer` prefer the current document (Option A), or
additionally down-rank superseded chunks in RRF fusion so `find`'s ranking
itself corrects (Option B). Arpit accepted Option A on 2026-07-23.

## Decision

**Parse, persist, and annotate — never reorder.**

1. **Frontmatter is the only contract acted on.** `status: superseded` and/or
   `superseded_by: <doc-id>` in a document's own frontmatter — nothing else.
   Prose mentions of "superseded" in a heading or body, and any other
   `status` value, are near-misses that must not flag (tested explicitly:
   `status: draft`, `status: superseded_by_nothing`, prose-only mentions).
2. **Extracted at index build, not ingest.** `index.build_index` re-parses
   each cache file's frontmatter anyway (for graph scanning); a new
   `_supersession_meta()` reads `status`/`superseded_by` from that same parse
   and merges `{"superseded": true, "superseded_by": <id>}` into the file's
   entry in `files[rel]` — in both the reused-chunks branch and the rebuilt
   branch (with stale keys explicitly stripped from a reused entry first, so
   a document that later drops its marker doesn't carry a ghost flag
   forward).
3. **Chains resolve to their terminal document; cycles are unresolved, not
   infinite.** A corpus-wide `_resolve_supersession()` pass (same shape as
   the existing corpus-wide edge-resolution pass) follows `superseded_by`
   chains via a `seen` set — a dangling target or a cycle sets
   `superseded_unresolved: true` and stops, never crashes, never loops.
4. **Persisted in both the index and `.fux/state/`.** The sqlite backend
   gained four `docs` columns (`superseded`, `superseded_by`,
   `superseded_by_resolved`, `superseded_unresolved`) and bumped
   `format_version` 2→3 (an incompatible schema rebuilds, per that module's
   existing recovery contract) — JSON/sqlite parity is provably preserved
   (both backends return the same optional keys, present only when true).
   `.fux/state/DocState` gained a `superseded_by` slot, folded through the
   existing generic `flags: list[str]` field plus one new slot — an
   **optional key in an already-arbitrary JSON meta payload**, so an
   unmarked document pays zero bytes toward the ~200 B/doc committed-state
   budget.
5. **Annotation only, ranking untouched.** `find`/`ask` `--json` gain
   `"superseded": true, "superseded_by": "<doc-id>"` (the resolved terminal
   when known, the raw named target when unresolved — a dangling pointer is
   shown, never silently dropped); human output gets a `[superseded → …]`
   marker. **Result ordering, and all four `--lexical-only` goldens, are
   byte-identical to before this change** — verified, not assumed.
6. **`answer` is the one place behaviour changes.** When a superseded
   document and its (resolved) successor are both in the pool `answer`
   actually retrieved for a query, `query.answer.prefer_current()` drops the
   superseded document's chunks before sentence selection. When the
   successor is absent from that pool, `answer` still sources from what it
   has and annotates the source as superseded in its `sources` list — it
   does not silently serve a retired answer as if it were current.
7. **`fux why` surfaces the flag** (`superseded`/`superseded_by` in
   `WhyResult`, plus a human "superseded: true → docs/current.md" line) so an
   inversion or a decline explains itself without re-deriving it by hand.

## Alternatives considered

- **Option B — down-rank in RRF fusion.** Rejected for now: the penalty
  magnitude is a tuned number, and the repo's own filed proposal
  (`docs/proposals/staleness-ranking-ignores-supersession.md`) already gates
  it on *a second realistic corpus confirming the effect and a penalty tuned
  against real inversions* — a condition Option A does not need, because
  honoring an author-written `superseded_by:` is reading a declaration, not a
  statistical judgment. B also risks regressing today's working evals (the
  `why`/`how-to`/`factual` classes score hit@5 = 1.00 on acme); A cannot
  regress anything because it never reorders. Reopens if a second corpus
  reproduces the inversion rate at a tunable-without-regression penalty, or if
  post-ship measurement shows agents demonstrably ignore the annotation.
- **NLP/heuristic detection of prose or dated supersession notes.** Forbidden
  by the no-model constraint; accepted as a documented, permanent limit —
  only frontmatter-marked documents are reachable.
- **Storing the raw and resolved `superseded_by` as one field.** Rejected:
  DoD 3 requires a dangling or cyclic target to still be *shown*, not hidden
  behind "couldn't resolve, so nothing to display" — keeping both the raw
  pointer and the resolved terminal separate is what lets `--json` show a
  broken pointer instead of silently dropping it.

## Consequences

**Easier.** An author who marks a document `superseded_by:` gets that fact
surfaced everywhere Fux answers from it — `find`, `ask`, `answer`, `why` — for
$0 and with no ranking risk. `fux why` can now explain a staleness inversion in
one line instead of a human re-deriving it.

**Harder.** The sqlite backend's schema bumped a major-ish version
(`format_version` 2→3); any environment with a pre-existing `.fux/index/fux.db`
rebuilds on next `fux ingest` rather than migrating in place — acceptable per
that module's own stated recovery contract, but worth calling out since it's
the first schema bump since ADR 0008.

**Owed.** Recovery on the acme corpus's measured 9/12 `find`-inversions is
**small and partial, measured exactly**
(`docs/conformance/2026-07-23-supersession-recovery/`): only **5 of 12** stale
docs carry a machine-readable marker at all, only **3 of the 9** inversions
have one, and at the `answer` level the fix **fully corrects 1** (settlement)
and **de-cites the retired doc in a 2nd** without promoting the current one
(authentication — a retrieval weakness, not a supersession defect); a 3rd
(reconciliation) was already answer-correct pre-fix, since `find`-inversion and
`answer`-correctness are different metrics. The other **6 are unmarked and
deterministically unreachable** without a model. `find`'s rank-1 harm for an
agent that reads only the top result and ignores the annotation is a named,
accepted residual — the reopen-trigger above is what would change that.

## References

- Nygard, *Documenting Architecture Decisions* (2011) — `superseded_by` as the
  established, machine-readable ADR-supersession marker; the reason this
  feature leans on frontmatter as the contract rather than inventing a new one.
- Measured: [`../conformance/2026-07-22-acme-payments/report.md`](../conformance/2026-07-22-acme-payments/report.md)
  §Finding 1 (the original 9/12) ·
  [`../conformance/2026-07-23-supersession-recovery/report.md`](../conformance/2026-07-23-supersession-recovery/report.md)
  (the after-measurement).
- [`../compare/supersession-handling.compare.md`](../compare/supersession-handling.compare.md) —
  the accepted fork and the rejected Option B, in full.
- Internal: [handoff 0006](../handoff/0006-trust-currency-handoff.md) (the build
  contract) · [ADR 0008](0008-substrate-store-lock-state.md) (the state-plane
  format this feature extends) · [ADR 0002](0002-ingest-cache-chunker.md) (the
  determinism guarantee `_resolve_supersession`'s corpus-wide pass preserves).
