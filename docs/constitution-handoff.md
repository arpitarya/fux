# Fux Constitutional-App Engine — Claude Code Build Handoff

**Owner:** Arpit · **Build site:** `fux` repo · **Flagship consumer:** `anton`
**Driving model:** Claude Code / Cowork. This is a build spec, not a discussion.
**Supersedes** the earlier substrate-only version of this file. Execution prompts: `docs/constitution-prompts.md` (regenerate to match this doc before running).

---

## 0. The one idea that makes everything else work

> **Fux never makes an API call. The host agent — Claude Code or Cowork, which the user already pays for — does the thinking. Fux is the deterministic harness around it.**

This is what lets a debate engine and a critic live *inside* Fux while Fux stays `$0`. The *intelligence* (debate, critique, revision) is the agent's tokens; the *rule-making, sealing, enforcement, and audit* are Fux's deterministic stdlib core. Fux's maintenance/enforcement path must never `import` a model. Cage meters the agent's tokens for visibility — that spend is the agent's, not Fux's. This extends the existing pattern of `/fux propose` and `/fux distill`, which already ride the open session.

If any instruction below seems to require Fux to call an LLM itself, you have misread it — stop and re-read.

---

## 1. What you are building

A **constitutional app** in the Constitutional-AI sense: an explicit, inspectable, editable set of principles (the constitution), plus a loop that **critiques a proposed action against the relevant principles and revises it before the action lands** — with deterministic enforcement for hard invariants and AI self-critique only for judgment calls. Principles are authored by a **two-agent debate** and ratified by a human.

Three layers, built in this order of dependency:

1. **Substrate + integrity** (deterministic, `$0`) — the constitution as data, made tamper-evident and amendable. *Foundation.*
2. **Debate engine** (agent-driven, `$0` to Fux) — how a principle becomes law. *Authoring.*
3. **Critic loop** (deterministic core + AI edge) — how principles govern actions at runtime. *Enforcement / the headline.*

---

## 2. Non-negotiables (from `fux/CLAUDE.md` — do not violate)

- `$0`, **stdlib only** on the maintenance/enforcement path. LLM use happens **only** inside agent-driven skills (`/fux debate`, `/fux propose`) that ride the host session — never in `check`/`gate`/`verify`/`seal`/`constitution`/`critic`/hooks.
- The LLM critic and debate ship as an **opt-in extra** (like the existing `[embeddings]` extra), never on the default import path.
- Deterministic: same rules + code ⇒ same findings/verdicts. No clocks/random in derived output.
- Files ≤ 100 lines (≤ 50 for `*_utils`). Python ≥ 3.11. No new runtime deps.
- **Docs in sync in the same change:** `docs/fux-plan.md`, `docs/fux-implementation.md`, `README.md` (if surface changes), `docs/cli.md` (commands), and a test in `tests/`.

---

## 3. The governance model (read before designing)

Two **orthogonal** axes — do not conflate them:

- **Coverage** = how much of the project is governed. Goal: **total**. Every path in `important_globs` maps to ≥ 1 rule. Enforced by a coverage gate (§7e).
- **Severity** = how hard a rule bites. Goal: **tiered**. A thin constitutional apex blocks unconditionally; standard rules block under the gate; advisory rules warn.

The pyramid (all three tiers *govern*; they differ only in amendment difficulty and enforcement):

- **Constitutional** (thin apex): the must-never-break invariants — determinism, money/PII, audit, and the amendment process itself. Ratified, supersession-only, always blocks regardless of `mode`.
- **Standard** (the bulk): conventions, ADRs, domain rules. Block under `gate`/strict; change via normal PR + `fux check`.
- **Advisory** (base): style nudges, memories. Warn only.

Cross-cutting split, applied to every principle:

- **`deterministic`** principles have a `check:` / seal / matcher and are enforced with **no LLM** (money, PII, audit, numbers). They may *never* be routed to the AI critic.
- **`judgment`** principles (tone, completeness, grounding, "did this hedge appropriately") are enforced by AI self-critique. They may *never* be faked as deterministic.

This split is your deterministic-core / probabilistic-edge law, made a schema field.

---

## 4. Packaging & positioning (ratified decisions — build to these)

