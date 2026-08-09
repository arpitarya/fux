# Handoffs — live build specs

One pair per milestone entering build: a **handoff doc** (the contract —
context, definition of done, scope, non-negotiables, tests, open
questions) and a **prompt** (paste-ready, points Claude Code at the
handoff and sets its behavior). Both are written *after* a debate gate;
the gate can and does change the plan.

Fully executed pairs move to [`../archive/`](../archive/), version-named,
with their ADRs linked.

| pair | milestone | model | status |
|------|-----------|-------|--------|
| [handoff](v0.30.0-m0-m1-gate-handoff.md) · [prompt](v0.30.0-m0-m1-gate-prompt.md) | M0 hygiene + ADR-0016 + **M1 the pruning gate** (+ M0b scaffold on PASS) | Sonnet build · **Opus verdict** | ready |

**Note on this pair:** its debate gate amended `PLAN.md`'s sequencing —
the package scaffold moved *after* the M1 gate, because scaffolding an
architecture that P1 may falsify is the failure the council's pre-mortem
seat named. PLAN §M0/§M1 and OPEN-WORK W-01…W-05 reflect the corrected
order.
