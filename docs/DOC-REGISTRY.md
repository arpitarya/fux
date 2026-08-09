# Doc registry — the documentation freshness tracker

*One row per maintained document. Agents (Cowork, Claude Code, any hook)
check it to know **which docs exist, what triggers an update to each, and
when each was last verified true**. The docs-in-sync law in CLAUDE.md says
update docs with every task; this file makes that checkable. Rows for the
archived v0.26 docs were retired 2026-08-09 with the reset — archived docs
are frozen and never update.*

**Contract:** every maintained doc has an update **trigger** and a
**last-verified** date. A task that fires a trigger updates the doc *and*
its row, in the same change. A row older than ~30 days is a review prompt.
Docs large enough to carry §humans + §agents sections update both.

| Document | Update trigger | Last verified | Notes |
|----------|---------------|---------------|-------|
| [`../CLAUDE.md`](../CLAUDE.md) | Scope, constraints, lifecycle, layout changes | 2026-08-09 | ⚠ still describes v0.26 in places — sync is M0 scope (W-03) |
| [`../README.md`](../README.md) | Status, guarantees, reading order change | 2026-08-09 | Rebuild-status stub until M4 |
| [`index.md`](index.md) | Bundle contents change | 2026-08-09 | OKF bundle root |
| [`PLAN.md`](PLAN.md) | Any design/scope/status change | 2026-08-09 | The build of record; agent quick-ref section at top |
| [`OPEN-WORK.md`](OPEN-WORK.md) | **Any work item or prediction changes state** | 2026-08-09 | The live tracker (replaces archived IMPLEMENTATION.md); §humans + §agents |
| [`paper/the-fux-index-paper.md`](paper/the-fux-index-paper.md) | Architecture changes; a P-prediction gets measured (M7 updates §5–6 to measured) | 2026-08-09 | Architecture of record + figures |
| [`architecture-components.svg`](architecture-components.svg) | Any component/plane/policy change | 2026-08-09 | v2 map; council annotations in footer |
| [`architecture-index-and-refer.svg`](architecture-index-and-refer.svg) | High-level flow changes | 2026-08-09 | |
| [`INTERVIEW.md`](INTERVIEW.md) | Direction/strategy/major decision changes | 2026-08-09 | Succession record; the reset is a mandatory entry |
| [`WORKLOG.md`](WORKLOG.md) | **Every substantive exchange** (append) | 2026-08-09 | Rolling session handoff |
| [`GLOSSARY.md`](GLOSSARY.md) | New recurring term, or a term changes meaning | 2026-07-24 | ⚠ needs v0.30 pass (index, ledger, wire/runtime, refer, enriched…) — W-03 scope |
| [`compare/README.md`](compare/README.md) | A compare doc opens, closes, changes status | 2026-08-09 | Six v0.30 forks; verdict-first convention |
| [`compare/*.compare.md`](compare/) | New evidence, verdict change, reopen-trigger fires | 2026-08-09 | `ingest-mode-naming` is ⏳ (closes via ADR-0016) |
| [`adr/`](adr/) | A feature completes (one ADR per feature) | 2026-08-09 | Empty + TEMPLATE; numbering continues at 0016; 0001–0015 archived |
| [`handoff/`](handoff/) | A feature enters build (handoff + prompt pair) | 2026-08-09 | Empty; M0 pair is next |
| [`proposals/`](proposals/README.md) | An idea is parked, graduates, or is rejected | 2026-08-09 | 3 new (mcp-adapters, knowledge-ci, wavelet-self-index) + 3 carried; v0.26-era moved to archive |
| [`conformance/`](conformance/README.md) | Every fux-lab run — report + ANALYSIS + evidence | 2026-07-24 | Persists across rebuilds; M1's eval run files here |
| [`archive/`](archive/README.md) | Something is implemented or superseded | 2026-08-09 | + `v0.26-docs/` (frozen) + `PLAN-v0.26.md` |
| `../.github/` | Required checks, release path change | 2026-07-22 | Unchanged by the reset; CI will need new paths at M0 (W-01 checks this) |

## How agents use this file

1. **At task end:** scan the trigger column; if your change fired a
   trigger, update that doc and bump its row. CLAUDE.md binds you to this.
2. **Adding a doc:** new maintained doc → new row, in the same change that
   creates it. Archiving a doc → retire its row, same change.
3. **The two ⚠ rows are open work items** (W-03) — they are stale
   knowingly, tracked in OPEN-WORK, not silently.
