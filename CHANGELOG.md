# Changelog

All notable changes to **fux-engine**. Dates are ISO; versions follow semver.

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
