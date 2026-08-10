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
| [`../CLAUDE.md`](../CLAUDE.md) | Scope, constraints, lifecycle, layout changes | 2026-08-10 | **Still proposed, not adopted** — the file's own header says so; [diff](handoff/v0.30.0-claude-md.diff) is the artifact awaiting Arpit's review. (Corrects a stale claim in this row that said "adopted".) |
| [`../README.md`](../README.md) | Status, guarantees, reading order change | 2026-08-10 | Status line moved to "T0 slice: ingest + ask work on this repo" (M0+M1 shipped) |
| [`../CHANGELOG.md`](../CHANGELOG.md) | A release-worthy change lands | 2026-08-11 | New this session — **released as `0.30.0`** (M0 scaffold + M1 T0 slice) |
| [`index.md`](index.md) | Bundle contents change | 2026-08-09 | OKF bundle root |
| [`architecture.svg`](architecture.svg) + [`architecture-overview.svg`](architecture-overview.svg) | Any tier/record-shape/query-path change (detailed) · any component add/remove (overview) | 2026-08-09 | Rev-2 pair: overview (5 components) + detailed; rev-1 pair archived |
| [`PLAN.md`](PLAN.md) | Any design/scope/status change | 2026-08-09 | The build of record; agent quick-ref section at top |
| [`OPEN-WORK.md`](OPEN-WORK.md) | **Any work item or prediction changes state** | 2026-08-10 | W-20/W-21 **DONE**; R1 **PASS**, R2 **2/3 PASS** (detail: ADR-0004) |
| [`paper/the-fux-index-paper.md`](paper/the-fux-index-paper.md) | Architecture changes; a P-prediction gets measured (M7 updates §5–6 to measured) | 2026-08-09 | Architecture of record + figures |
| [`INTERVIEW.md`](INTERVIEW.md) | Direction/strategy/major decision changes | 2026-08-09 | Succession record; the reset is a mandatory entry |
| [`WORKLOG.md`](WORKLOG.md) | **Every substantive exchange** (append) | 2026-08-10 | Rolling session handoff |
| [`GLOSSARY.md`](GLOSSARY.md) | New recurring term, or a term changes meaning | 2026-08-09 | Rewritten for v0.30 (index vs db, ledger, keyspace, wire/runtime, refer/snapshot, inferred/enriched, pruning, ARC); archived v0.26 terms marked not-current |
| [`compare/README.md`](compare/README.md) | A compare doc opens, closes, changes status | 2026-08-09 | Seven v0.30 forks; verdict-first convention |
| [`compare/*.compare.md`](compare/) | New evidence, verdict change, reopen-trigger fires | 2026-08-09 | `ingest-mode-naming` ⏳ (ADR-0001) · `pruning-criterion` ❌ **falsified** by ADR-0003 · `storage-architecture` carries a **size amendment** |
| [`adr/`](adr/) | A feature completes (one ADR per feature) | 2026-08-10 | **Renumbered from 0001 for v0.30** (README has the policy): 0001 naming (proposed) · 0002 P1 INCONCLUSIVE · 0003 **P1 FAIL / option E** · **0004 index format & committed store, accepted**. Archived v0.26 ADRs cited as "archived ADR-NNNN" |
| [`handoff/`](handoff/) | A feature enters build (handoff + prompt pair) | 2026-08-10 | M0/M1 pair (**executed** — ADR-0004) + M1-rerun pair (executed) + two CLAUDE.md diffs (the full M0a rewrite, proposed; a small M1 build/test-section update, also proposed) |
| [`INTERVIEW.md`](INTERVIEW.md) *(reset block)* | The reset block leads the doc; update on direction change | 2026-08-09 | Everything below the block is archived history and says so |
| [`proposals/`](proposals/README.md) | An idea is parked, graduates, or is rejected | 2026-08-10 | **3 filed this session** from the agent-search-API landscape research: `agent-search-landscape` (research note + evidence base), `caller-set-freshness-policy` and `token-budget-retrieval` (both graduate into the M4/W-24 handoff). Prior set unchanged: 4 filed 2026-08-09 (mcp-adapters, knowledge-ci, wavelet-self-index, query-log-pruning) + 3 carried; v0.26-era moved to archive |
| [`conformance/`](conformance/README.md) | Every measurement run — report + ANALYSIS + evidence | 2026-08-09 | Two runs filed: `2026-08-09-pruning-eval` (INCONCLUSIVE) and `2026-08-09-pruning-rerun` (**FAIL**) |
| [`../tools/pruning-eval/`](../tools/pruning-eval/README.md) | The gate's definitions change (they must not) or a selector is ported | 2026-08-09 | Two **frozen** pre-registrations (v1, v2), both committed before their first number; 50 tests; corpus acquisition + 3 diagnostics |
| [`archive/`](archive/README.md) | Something is implemented or superseded | 2026-08-10 | Empty; its README records **where the v0.26 doc set actually lives** (`archive/v0.26-docs/`) — a reset discrepancy left for Arpit to resolve. **M1's R2 measured its downstream effect:** one frozen citation target is unreachable from configured sources until this moves (ADR-0004) |
| `../.github/` | Required checks, release path change | 2026-08-10 | Workflow YAML already targeted the new tree; restored `scripts/ai-review.sh` + `apply-branch-protection.sh`, which the live CI referenced but were missing from the tree since the v0.26 archive move |
| [`../examples/playground/PLAYGROUND.md`](../examples/playground/PLAYGROUND.md) | The fixture corpus or its walkthrough commands change | 2026-08-10 | New row. Every command verified to actually run; fixed a stale "16 shards" comment and a hardcoded example shard path that didn't exist under the real (sparse, fixed-256) assignment |

## How agents use this file

1. **At task end:** scan the trigger column; if your change fired a
   trigger, update that doc and bump its row. CLAUDE.md binds you to this.
2. **Adding a doc:** new maintained doc → new row, in the same change that
   creates it. Archiving a doc → retire its row, same change.
3. **No ⚠ rows remain** — the two stale rows (CLAUDE.md, GLOSSARY.md) were
   cleared by W-03 on 2026-08-09; GLOSSARY was rewritten and CLAUDE.md's
   rewrite was proposed for review. **Correction (2026-08-10):** CLAUDE.md's
   row previously said the rewrite was "adopted" — the file itself still
   carries a "PROPOSED — not in force" header, so it has not been; fixed
   above. Adoption is Arpit's call and unchanged by this session.
