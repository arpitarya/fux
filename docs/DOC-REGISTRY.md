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
| [`../README.md`](../README.md) | Status, guarantees, reading order change | 2026-08-12 | Status line: "T0 slice: ingest + ask work on this repo" (M0+M1 shipped); gained a **`.fux/` layout table** and the new URL paths (ADR-0011). **Reading-order item 5 repointed at the **`fux-playground` sibling repo** (ADR-0012); `examples/` deleted from this tree.** |
| [`../.fux/README.md`](../.fux/README.md) | The `.fux/` layout table changes (a plane is added, renamed, or flips committed/derived) | 2026-08-11 | New row. **Generated** by `store/fuxdir.py` at ingest, write-if-missing — edit the generator, not the file; a consumer's copy is never overwritten (ADR-0011) |
| [`../CHANGELOG.md`](../CHANGELOG.md) | A release-worthy change lands | 2026-08-11 | **Released as `0.30.0`** (M0 scaffold + M1 T0 slice); `[Unreleased]` now carries ADR-0010 + **ADR-0011** (`.fux/` layout, URL-source relocation, breaking + unshimmed) |
| [`index.md`](index.md) | Bundle contents change | 2026-08-09 | OKF bundle root |
| [`architecture.svg`](architecture.svg) + [`architecture-overview.svg`](architecture-overview.svg) | Any tier/record-shape/query-path change (detailed) · any component add/remove (overview) | 2026-08-12 | Rev-2 pair: overview (5 components) + detailed; rev-1 pair archived. Build-order caption no longer names the deleted AcmePay fixture. |
| [`PLAN.md`](PLAN.md) | Any design/scope/status change | 2026-08-09 | The build of record; agent quick-ref section at top |
| [`open/`](open/README.md) | **An item opens or closes** — its file is created with its index row and **deleted with it** | 2026-08-12 | New row. One file per open `W-nn`; holds open work only, which is the property that makes `OPEN-WORK.md` trustworthy. Closed items leave no tombstone here. |
| [`OPEN-WORK.md`](OPEN-WORK.md) | **Any work item or prediction changes state** | 2026-08-12 | **Restructured 2026-08-12 into an index**: one line per open item, detail in [`open/`](open/README.md), **every DONE item purged** (W-20/21/40/41 rows deleted — their record is the ADR + WORKLOG). Open set is W-22 (next) · W-23…W-27 · W-30/31/32/33 (human) · W-42 · W-43 · W-38 parked. |
| [`paper/the-fux-index-paper.md`](paper/the-fux-index-paper.md) | Architecture changes; a P-prediction gets measured (M7 updates §5–6 to measured) | 2026-08-09 | Architecture of record + figures |
| [`INTERVIEW.md`](INTERVIEW.md) | Direction/strategy/major decision changes | 2026-08-11 | Succession record; the reset is a mandatory entry. **+ADR-0011 entry** (the ignore-rule failure mode; the opaque-config-table line to hold) |
| [`WORKLOG.md`](WORKLOG.md) | **Every substantive exchange** (append) | 2026-08-12 | Rolling session handoff |
| [`GLOSSARY.md`](GLOSSARY.md) | New recurring term, or a term changes meaning | 2026-08-12 | **+4 terms** (`.fux directory`, `derived plane`, `middleware (URL)`, `url source`) — paying ADR-0010's recorded debt; fixed a stale "numbering continues at 0016" line. Rewritten for v0.30 (index vs db, ledger, keyspace, wire/runtime, refer/snapshot, inferred/enriched, pruning, ARC); archived v0.26 terms marked not-current. **+3 terms** (`playground`, `golden query`, `known failure / xfail`) from ADR-0012. |
| [`compare/README.md`](compare/README.md) | A compare doc opens, closes, changes status | 2026-08-09 | Seven v0.30 forks; verdict-first convention |
| [`compare/*.compare.md`](compare/) | New evidence, verdict change, reopen-trigger fires | 2026-08-09 | `ingest-mode-naming` ⏳ (ADR-0001) · `pruning-criterion` ❌ **falsified** by ADR-0003 · `storage-architecture` carries a **size amendment** |
| [`adr/`](adr/) | A feature completes (one ADR per feature) | 2026-08-12 | **Renumbered from 0001 for v0.30** (README has the policy): 0001 naming (proposed) · 0002 P1 INCONCLUSIVE · 0003 **P1 FAIL / option E** · **0004 index format & committed store, accepted** · **0010 URL source via consumer middleware, ⏳ proposed — amended in place by 0011** · **0011 `.fux/` directory layout, ⏳ proposed** (0005–0009 remain reserved for M2–M6 per OPEN-WORK DoDs). Archived v0.26 ADRs cited as "archived ADR-NNNN". **+ADR-0012** (playground leaves the repo, accepted). README now flags the unresolved 0012-vs-0016 numbering contradiction with CLAUDE.md. Broken relative link to the archived ADR path fixed (`../` → `../../`). |
| [`handoff/`](handoff/) | A feature enters build (handoff + prompt pair) | 2026-08-12 | **Archive-law debt paid (W-43, closed 2026-08-12):** the executed M1-T0-slice and fux-playground pairs moved to `archive/`, so this directory now lists **live work only** — one live pair (v0.32.0 open-items) plus three proposed CLAUDE.md diffs. README restructured into live / proposed-diffs / executed-and-where-they-went sections and its "root archive" wording corrected. |
| [`INTERVIEW.md`](INTERVIEW.md) *(reset block)* | The reset block leads the doc; update on direction change | 2026-08-09 | Everything below the block is archived history and says so |
| [`proposals/`](proposals/README.md) | An idea is parked, graduates, or is rejected | 2026-08-10 | **3 filed this session** from the agent-search-API landscape research: `agent-search-landscape` (research note + evidence base), `caller-set-freshness-policy` and `token-budget-retrieval` (both graduate into the M4/W-24 handoff). Prior set unchanged: 4 filed 2026-08-09 (mcp-adapters, knowledge-ci, wavelet-self-index, query-log-pruning) + 3 carried; v0.26-era moved to archive |
| [`conformance/`](conformance/README.md) | Every measurement run — report + ANALYSIS + evidence | 2026-08-09 | Two runs filed: `2026-08-09-pruning-eval` (INCONCLUSIVE) and `2026-08-09-pruning-rerun` (**FAIL**) |
| [`../tools/pruning-eval/`](../tools/pruning-eval/README.md) | The gate's definitions change (they must not) or a selector is ported | 2026-08-09 | Two **frozen** pre-registrations (v1, v2), both committed before their first number; 50 tests; corpus acquisition + 3 diagnostics |
| [`archive/`](archive/README.md) | Something is implemented or superseded | 2026-08-12 | **Three executed pairs** now, all stamped `status: implemented` + ADR link: v0.30.0 M1-T0-slice (ADR-0004), v0.31.0 `.fux`-layout (ADR-0011), v0.31.0 fux-playground (ADR-0012). README rewritten with a **two-archives table** (root `archive/` = old *builds*; `docs/archive/` = completed *doc artifacts*) and the **reset discrepancy recorded as resolved** — Arpit's 2026-08-10 ruling scoped the v0.26 doc set, which is why `docs/archive/` still exists. The paragraph is kept rather than deleted because ADR-0004 §Consequences cites it as the reason R2-Q3 was unanswerable at M1 |
| `../.github/` | Required checks, release path change | 2026-08-10 | Workflow YAML already targeted the new tree; restored `scripts/ai-review.sh` + `apply-branch-protection.sh`, which the live CI referenced but were missing from the tree since the v0.26 archive move |
| *(the demo corpus)* | — | 2026-08-12 | **Row retired.** `examples/playground/` was deleted and rebuilt as the sibling repo `fux-playground` ([ADR-0012](adr/0012-playground-sibling-repo.md)). It is a separate repository with its own docs, so it has no row here; the fux-side contract is ADR-0012 plus README reading-order item 5 |

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
