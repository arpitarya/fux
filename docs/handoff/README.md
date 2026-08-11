# Handoffs — live build specs

One pair per milestone entering build: a **handoff doc** (the contract —
context, definition of done, scope, non-negotiables, tests, open
questions) and a **prompt** (paste-ready, points Claude Code at the
handoff and sets its behavior). Both are written *after* a debate gate;
the gate can and does change the plan.

Fully executed pairs move to [`../archive/`](../archive/README.md) — *completed doc artifacts* —
version-named, with their ADRs linked. (Root `archive/` holds **old builds**: `v0.26/`, `v0.1/`,
`v0.30-rev1-planning/`. The two are different archives and the distinction matters.)

> **Outstanding ([W-43](../open/W-43-archive-law-debt.md)):** the two pairs marked *executed* below
> are still in this directory. Until they move, listing `handoff/` does **not** answer "what is in
> flight" — which is the only reason the archive law exists.

| pair | milestone | model | status |
|------|-----------|-------|--------|
| [handoff](../../archive/v0.30-rev1-planning/v0.30.0-m0-m1-gate-handoff.md) · [prompt](../../archive/v0.30-rev1-planning/v0.30.0-m0-m1-gate-prompt.md) | M0 hygiene + ADR-0001 + M1 the pruning gate | Sonnet build · Opus verdict | **executed** 2026-08-09 → [ADR-0001](../adr/0001-ingest-mode-naming.md), [ADR-0002](../adr/0002-pruning-eval-gate.md) (INCONCLUSIVE) |
| [handoff](../../archive/v0.30-rev1-planning/v0.30.0-m1-rerun-handoff.md) · [prompt](../../archive/v0.30-rev1-planning/v0.30.0-m1-rerun-prompt.md) | M1-rerun — make P1 decidable (RFC corpus, 5 arms, retention-matched, recall@20) | Opus throughout | **executed** 2026-08-09 → [ADR-0003](../adr/0003-pruning-criterion-rerun.md) (**FAIL** — option E accepted) |
| [handoff](v0.30.0-m1-t0-slice-handoff.md) · [prompt](v0.30.0-m1-t0-slice-prompt.md) | **M0 scaffold + M1 T0 slice** — canonical JSONL store, git-dir ingest, scan `ask`, dogfood on this repo | **Sonnet** · one Opus review checkpoint (the canonical writer) | **executed** 2026-08-10 → [ADR-0004](../adr/0004-index-format.md) (R1 PASS, R2 2/3 PASS) |
| [handoff](v0.31.0-fux-playground-extraction-handoff.md) · [prompt](v0.31.0-fux-playground-extraction-prompt.md) | **fux-playground** — delete `examples/`, build the graded sibling corpus (10 docs, 50 goldens, 10 URLs, file-only index + staleness guard) | **Opus** throughout — the corpus and golden set are the deliverable and no test catches a bad one | **executed** 2026-08-12 → [ADR-0012](../adr/0012-playground-sibling-repo.md) (41 pass / 9 named xfail) |
| [handoff](v0.32.0-open-items-handoff.md) · [prompt](v0.32.0-open-items-prompt.md) | **v0.32.0 open-items program** — Phase 0 clears the backlog (W-43, W-33, W-42, the W-30/31/32 ratification package); Phase 1 builds M2 (W-22); M3–M7 gated on their own pairs | **Opus** throughout, two named Sonnet windows — the differential law is the invariant the tiering story rests on, and Phase 0 holds three silent-failure judgment calls | **live** (proposed) |

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