- **Packaging:** the debate + critic live **inside Fux**, as agent-driven skills + a deterministic harness, gated behind an opt-in extra. One tool, one story, one install. Fux stays `$0` because the agent does the thinking (§0).
- **Positioning:** Fux is **the constitutional-app engine**. Anton is its flagship.
- **Anton's scope:** Anton is a **constitutional app at its core** (financial decisions, numbers, recommendations, PII, audit) and a **normal app at its edges** (UI chrome, convenience). Do not make every Anton feature constitutional — that crushes velocity. Govern where trust lives.

---

## 5. Rollout sequence (the app already exists — this matters)

Build-agent governance only covers *new* code. Anton already runs, so:

1. **Build-agent critic first — the rehearsal.** Claude Code/Cowork critique their own proposed changes against the constitution before committing. Cheap, safe place to author and calibrate the constitution and stop new features adding violations.
2. **Audit sweep — brings the existing app in.** Point the calibrated critic over existing Anton once; surface where current behavior already violates principles; fix the real ones. You do *not* re-run build agents over old code — you audit it.
3. **Runtime critic — the lasting protection.** Add the critic in front of Anton's riskiest live paths first (money, PII), then widen. It governs old and new code equally because it inspects behavior, not authorship.

---

## 5b. Migration & backward compatibility (no surprise breakage)

Adopting the new `fux-engine` on a repo that already has rules (fux's own `.fux/`, Anton's `.fux/rules` + glossary + memory) must change **nothing** about existing behavior until you deliberately opt in. Guarantees the build must honor:

- **Additive, optional schema.** `tier` / `principle` / `enforcement` / `ratification` are all optional. `tier` defaults to `standard`; absent `principle`/`enforcement` means "not critic-governed." Every existing rule stays schema-valid with zero edits — test this explicitly.
- **No auto-promotion.** Upgrading promotes *nothing* to constitutional. The constitution and `constitution.lock` start empty except what you ratify by hand. No existing rule changes tier on upgrade.
- **Standard-tier behavior is unchanged.** A `standard` rule under the new gate blocks exactly when it did before (kind-based, under strict/`mode`). Tamper/seal/lock checks apply to constitutional rules only, so existing unsealed rules are untouched.
- **Coverage gate ships report-first.** On a repo with many ungoverned `important_globs`, coverage must *report*, not block, on first adoption — opt into blocking later, by tier. Otherwise the upgrade floods Anton with blockers.
- **Backfill is deliberate, not scripted.** Tagging existing rules with `principle`/`enforcement` (deterministic vs judgment) is a human/debate call, never auto-guessed. `fux check` emits an *advisory* "untagged-candidate" finding listing rules that look like they should carry a principle, so you backfill systematically. Reuse `importer.py` / `parity.py` for any bulk validation.

**Migration gate (mandatory, runs before every adoption).** Enforced by a small deterministic helper, not a manual procedure — "no surprise breakage" must be CI-testable:

- `fux check --baseline-write <file>` snapshots current findings (canonically ordered: kind, rule_id, message) to `<file>`.
- `fux gate --baseline <file>` re-runs, diffs against the snapshot, and **exits 2 on any new *blocking* finding** (new advisories are ignored — expected during migration).
- Implementation: a `baseline.py` helper (≤ 50 lines, utils-style) reusing the existing `Finding` serialization; `check` findings must be canonically sorted for the diff to be meaningful (part of this work). No new deps.
- **Anti-gaming:** the baseline is captured *pre-upgrade*, committed to the upgrade PR, and enforced in that PR's CI — it cannot be regenerated to hide a regression without that being visible in the same diff a reviewer sees.
- **Scope:** a transient migration guard (captured for the upgrade, enforced in that PR, retired once green) — *not* a permanent regression-tracking subsystem. It generalizes later; do not build that now.

A non-empty blocking diff means the upgrade is not backward-compatible — fix the engine, not the repo.

---

## 6. Schema additions (`fux/data/schema.json`)

```jsonc
"tier":        { "type": "string", "enum": ["constitutional", "standard", "advisory"] }, // default "standard"
"principle":   { "type": "string" },   // the natural-language norm the critic reasons about
"enforcement": { "type": "string", "enum": ["deterministic", "judgment"] }, // §3 split
"ratification": {
  "type": "object",
  "required": ["by", "date", "content_seal"],
  "properties": {
    "by":           { "type": "string" },   // human ratifier (Arpit)
    "date":         { "type": "string" },   // ISO date
    "content_seal": { "type": "string" },   // hash of normalized body + governing fm (tamper)
    "debate_hash":  { "type": "string" },   // hash of the two-agent debate transcript
    "supersedes":   { "type": "array", "items": { "type": "string" } }
  }
}
```

