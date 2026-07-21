---
type: Registry
title: Doc registry — the documentation freshness tracker
description: One row per maintained doc — update trigger + last-verified date; the docs-in-sync law made checkable.
timestamp: 2026-07-21T00:00:00Z
---

# Doc registry — the documentation freshness tracker

*One row per maintained document. This is the separate tracking file Arpit asked for:
agents (Cowork, Claude Code, any hook) check it to know **which docs exist, what
triggers an update to each, and when each was last verified true**. The docs-in-sync
law in CLAUDE.md says update docs with every task; this file makes that checkable
instead of remembered — the same instinct as the held rule engine, applied to docs.*

**Contract (research-grounded):** every maintained doc has an update **trigger**
("what change makes this stale?") and a **last-verified** date. A task that fires a
trigger updates the doc *and* its row. A row older than ~30 days is a review prompt,
not a crisis. Docs update in the same change as the work — atomic, per docs-as-code
practice.

| Document | Update trigger | Last verified | Notes |
|----------|---------------|---------------|-------|
| [`../CLAUDE.md`](../CLAUDE.md) | Scope, constraints, lifecycle, or layout changes; new durable session learnings | 2026-07-21 | Binding; also auto-folded per the standing rule |
| [`index.md`](index.md) | Bundle contents change (new/moved/removed docs) | 2026-07-21 | OKF bundle root; declares okf_version |
| [`../README.md`](../README.md) | Install/use surface, commands, guarantees change | 2026-07-21 | Public front door; v1 command surface |
| [`../DOGFOOD.md`](../DOGFOOD.md) | v1 use surface changes; dogfood learnings land | 2026-07-21 | 10-min Anton quickstart (master-prompt rule 6) |
| [`fux-plan.md`](fux-plan.md) | Any design decision, scope change, status change | 2026-07-21 | Design of record |
| [`model-handoff-interview.md`](model-handoff-interview.md) | Direction/strategy/major decision changes | 2026-07-21 | Succession record; add yourself to maintainer line |
| [`worklog.md`](worklog.md) | **Every substantive exchange** (append) | 2026-07-21 | Rolling session handoff |
| [`implementation.md`](implementation.md) | Every milestone completion + regular intervals during builds | 2026-07-21 | Live build tracker; deviations logged |
| [`cli-examples.md`](cli-examples.md) | Any command/flag/output-format/exit-code change | 2026-07-21 | UX contract; e2e goldens derive from it — update together |
| [`compare/README.md`](compare/README.md) | A compare doc opens, closes, or changes status | 2026-07-21 | Decision index |
| [`compare/*.compare.md`](compare/) | New evidence, verdict change, or reopen-trigger fires | 2026-07-21 | One per decided fork |
| [`adr/`](adr/) | A feature completes (one ADR per feature) | 2026-07-21 | 0001–0005 (v1 + v1.1 features) |
| `handoff/` | A feature enters build (handoff + prompt pair) | 2026-07-21 | 0003 (v2 hybrid) live; 0001+0002 implemented → `archive/` |
| [`proposals/`](proposals/README.md) | An idea is parked, graduates, or is rejected | 2026-07-21 | `status:` frontmatter tracks lifecycle |
| [`archive/`](archive/README.md) | A handoff/prompt/proposal is fully implemented | 2026-07-21 | 0001 + 0002 pairs archived with ADR links |
| `tests/` + e2e suite docs | Any behaviour change | 2026-07-21 | 154 unit + 25 e2e; goldens updated via FUX_UPDATE_GOLDENS=1 only |

## How agents use this file

1. **At task end:** scan the trigger column; if your change fired a trigger, update
   that doc and bump its row. CLAUDE.md binds you to this.
2. **Hook prompt (once wired):** the session-end hook reads this table, diffs changed
   files against triggers, and *prompts* "these docs look affected — update them?"
   Fail-open, advisory: the hook nags, it never blocks.
3. **Adding a doc:** new maintained doc → new row, in the same change that creates it.
