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
| [`../CLAUDE.md`](../CLAUDE.md) | Scope, constraints, lifecycle, or layout changes; new durable session learnings | 2026-07-22 | Binding; also auto-folded per the standing rule |
| [`index.md`](index.md) | Bundle contents change (new/moved/removed docs) | 2026-07-22 | OKF bundle root; declares okf_version |
| [`example/index.md`](example/index.md) | A doc is added/removed under `example/` | 2026-07-22 | Per-dir OKF index for the examples bundle |
| [`../README.md`](../README.md) | Install/use surface, commands, guarantees change | 2026-07-22 | Public front door; story-first format per the old build's README |
| [`../DOGFOOD.md`](../DOGFOOD.md) | v1 use surface changes; dogfood learnings land | 2026-07-21 | 10-min Anton quickstart (master-prompt rule 6) |
| [`PLAN.md`](PLAN.md) | Any design decision, scope change, status change | 2026-07-22 | Design of record |
| [`INTERVIEW.md`](INTERVIEW.md) | Direction/strategy/major decision changes | 2026-07-22 | Succession record; add yourself to maintainer line |
| [`WORKLOG.md`](WORKLOG.md) | **Every substantive exchange** (append) | 2026-07-22 | Rolling session handoff; ALL-CAPS = no frontmatter |
| [`IMPLEMENTATION.md`](IMPLEMENTATION.md) | **Every execution, whatever the outcome** (complete/blocked/failed/interrupted) | 2026-07-22 | Live build tracker; ALL-CAPS = no frontmatter; deviations logged |
| [`../CHANGELOG.md`](../CHANGELOG.md) | Every version bump; latest entry mirrored into README | 2026-07-22 | Root file; keep-a-changelog style |
| [`example/CLI.md`](example/CLI.md) | Any command/flag/output-format/exit-code change | 2026-07-22 | UX contract; e2e goldens derive from it — update together; ALL-CAPS = no frontmatter |
| [`GLOSSARY.md`](GLOSSARY.md) | A new recurring term enters the repo, or a defined term changes meaning | 2026-07-22 | Definitions link to owning docs; ALL-CAPS = no frontmatter |
| [`example/TOML.md`](example/TOML.md) | Any config key added/renamed/re-defaulted | 2026-07-22 | The annotated example config (fenced example + prose per key); asserted against the parser by tests/test_config.py; ALL-CAPS = no frontmatter |
| [`example/SETUP.md`](example/SETUP.md) | Any `fux setup` flag, generated agent/skill/hook file, or hook I/O change | 2026-07-22 | Setup variants + hooks install; quotes real output; ALL-CAPS = no frontmatter |
| [`example/SKILLS.md`](example/SKILLS.md) | Skill content (`agents/generate.py`) or `fux ask --json` shape change | 2026-07-22 | The two shipped skills verbatim + usage flow; ALL-CAPS = no frontmatter |
| [`example/API.md`](example/API.md) | Any change to `find_root`/`load`/`ingest_paths`/`load_searcher` or `IngestReport`/`ScoredChunk` fields | 2026-07-22 | Programmatic create-file → ingest → query; real output; ALL-CAPS = no frontmatter |
| [`example/DEBUG.md`](example/DEBUG.md) | `[debug]` semantics, `fux doctor` checks, or `fux why` evidence/verdict change | 2026-07-22 | Worked failures + fixes for the five debug questions; new v0.24.0 |
| [`compare/README.md`](compare/README.md) | A compare doc opens, closes, or changes status | 2026-07-21 | Decision index |
| [`compare/*.compare.md`](compare/) | New evidence, verdict change, or reopen-trigger fires | 2026-07-21 | One per decided fork |
| [`adr/`](adr/) | A feature completes (one ADR per feature) | 2026-07-22 | 0001–0012 (v1 + v1.1 + v2 + v3 substrate + v3.1 debug & observability) |
| `handoff/` | A feature enters build (handoff + prompt pair) | 2026-07-22 | empty — v0.20–0.24 all archived by version |
| [`proposals/`](proposals/README.md) | An idea is parked, graduates, or is rejected | 2026-07-21 | `status:` frontmatter tracks lifecycle |
| [`archive/`](archive/README.md) | A handoff/prompt/proposal is fully implemented | 2026-07-22 | Version-named (`vX.Y.Z-name.md`) per CLAUDE.md; master-prompt unversioned; ADR links in frontmatter |
| `tests/` + e2e suite docs | Any behaviour change | 2026-07-22 | 417 unit + 100 e2e (+1 gated skip); goldens via FUX_UPDATE_GOLDENS=1 only |
| [`../tests_e2e/eval/README.md`](../tests_e2e/eval/README.md) | Eval pairs/metrics/gate change | 2026-07-21 | The v2 gate + Anton private-eval workflow |
| [`../tools/distill/README.md`](../tools/distill/README.md) | Model recipe, format, or teacher changes | 2026-07-21 | Pinned distillation recipe (ADR 0006) |
| `../.github/` (ci/publish + branch-protection.json) | Required checks, release path, or the wall change | 2026-07-22 | **No required checks as of 2026-07-22** (Arpit): "fux gate"+"ai-review" still run on every PR but no longer block merge; wall = enforce_admins + no force-push/deletion only. Release → OIDC PyPI publish |

## How agents use this file

1. **At task end:** scan the trigger column; if your change fired a trigger, update
   that doc and bump its row. CLAUDE.md binds you to this.
2. **Hook prompt (once wired):** the session-end hook reads this table, diffs changed
   files against triggers, and *prompts* "these docs look affected — update them?"
   Fail-open, advisory: the hook nags, it never blocks.
3. **Adding a doc:** new maintained doc → new row, in the same change that creates it.
