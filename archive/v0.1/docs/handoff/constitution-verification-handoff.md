# Fux Constitution — Verification & Hardening Handoff

**Owner:** Arpit · **Repos:** `fux` (engine), `anton` (flagship) · **Driving model:** Claude Code / Cowork.
**Status:** the build plan (`docs/constitution-handoff.md`, Phases 0–9) is implemented. This doc is what you do *after* code — prove it holds, then harden it. Prompts: `docs/constitution-verification-prompts.md`.

---

## 0. Why this exists

A system whose entire claim is *"neither a developer nor an agent can break it"* is **not done when the tests are green.** Green tests verify what you expected; they say nothing about the bypass you didn't think to write a test for. The only proof that matters here is adversarial: someone tried every way in, and each was caught.

Two rules for this phase:

- **Adversarial, not confirmatory.** Don't ask "does it work?" Ask "how do I break it?" and enumerate.
- **Fresh eyes.** Run the red-team and the review in a *new session / subagent*, not the one that implemented the plan. The building session grades its own homework too kindly — confident output looks identical whether it's right or wrong.

---

## 1. What "broken" means (the threat model)

The constitution is broken if any of these slip through without a blocking signal:

- a constitutional rule's **meaning** changes (body / governing frontmatter),
- a constitutional rule is **added or removed** outside `propose → debate → ratify`,
- a rule is **promoted** into the constitutional tier without ratification,
- governed **code drifts** from a constitutional rule's seal,
- the **provenance** (debate transcript) behind a ratified rule is altered,
- a **deterministic** principle (money/PII/audit/numbers) is routed through the probabilistic critic,
- enforcement is **bypassed** (local hook skipped) without the CI wall catching it,
- the **migration baseline** is gamed to hide a regression,
- Fux's **$0 invariant** is violated (a model reachable on the maintenance/default path).

---

## 2. Verification matrix (the core of this phase)

For each attack: the mechanism that must catch it, and the signal you should see. Run every row in `fux`, then the repo-relevant ones in `anton`.

| # | Attack | Must be caught by | Expected signal |
|---|--------|-------------------|-----------------|
| 1 | Hand-edit a ratified constitutional rule's body/fm | `content_seal` → `check_tamper` | `tampered`, gate exit 2 |
| 2 | Add a constitutional rule without `fux ratify` | `check_lock` (not in manifest / no ratification) | blocking lock finding |
| 3 | Edit `.fux/constitution.lock` directly | `check_lock` (recomputed manifest ≠ file) | blocking lock finding |
| 4 | Edit a ratified debate transcript | `provenance-drift` (Phase 3b) | blocking, constitutional only |
| 5 | Promote a standard rule via `tier: constitutional` frontmatter edit | `check_lock` + `check_tamper` (no ratification block) | blocking |
| 6 | Change code so a constitutional rule's seal drifts | `unsealed` (blocking for constitutional) | gate exit 2 |
| 7 | `git commit --no-verify` (skip local hook) | **CI** `fux gate` as a required check | caught at CI, not locally |
| 8 | Regenerate the migration baseline to hide a blocker | **procedural** — baseline committed pre-upgrade; regeneration shows in the PR diff | reviewer sees it (no fired finding) |
| 9 | Route a `deterministic` money/PII principle through the AI critic | enforcement-split guard (Phase 4) | refuses / errors, never reaches AI |
| 10 | `pip install fux-engine` (no extra) and import the maintenance path | import guard test | model-free; no LLM import reachable |
| 11 | Merge a PR while `fux gate` is RED | **CI required check** `fux gate` (branch protection) | merge **BLOCKED**, the check named as the blocker |
| 12 | Direct commit/push to the protected branch (as owner) | branch protection (`enforce_admins`, PR-only) | push **REJECTED** — the only path in is a new branch + PR |
| 13 | Set the `ai-review` reviewer == PR author | `scripts/ai-review.sh` separation-of-duties guard | job **REFUSES** (exit 3), names author==reviewer |
| 14 | Plant a constitutional violation in a PR diff | **CI required check** `ai-review` (`fux gate`/`critic` on the diff) | `ai-review` RED → merge **BLOCKED** |
| 15 | Admin-merge a PR past a red required check | `enforce_admins: true` | merge **BLOCKED** even for an admin |
| 16 | Remove/rename a required check on live protection | scheduled drift-audit (`scripts/audit-branch-protection.sh`) | audit **FAILS loudly** (live ≠ committed JSON) |

