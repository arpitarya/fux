# Changelog

All notable changes to **fux-engine**. Dates are ISO; versions follow semver.

## [0.17.2] — 2026-07-01 — error-contract consistency (fux-lab Cycle 1)

The `fux-lab` harness's Cycle-1 pass (deepened with 20 behavioral oracles) showed
the `why <unknown>` error-contract bug fixed in 0.17.1 was **systemic**: several
commands printed `fux: <msg>` to **stdout** and returned 1, bypassing the
`FuxError` boundary. All now raise `FuxError`, so `main()` renders the documented
terse `error: …` on **stderr** (exit 1):

- `explain <unknown-term>`, `path <unresolved-endpoint>`, `query <no-match>`
- `seal` (no ids / no `--all`), `candidates accept|reject` (missing/unknown id,
  cannot-accept, already-exists)
- `fetch-rules` (missing file / fetch error), `ingest --connector` (unbounded query)

Also: `path` with valid-but-disconnected endpoints is a legitimate empty result
and now exits **0** (was 1). Regression tests parametrized over the affected
commands; `test_ingest_connector.py` / `test_fetch_rules.py` updated. Full suite:
371 passed. `$0`/stdlib, no behaviour change beyond the error channel/exit codes.

## [0.17.1] — 2026-07-01 — harness-driven fixes: error contract + seal stability

Two real engine bugs surfaced by the new external `fux-lab` end-to-end harness
(exhaustive, offline, `$0` — drives every `fux/registry.py` command, diffs golden
output, springs worktree-isolated traps + negative guards), both fixed with tests:

- **Error contract** — `fux why <unknown-id>` printed `fux: no rule '…'` to stdout
  and returned 1, bypassing the `FuxError` boundary. It now raises `FuxError`, so
  `main()` renders the documented terse `error: …` on **stderr** (exit 1).
- **Seal stability** — `fmwrite._scalar` emitted a *string* `"true"` as bare
  `true`, which the reader re-parsed as a bool; for a ratified rule's
  quoted-boolean example that changed `content_seal` and raised a **false
  `tampered`**. The writer now quotes any string whose bare form would re-parse as
  a non-string (bool/null/list), making `dump → split` a fixed point of the reader.

Additive, `$0`/stdlib, no behaviour change beyond the two fixes. Full suite: 366
passed. The `fux-lab` harness re-runs at 0 findings.

## [0.8.0] — 2026-06-21 — Solar Terminal viewer: fast, legible, governance-aware

The interactive `graph.html` viewer was reworked end-to-end so it stays smooth at
thousands of nodes and turns from eye-candy into a decision tool. Additive and
backward-compatible — `graph.json` gains two rule-node fields; upgrading is a CLI
no-op. Still zero runtime deps, one self-contained offline file, deterministic `$0`
build, same Solar Terminal look.

### Added
- **Macro LOD** — below `view.k < 0.4` each community collapses to one blob (area ∝
  member count, community-coloured, amber-cored if it holds knowledge) behind a faint
  **convex-hull territory** with a top-centrality label; individual nodes return on
  zoom-in (`drawMacro`/`macroRollup`/`convexHull`).
- **Coverage lens** — tints code warm when a rule touches it (via `governs`/`related`/
  `references`/`implements`), cold-grey when ungoverned, so the governed/ungoverned
  split reads at a glance. Client-only, no data change.
- **Governance overlay** — rules whose **AST seal has drifted** pulse red and
  **constitutional**-tier rules wear a crown. Driven by two new `graph.json` rule-node
  fields, **`drift`** and **`tier`**, stamped by `graph.build` from the existing
  `seal`/`check` pass — `$0`, deterministic, never a model. `drift` equals `fux check`'s
  `unsealed` set exactly (`graph._drift_of` mirrors `check._seal`/`seal.current`).

### Changed
- **Layout + render rewritten for scale** — a hand-rolled **Barnes–Hut quadtree**
  (O(n log n), θ≈0.8) replaces the O(n²) repulsion loop; the draw path adds viewport
  culling, pre-rendered amber glow sprites + a two-pass governs-thread stroke (no
  per-frame `shadowBlur`/gradients), a cached visible-node list, and an offscreen
  static-substrate cache blitted when idle. On the largest test graph (~2,356 nodes /
  14,744 edges) median frame time dropped **~38 ms → ~5 ms** active and **~1.9 ms**
  idle, with no visual regression.