---

## 7. Component specs

### 7a. Integrity layer — tier, tamper, ratify, lock (deterministic, `$0`)
- `tier` enforced in `fux/findings.py`: any finding against a `constitutional` rule blocks unconditionally regardless of `mode`; `standard` keeps kind-based blocking under strict; `advisory` warns. `unsealed` becomes blocking for constitutional rules.
- New `fux/constitution.py` (≤ 100 lines): `content_seal(rule)`, `check_tamper(rules)` → always-blocking `tampered` finding on mismatch, `lock_manifest(rules)` + `check_lock(root, rules)` over `.fux/constitution.lock` (catches add/delete outside the ritual). Reuse `seal.py` normalization; no new deps. Wire into `check.py::run`.
- `fux ratify <id>` (deterministic, no LLM): stamps `ratification.*`, freezes the code seal, updates the lock. **The only path into the constitutional tier.**

### 7b. Debate engine — agent-driven, `$0` to Fux
- Skill `/fux debate "<proposed rule>"`. It drives the host agent to run a **two-agent free debate** (no assigned sides; both peers fluent in building *and* selling).
- **Spawn two sub-agents** (Claude Code Task tool / Cowork Agent tool) for genuine **blind first passes** — each forms a position without seeing the other — then reveal and debate.
- Anti-sycophancy rules: each agent must surface ≥ 1 concrete objection; convergence is only valid after both tried to break the rule; instant agreement on a *constitutional* rule forces one extra adversarial round.
- **Non-convergence escalates to Arpit** with both arguments — he is the tie-breaker and ratifier. The transcript is hashed into `debate_hash`.
- Fux's role is the deterministic harness: capture transcript → hash → hand to `fux ratify`. Fux spends nothing.

### 7c. Critic loop — critique → revise → act
At the action boundary (PreToolUse / pre-commit for build agents; a callable for runtime):
1. **Gather** — Fux recall retrieves the principles relevant to the proposed action.
2. **Deterministic pass first** — run typed `check:` / seals / matchers for `deterministic` principles. Hard invariant violated → block, **no LLM**.
3. **Self-critique** — for `judgment` principles, the agent critiques its *own* proposal against the principle text → verdict + rationale.
4. **Revise** — if flagged, the agent revises and re-runs; bounded iterations; then escalate to a human.
5. **Two-agent debate** — fires *only* on borderline / escalated judgment cases, never on every action (latency + cost).
6. **Act** — only a proposal passing all applicable passes lands.
7. **Record** — verdict + applied principles → audit trail; Cage meters the agent tokens.

### 7d. Opt-in extra
The critic/debate LLM surface ships behind an extra (e.g. `[critic]`), mirroring `[embeddings]`. Default `pip install fux-engine` stays model-free.

### 7e. Coverage gate — total governance
Use existing `coverage.py` / `mine.py` / `impact.py`: `fux gate` reports any path in `important_globs` governed by **zero** rules. **Report-first on adoption** (§5b); opt into blocking by tier later. This is what makes "the documentation governs the whole project" measurable — without flooding an existing repo the day you turn it on.

---

## 8. Phased build + acceptance tests

Run in order; do not start a phase until the previous acceptance test is green. Keep `python -m pytest -q` and `fux build && fux check` green throughout.

**Phase 0 — Amendment article (bootstrap).** Author one constitutional rule `con-amendment` stating: a constitutional rule is created/changed only via propose → debate → ratify; changes only by supersession; ratification needs a named human + recorded debate. Add a "Constitution layer" section to `fux-plan.md`. No enforcement code. *Acceptance:* rule parses; plan updated.

**Phase 1 — Tier + unconditional block.** Implement §6 `tier` + §7a tier enforcement; make `unsealed` blocking for constitutional rules; tests prove a broken ref on a constitutional rule fails `fux gate` (exit 2) with `mode = "fix"`. Also build the §5b migration helper here — `--baseline-write` / `--baseline`, canonical finding ordering, `baseline.py` (≤ 50 lines) — and unit-test it against fux's own `.fux/` rules (bump nothing → empty blocking diff; inject a blocker → exit 2). *Acceptance:* that test is green; standard-rule break does not block outside strict; **backward-compat test** — every existing rule in fux's `.fux/` still parses and produces no new blocking finding under the default `tier`.

