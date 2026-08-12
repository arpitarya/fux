# Handoffs — live build specs

One pair per milestone entering build: a **handoff doc** (the contract —
context, definition of done, scope, non-negotiables, tests, open
questions) and a **prompt** (paste-ready, points Claude Code at the
handoff and sets its behavior). Both are written *after* a debate gate;
the gate can and does change the plan.

**This directory holds live work only.** A fully executed pair moves to
[`../archive/`](../archive/README.md) — *completed doc artifacts* — in the
same change as its ADR, stamped `status: implemented` with the ADR link.
That is what makes listing this directory answer *"what is in flight"*.

Root `archive/` is a different archive: it holds **old builds** (`v0.26/`,
`v0.1/`, `v0.30-rev1-planning/`). See
[`../archive/README.md`](../archive/README.md) for the full distinction.

## Live pairs

| pair | milestone | model | status |
|------|-----------|-------|--------|
| [handoff](v0.33.0-m4-refer-plane-handoff.md) · [prompt](v0.33.0-m4-refer-plane-prompt.md) | **M4 · the refer plane** — HTTP + Confluence, the ARC cache under the differential law, transient convert + passage re-score, the freshness fence; both filed proposals graduate into the API's first shape | **Opus** for the API shape and the ARC differential · one named **Sonnet** window for the adapters and the bench | **live** (proposed) — do not start until ADR-0005 is ratified |
| [handoff](v0.32.0-open-items-handoff.md) · [prompt](v0.32.0-open-items-prompt.md) | **v0.32.0 open-items program** — Phase 0 (W-43, W-33, W-42, the ratification package) and Phase 1 (W-22 / M2) are **both closed**; M3–M7 gated on their own pairs | **Opus** throughout, two named Sonnet windows | **live** — Phases 0 and 1 done 2026-08-12; §5's remaining chain is still the sequencing of record |

## Proposed diffs (awaiting Arpit — agent-steering files are never auto-applied)

| diff | what it changes | tracked by |
|---|---|---|
| [`v0.30.0-claude-md.diff`](v0.30.0-claude-md.diff) | the M0a `CLAUDE.md` rewrite (48 KB) | [W-32](../open/W-32-claude-md-adoption.md) |
| [`v0.30.0-m1-claude-md-build-test.diff`](v0.30.0-m1-claude-md-build-test.diff) | `CLAUDE.md` §Build & test, once `src/` existed | [W-32](../open/W-32-claude-md-adoption.md) |
| [`v0.31.0-claude-md-layout.diff`](v0.31.0-claude-md-layout.diff) | the four-line `.fux/` addition to §Layout | [W-31](../open/W-31-ratify-adr-0010-0011.md) · [W-32](../open/W-32-claude-md-adoption.md) |
| [`v0.32.0-adr-numbering.diff`](v0.32.0-adr-numbering.diff) | `adr/README.md` becomes the single owner of the numbering policy; `CLAUDE.md` points at it instead of restating "0016" | [W-33](../open/W-33-adr-numbering-contradiction.md) |

All five decisions are packaged for a single sitting in
[`v0.32.0-ratification-package.md`](v0.32.0-ratification-package.md) —
which also corrects two things the tracker had wrong: there is no
`CLAUDE.md.proposed` (the rewrite is already the live file), and ADR-0010 /
ADR-0011 are **shipped code** sitting under unratified decisions.

## Executed pairs — where they went

| pair | milestone | closed by |
|------|-----------|-----------|
| [handoff](../../archive/v0.30-rev1-planning/v0.30.0-m0-m1-gate-handoff.md) · [prompt](../../archive/v0.30-rev1-planning/v0.30.0-m0-m1-gate-prompt.md) | M0 hygiene + ADR-0001 + M1 the pruning gate | 2026-08-09 → [ADR-0001](../adr/0001-ingest-mode-naming.md), [ADR-0002](../adr/0002-pruning-eval-gate.md) (INCONCLUSIVE) |
| [handoff](../../archive/v0.30-rev1-planning/v0.30.0-m1-rerun-handoff.md) · [prompt](../../archive/v0.30-rev1-planning/v0.30.0-m1-rerun-prompt.md) | M1-rerun — make P1 decidable (RFC corpus, 5 arms, retention-matched, recall@20) | 2026-08-09 → [ADR-0003](../adr/0003-pruning-criterion-rerun.md) (**FAIL** — option E accepted) |
| [handoff](../archive/v0.30.0-m1-t0-slice-handoff.md) · [prompt](../archive/v0.30.0-m1-t0-slice-prompt.md) | **M0 scaffold + M1 T0 slice** — canonical JSONL store, git-dir ingest, scan `ask` | 2026-08-10 → [ADR-0004](../adr/0004-index-format.md) (R1 PASS, R2 2/3 at M1) |
| [handoff](../archive/v0.31.0-fux-dir-layout-handoff.md) · [prompt](../archive/v0.31.0-fux-dir-layout-prompt.md) | **the `.fux/` layout** — declared committed vs derived planes, URL source relocated | 2026-08-11 → [ADR-0011](../adr/0011-fux-dir-layout.md) |
| [handoff](../archive/v0.31.0-fux-playground-extraction-handoff.md) · [prompt](../archive/v0.31.0-fux-playground-extraction-prompt.md) | **fux-playground** — delete `examples/`, build the graded sibling corpus | 2026-08-12 → [ADR-0012](../adr/0012-playground-sibling-repo.md) (41 pass / 9 named xfail) |

The first two pairs pre-date the archive law's `docs/archive/` convention
and live under root `archive/v0.30-rev1-planning/` with the rest of the
pre-gate planning set; they are not moved, because moving frozen planning
artifacts would break the citations in ADRs 0002 and 0003.

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