### Deferred
- **Git-history playback** (animating rules + `governs` threads over commits) — noted
  as a follow-up, not built.

## [0.7.0] — 2026-06-21 — optional cage token-savings receipt + docs reorg

### Added
- **Cage token-savings receipt** — optional per-session savings attribution from the
  Cage ledger.

### Changed
- **Docs reorganised.** No engine/command/schema change beyond the above.

## [0.6.2] — 2026-06-19 — README copy edit

Docs-only. No engine, command, schema, or dependency change — upgrading is a CLI no-op.

### Changed
- **README "story" intro reworded** — a sharper opening line for the red-pipe story.

## [0.6.1] — 2026-06-18 — README rewrite (the red-pipe story)

Docs-only. No engine, command, schema, or dependency change — upgrading is a CLI no-op.

### Changed
- **README rewritten** around the "red pipe" story: a tighter value proposition, a
  `fux why day-pnl` walkthrough as the lead example, shields.io badges, an
  explain-like-I'm-five section, a constitution overview, a collapsible full command
  surface, an honest-limits section, and a "what's new" digest. The absolute-URL PNG logo
  (so it renders on PyPI) and all doc links are preserved.

## [0.6.0] — 2026-06-18 — the wall is real (review, ratify-through-PR, drift audit)

Completes the enforcement hardening begun in 0.5.1: a **second required check**, a
distinct agent author identity, the amendment ritual that **opens its own gated PR**, and a
**scheduled drift audit** for the one setting Fux can't seal. Branch protection is now two
required checks + `enforce_admins` + a watched source-of-truth config. Adopting is still a
CLI no-op unless you opt into the constitution layer; `fux ratify` gains PR-routing behaviour.

### Added
- **`ai-review` as a second required CI check** (`.github/workflows/ci.yml`,
  `scripts/ai-review.sh`) — a *separate reviewer identity* reviews the PR diff against the
  constitution and **refuses (exit 3) when reviewer == PR author** (separation of duties,
  §2R.1). Model-free per the engine's non-negotiables: it is `fux gate` + `fux critic` on the
  diff — the second set of eyes a solo author's missing approval would otherwise provide. Its
  check context is the bare job name **`ai-review`**.
- **`fux ratify … [--no-pr]` routes through a gated PR** (`fux/cliconstitution.py`,
  `fux/gitutil.py`) — on the protected branch with a remote, ratify writes on a new
  `constitution/<id>` branch and opens a PR automatically (deterministic git/gh, no model), so
  a ratification can never land on `main` directly (§2g). `--no-pr` does a local/offline
  in-place ratify.
