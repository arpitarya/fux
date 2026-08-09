# Handoffs — live build specs

One pair per milestone entering build: a **handoff doc** (the contract —
context, definition of done, scope, non-negotiables, tests, open
questions) and a **prompt** (paste-ready, points Claude Code at the
handoff and sets its behavior). Both are written *after* a debate gate;
the gate can and does change the plan.

Fully executed pairs move to [`../archive/`](../archive/README.md), version-named,
with their ADRs linked.

| pair | milestone | model | status |
|------|-----------|-------|--------|
| [handoff](v0.30.0-m0-m1-gate-handoff.md) · [prompt](v0.30.0-m0-m1-gate-prompt.md) | M0 hygiene + ADR-0016 + M1 the pruning gate | Sonnet build · Opus verdict | **executed** 2026-08-09 → [ADR-0016](../adr/0016-ingest-mode-naming.md), [ADR-0017](../adr/0017-pruning-eval-gate.md) (INCONCLUSIVE) |
| [handoff](v0.30.0-m1-rerun-handoff.md) · [prompt](v0.30.0-m1-rerun-prompt.md) | **M1-rerun — make P1 decidable** (long-doc corpus, 5 selector arms, retention-matched, recall@20 gate) | **Opus throughout** | ready · **next** |

**Note on the first pair:** its debate gate amended `PLAN.md`'s sequencing —
the package scaffold moved *after* the M1 gate, because scaffolding an
architecture that P1 may falsify is the failure the council's pre-mortem
seat named. That call paid: P1 came back INCONCLUSIVE and no orphan
scaffold exists.

**Note on the second pair:** its gate found that a naive re-run would have
repeated the same design on a better corpus — measuring the index's own
hit@5, when the index is a candidate generator feeding a re-score stage.
The metric moved to recall@20, the criterion opened to five arms, and the
budget became retention-based. See
[`../compare/pruning-criterion.compare.md`](../compare/pruning-criterion.compare.md).