**Honesty note:** rows 1–6, 9, 10 are **mechanical** (a check fires). Row 7 is mechanical *at CI* but bypassable locally by design — CI is the wall, so confirm the required-check config. Row 8 is **procedural** — its guard is a visible diff in the upgrade PR, not a fired finding. Rows 11–15 are **mechanical at the GitHub boundary** (branch protection / required checks / the `ai-review` guard) — a green config readout is *not* proof; a blocked merge is, so run them for real (§4). Row 16 is the **drift-audit on a setting Fux can't seal** — GitHub config watched on a schedule, not sealed by `fux gate`. Disclose all three kinds; don't claim a mechanical guard where there's a procedural or watched-config one.

---

## 3. Independent review (§9 of the build handoff, with evidence)

Fresh eyes, run — don't eyeball — each item:

- **$0 held** — grep the maintenance path (`check`/`gate`/`verify`/`seal`/`constitution`/`critic`/hooks) for any LLM import; confirm default install is model-free.
- **Determinism** — run `fux gate` twice on an unchanged tree; diff the output; must be identical.
- **No new deps** — `dependencies = []`; LLM surface is an extra only.
- **Split honored** — money/PII/audit/numbers never reach the critic's AI pass.
- **Coverage report-first** — adoption doesn't flood; blocking is opt-in by tier.
- **Docs in sync** — plan + implementation + cli + README reflect the shipped surface.
- **File sizes** — ≤100 lines (≤50 utils); list any over and split them.
- **Over-build** — flag and cut anything the phases didn't ask for.

---

## 4. Dogfood the real ritual

Synthetic tests pass; now walk it by hand once, because the *feel* is the product:

- In `fux`: run `/fux debate` on `con-amendment` for real → escalate to you → you ratify. Confirm the `ratification` block, `debate_hash`, `constitution.lock`, and the provenance check all populate.
- In `anton`: same for the money/PII rule.
- Open the `fux constitution` status view (build it if absent, §5): what's constitutional, what each governs, current violations.
- Deliberately break each ratified rule by hand and read the gate output a future you would see. That output *is* the UX — if it's cryptic, fix it now.

---

## 5. Follow-up roadmap (after verification is clean)

In priority order:

1. **Advisory-first critic.** Default the judgment-principle critic to *suggest*, not block; only deterministic hard-invariants block. Earn trust before it interrupts — this is the single biggest "will I keep it on" lever.
2. **`fux constitution` status view.** One command: what's constitutional, what it governs, recent debates, current violations. Collapses the cognitive load of the whole system into one screen.
3. **"Is this constitutional?" heuristic in `con-amendment`.** One line: *constitutional only if a wrong answer costs money/PII/audit/trust **and** the rule never legitimately changes.* Stops over- and under-constitutionalizing.
4. **Runtime critic (deferred §5.3 of the build plan).** Expose the critic as a callable in front of Anton's riskiest live paths (money, PII) — the step that governs already-running behavior, old and new code alike. Start advisory there too.

---

## 6. Exit criteria — when it's "real"

- Every **mechanical** row of §2 is CAUGHT; row 7 confirmed at CI; row 8's procedural guard confirmed visible.
- §3 review comes back clean (or findings remediated).
- §4 dogfood populates the full audit trail and the gate blocks hand-breakage with readable output.

Until then, treat "implemented" as "drafted." After that, it's a constitution.