**Phase 2 — Self-seal + tamper + lock.** Build `constitution.py` (§7a), `tampered` finding, `fux ratify`, `.fux/constitution.lock`; wire into `check.py`. *Acceptance:* `fux ratify con-amendment`; hand-edit its body → `fux gate` fails `tampered`; restore + re-ratify → green.

**Phase 3 — Debate engine.** Add `/fux debate` (§7b) using spawned sub-agents, blind first pass, escalation to human, transcript hashing into `debate_hash`; `fux ratify` consumes it. Add a guard test asserting no maintenance-path module imports an LLM client. *Acceptance:* a debate produces a transcript + hash; ratify records it; guard test passes; `pip install fux-engine` (no extra) imports with no model deps.

**Phase 4 — Principle tagging + deterministic/judgment split.** Add `principle` + `enforcement` (§6); enforce that `deterministic` principles are never routed to the AI path and `judgment` never faked deterministic. *Acceptance:* a test asserts a `deterministic` principle cannot reach the critic's AI pass.

**Phase 5 — Critic loop (build-agent surface) + coverage gate.** Implement §7c behind the `[critic]` extra at the PreToolUse/pre-commit boundary, deterministic pass first; implement §7e coverage reporting in `gate`. *Acceptance:* a build-agent change violating a `judgment` principle is critiqued and revised before commit; an ungoverned `important_glob` path is reported by `fux gate`.

**Phase 6 — Cut a new `fux-engine` version.** Confirm `pytest -q`, `fux build && fux check`, `fux gate` clean. Bump `fux.__version__` (minor — feature release). Update `README.md`, `fux-implementation.md` (flip items ✅), CHANGELOG. Build; confirm `fux --version`. Do not publish. *Acceptance:* version bumped; docs ✅; package builds.

**Phase 7 — Integrate into Anton (rehearsal stage of §5).** Bump `fux-engine` pin in `anton/pyproject.toml`. **First, run the §5b migration gate via the helper:** `fux check --baseline-write` on the pre-upgrade tree, commit it, bump the pin, then `fux gate --baseline <file>` as a CI step — it must exit 0 (zero new blockers) *before* ratifying anything. A non-empty blocking diff stops the upgrade. Then make Anton's **"never commit money docs / PII; plans live in elgar"** rule the first constitutional rule via `/fux debate` → `fux ratify`; create `anton/.fux/constitution.lock`. Add `just constitution` → `fux gate` as a **required CI check** (CI is the wall; `--no-verify` bypasses local hooks). Update `anton/CLAUDE.md` Must-Know Rules + `anton/docs/guardrails.md`. *Acceptance:* `just constitution` green on clean tree; a staged money/PII violation fails it; lock exists; docs updated.

**Phase 8 — Audit sweep over existing Anton (§5 step 2).** Run the critic across existing Anton once; produce a report of current principle violations on the constitutional paths (money/PII/recommendations/audit); fix the real ones. *Acceptance:* report produced; no unresolved constitutional violations on the covered paths.

**Deferred — runtime critic (§5 step 3).** Expose the critic as a callable in front of Anton's riskiest live paths (money, PII). Not in this build; documented so it isn't dropped.

---

## 9. Review checklist (principal bar, before merging each phase)

- **`$0` held** — no LLM import reachable from `check`/`gate`/`verify`/`seal`/`constitution`/`critic`/hooks; default install is model-free. The Phase 3 guard test must cover this.
- **Determinism** — re-running `fux gate` on an unchanged tree yields identical output.
- **No new runtime deps** — `dependencies = []`; LLM surface is an extra only.
- **Tamper actually proofs** — a constitutional rule's meaning cannot change without `tampered`/`unsealed` firing; try it by hand.
- **Split honored** — money/PII/audit/numbers run deterministically; never through the critic's AI pass.
- **CI is the wall** — `fux gate` is a required CI check in both repos.
- **Audit surface** — `ratification` (by/date/debate_hash) preserved as the "who approved this and why" record.
- **Docs in sync** — plan + implementation + cli + README updated in the same change.
- **Over-build cut** — agents love abstraction; remove anything the phase didn't ask for. Files ≤ 100 lines.

---

## 10. Recovery note

If a session drifts (over-engineers, invents a dep, or routes enforcement through a model), **stop — don't prompt deeper**. Reset context, re-paste the phase spec plus §0 and §2, and restart that phase clean. Three good turns from a sharp spec beat twenty patching a drift.