- **Branch-protection drift audit** — `scripts/audit-branch-protection.sh` +
  `.github/workflows/audit-protection.yml` (weekly) + a `just audit-protection` recipe assert
  the required contexts + `enforce_admins=true` and **fail loudly** on any diff vs the committed
  `.github/branch-protection.json` (source of truth). The audit needs an admin-scoped
  `BRANCH_PROTECTION_TOKEN` secret in CI (the default `GITHUB_TOKEN` can't read protection) and
  exits non-zero rather than passing silently if it can't.
- **`.github/CODEOWNERS`** routing `/.fux/` + `constitution.lock` to the human maintainer
  (constitutional paths get human judgment; enforced as a required code-owner review once a
  second maintainer joins, §2R.2).
- **Distinct agent git identity** — `scripts/git-identity-claude.sh` + `.gitmessage-claude`
  give Claude Code the author `Claude (agent) <claude-code@fux.local>` and an
  `Agent: claude-code` commit trailer for auditable authorship. **No GitHub account created**
  (§2R.3; the GitHub-App / bot path stays deferred, §2R.4).

### Changed
- `.github/branch-protection.json` now requires **two** checks (`fux gate` + `ai-review`).
- `/fux debate` skill + `docs/cli.md` document the ratify→PR routing.

## [0.5.1] — 2026-06-18 — the gate is now a real wall

Infrastructure-only: makes the constitutional `fux gate` a **required, merge-blocking
status check** on `main`, closing the load-bearing gap from the enforcement handoff. No engine
behaviour, command, or schema change — upgrading is a no-op for the CLI.

### Added
- **`fux gate` as a required CI check** (`.github/workflows/ci.yml`) — a new `gate` job runs
  `fux gate` on every PR; its check context is the bare job name **`fux gate`**. A red/pending
  gate now blocks merge.
- **Branch protection as code** (`.github/branch-protection.json`) — the diffable source of
  truth for `main`: required `fux gate` check (`strict`), `enforce_admins: true`, no
  force-push/deletion. `required_pull_request_reviews` is `null` on purpose (solo repo: a sole
  developer can't approve their own PR). Every change now routes through a green-gate PR — no
  direct commits to `main`, including by admins.
- **`scripts/apply-branch-protection.sh OWNER REPO BRANCH`** — one-command reproducible apply
  of the checked-in protection config.

## [0.4.0] — 2026-06-17 — the constitutional-app engine

Fux becomes a **constitutional-app engine**: an optional, additive governance layer on the
existing frontmatter substrate, with `$0` deterministic enforcement and the LLM surface gated
behind an opt-in extra. **Adopting this release is a no-op until you opt in** — `tier` defaults
to `standard`, nothing auto-promotes, and every existing rule stays valid and untagged.

### Added
- **Tiered governance** — a rule's `tier` (`constitutional` · `standard` · `advisory`) sets how
  hard it bites. Constitutional findings block in any `mode`; standard only under `strict`;
  advisory warn. Enforced deterministically in `fux/findings.py`.
- **Tamper-evidence + ratification** (`fux/constitution.py`) — a ratified constitutional rule
  carries `ratification.{by,date,content_seal,debate_hash?}` and is recorded in a committed
  **`.fux/constitution.lock`**. `fux check` recomputes both each run → an always-blocking
  `tampered` finding on any in-place edit, add, delete, or re-stamp outside the ritual.
- **`fux ratify <id> [--by] [--date] [--debate FILE]`** — the only path into the constitutional
  tier (deterministic, no LLM): stamp ratification, freeze the code seal, write the lock.
- **`/fux debate "<rule>"`** skill — author a rule via a two-agent free debate (no assigned
  sides, blind first passes, anti-sycophancy gates, human as tie-breaker/ratifier); the
  transcript is hashed into `ratification.debate_hash`. Fux spends nothing — the host session's
  tokens do the thinking.
- **Deterministic / judgment split** — `principle` + `enforcement` (`deterministic|judgment`)
  fields (both optional). A `$0` router (`fux/critic.py`) keeps `deterministic` principles
  (money/PII/numbers) off the AI path and never fakes a `judgment` principle as a machine check.
  `fux check` emits an advisory `untagged-candidate` to guide backfill (never blocks).
- **Critic loop** (`fux/criticloop.py`) + **`fux critic "<change>"`** — at the action boundary:
  gather principles → deterministic pass first (blocks, no LLM) → host-agent self-critique of
  judgment principles → record to `.fux/out/critic.jsonl`. The `critic` skill drives the bounded
  revise / escalate / debate loop.
- **`[critic]` opt-in extra** (`anthropic`) — a headless AI self-critique backend
  (`fux/criticllm.py`) for no-session/runtime use; lazily imported, never on the maintenance
  path. Mirrors `[embeddings]`.
- **Report-first coverage gate** — `fux gate` reports every `important_globs` path governed by
  zero rules (never blocks on adoption).
- **§5b migration guard** — `fux check --baseline-write <file>` snapshots findings; `fux gate
  --baseline <file>` fails only on findings *new* since the snapshot. A transient upgrade check.

### Changed
- `fux gate` blocking is now **tier-aware** and reads the project `mode`; `fux check` output is
  **canonically sorted** (kind, rule_id, message). `cmd_ratify`/`cmd_critic` live in
  `fux/cliconstitution.py`.

### Guarantees held
- `dependencies = []` — stdlib only; the LLM surface is an extra. A guard test asserts no
  maintenance-path module imports a model client and the default install is model-free.
- Deterministic: same rules + code ⇒ identical findings/verdicts. 195 tests.
