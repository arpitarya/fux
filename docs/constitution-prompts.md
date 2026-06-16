# Fux Constitutional-App Engine — Claude Code Execution Prompts

Paste one at a time, in order, in the indicated repo. Each is self-contained for a cold session. Do not start a prompt until the previous acceptance test is green. Full spec: `docs/constitution-handoff.md` (this file tracks its phases 0–8).

The through-line on every prompt: **Fux never makes an API call — the host agent does the thinking; Fux is the deterministic harness.** If a prompt seems to require Fux to call a model, you've misread it — stop.

Workflow each prompt enforces: **plan → approve → implement with tests → self-verify.** When a session drifts, stop and re-paste fresh — don't prompt deeper.

---

## Prompt 0 — Prime the session (run once per fresh session, fux repo)

```
Read docs/constitution-handoff.md fully, plus fux/CLAUDE.md, fux/findings.py, fux/gate.py,
fux/check.py, fux/seal.py, fux/coverage.py, and fux/data/schema.json. We are building the
constitutional-app engine described in the handoff. Hard constraints on every change:
- $0, stdlib only on the maintenance/enforcement path. LLM use happens ONLY inside agent-driven
  skills (/fux debate, /fux propose) that ride this session — never in check/gate/verify/seal/
  constitution/critic or any hook. The LLM surface ships as an opt-in extra like [embeddings].
- Deterministic: same rules + code ⇒ same findings/verdicts. No clocks/random in output.
- Files ≤100 lines (≤50 for *_utils). Python ≥3.11. No new runtime deps.
- Adopting the new version must be a no-op until I opt in (§5b migration rules).
- Docs in sync IN THE SAME CHANGE: fux-plan.md, fux-implementation.md, README.md (if surface
  changes), cli.md (commands), and a test in tests/.
Do not write code yet. Reply with (a) a one-paragraph confirmation of the end state, and (b) the
exact files you expect to touch for each of Phases 0–8. Wait for my go.
```

---

## Prompt 1 — Phase 0: amendment article (fux repo)

```
Phase 0. Author ONE constitutional rule, id `con-amendment`, in .fux/rules/. Body: a constitutional
rule is created or changed only via propose → debate → ratify; it changes only by supersession,
never in-place edit; ratification requires a named human ratifier and a recorded debate. Frontmatter:
tier: constitutional, type: rule, status: active. Leave the ratification: block as a TODO (I run
`fux ratify` after Phase 2). Add a "Constitution layer" section to docs/fux-plan.md linking
con-amendment as the meta-rule. NO enforcement code yet. Show me the rule file and the plan-doc
diff for approval before writing.
```
Acceptance: rule parses under `fux check`; plan updated.

---

## Prompt 2 — Phase 1: tier + unconditional block + backward-compat (fux repo)

```
Phase 1. Plan first, then wait for approval.
1. Add `tier` (enum constitutional|standard|advisory, default standard) to fux/data/schema.json,
   additive and optional.
2. In fux/findings.py make blocking tier-aware: ANY finding against a tier:constitutional rule blocks
   unconditionally regardless of mode; standard keeps today's kind-based blocking under strict;
   advisory only warns. Carry tier on the Finding deterministically.
3. Make `unsealed` blocking for constitutional rules only.
4. Build the §5b migration helper: `fux check --baseline-write <file>` snapshots findings (canonical
   order: kind, rule_id, message) and `fux gate --baseline <file>` diffs + exits 2 on any new
   BLOCKING finding (new advisories ignored). Add a baseline.py helper (≤50 lines) reusing Finding
   serialization; make check's finding order canonical. No new deps. Scope: transient migration guard,
   not a regression subsystem.
5. Tests: (a) a broken ref on a constitutional rule fails `fux gate` exit 2 with mode = "fix";
   (b) the same break on a standard rule does NOT block outside strict; (c) BACKWARD-COMPAT —
   every existing rule in fux's .fux/ still parses and produces no new blocking finding under the
   default tier; (d) the helper — baseline-write then gate --baseline on an unchanged tree → exit 0;
   inject a blocker → exit 2.
6. Update fux-plan.md, fux-implementation.md, cli.md.
Stdlib only, ≤100-line files, deterministic, $0. After coding, run `python -m pytest -q` and
`fux build && fux check` and paste output.
```
Acceptance: all three tests green; breaking `con-amendment`'s ref → `fux gate` exit 2 at mode=fix.

---

## Prompt 3 — Phase 2: self-seal + tamper + lock + ratify (fux repo)

```
Phase 2 — the integrity keystone. Plan first; show me the constitution.py interface (signatures +
one-line docstrings) for review BEFORE implementing.
1. fux/constitution.py (≤100 lines): content_seal(rule), check_tamper(rules), lock_manifest(rules),
   check_lock(root, rules). Reuse seal.py normalization; no new deps.
2. Add `tampered` to findings.KINDS, always-blocking for constitutional rules.
3. `fux ratify <id>` (deterministic, NO LLM): stamp ratification.by/date/content_seal, freeze the
   code seal, write/update .fux/constitution.lock. Only path into the constitutional tier.
4. Wire check_tamper + check_lock into check.py::run. Tamper/seal/lock apply to constitutional rules
   only — existing unsealed rules must stay untouched.
5. Tests: hand-edit a ratified constitutional rule body → tampered blocks gate; delete one → lock
   mismatch blocks; only `fux ratify` mutates the lock; existing non-constitutional rules unaffected.
6. Update fux-plan.md, fux-implementation.md, cli.md, README.md (new command).
Run pytest + `fux build && fux check`; paste output.
```
Acceptance: `fux ratify con-amendment`; edit its body → `fux gate` fails `tampered`; restore + re-ratify → green.

---

## Prompt 4 — Phase 3: two-agent debate engine (fux repo)

```
Phase 3. Add a `/fux debate "<proposed rule>"` SKILL — Fux spends nothing; it drives THIS host agent.
The skill must:
- Spawn TWO sub-agents (Task/Agent tool), both fluent in building AND selling, NO assigned sides
  (free debate). Each forms its position BLIND (without seeing the other's) first, then they reveal
  and debate.
- Enforce anti-sycophancy: each must surface ≥1 concrete objection; convergence counts only after
  both tried to break the rule; instant agreement on a constitutional rule forces one extra
  adversarial round.
- On non-convergence, ESCALATE to me with both arguments — I am the tie-breaker and ratifier.
- Hash the transcript into debate_hash; `fux ratify` consumes it.
Fux's code role is only the deterministic harness: capture transcript → hash → hand to ratify.
Wire the skill into install.sh and fux/data/skills/fux/SKILL.md alongside plan/adr/propose. Add a
GUARD TEST asserting no maintenance-path module (check/gate/verify/seal/constitution/critic/hooks)
imports an LLM client, and that `pip install fux-engine` with no extras imports model-free.
Update all four docs. Plan before coding.
```
Acceptance: a debate yields a transcript + hash; `fux ratify` records `debate_hash`; guard test passes; default install is model-free.

---

## Prompt 5 — Phase 4: principle tagging + deterministic/judgment split (fux repo)

```
Phase 4. Add optional schema fields `principle` (string) and `enforcement` (enum
deterministic|judgment) per the handoff. Enforce the split in code: a `deterministic` principle may
NEVER be routed to the AI critic path; a `judgment` principle may never be faked as deterministic.
Add an ADVISORY `untagged-candidate` finding in `fux check` listing rules that look like they should
carry a principle (so backfill is guided, never auto-guessed). Both fields optional → existing rules
stay valid and untagged. Test: a deterministic principle cannot reach the critic's AI pass; existing
untagged rules produce no blocking finding. Update all four docs. Plan first.
```
Acceptance: split test green; untagged-candidate is advisory only; no existing rule newly blocks.

---

## Prompt 6 — Phase 5: critic loop (build-agent surface) + coverage gate (fux repo)

```
Phase 5. Behind a new opt-in `[critic]` extra (mirroring [embeddings]; default install stays
model-free), implement the critique→revise→act loop at the PreToolUse/pre-commit boundary for build
agents:
1. Gather relevant principles via recall. 2. DETERMINISTIC pass first — run check:/seals/matchers
for `deterministic` principles; hard invariant fails → block, NO LLM. 3. For `judgment` principles,
the agent self-critiques its own proposal → verdict + rationale. 4. Revise + re-run, bounded, then
escalate to a human. 5. Two-agent debate fires ONLY on borderline/escalated judgment cases.
6. Record verdict + applied principles to the audit trail; Cage meters the agent tokens.
Also implement the COVERAGE gate using coverage.py/mine.py/impact.py: `fux gate` REPORTS (report-
first, not blocking on adoption) any important_globs path governed by zero rules. Tests: a build-agent
change violating a judgment principle is critiqued and revised pre-commit; an ungoverned glob path is
reported, not blocked. Update all four docs. Plan first; show the critic seam interface for review.
```
Acceptance: judgment violation is caught + revised before commit; coverage reports ungoverned paths without blocking.

---

## Prompt 7 — Phase 6: cut the new fux-engine version (fux repo)

```
Phase 6. Confirm `python -m pytest -q`, `fux build && fux check`, and `fux gate` are clean on a clean
tree (paste output). This is a feature release — the constitutional-app engine. Bump fux.__version__
to the next minor. Update README.md and fux-implementation.md (flip constitution/debate/critic items
to ✅, summarize the new surface: tier, fux ratify, /fux debate, [critic] extra, coverage report,
.fux/constitution.lock). Add a CHANGELOG entry. Build the package; confirm `fux --version`. Do NOT
publish — produce the bump and a clean build.
```
Acceptance: `fux --version` shows the bump; docs ✅; package builds.

---

## Prompt 8 — Phase 7: integrate into Anton (anton repo)

```
Integrate the new fux-engine into this repo. Plan first; show me the chosen first rule before
ratifying anything.
1. MIGRATION GATE FIRST (via the helper from Phase 1): run `fux check --baseline-write
   .fux/upgrade-baseline.json` on the pre-upgrade tree and commit it; bump the fux-engine pin in
   pyproject.toml; then run `fux gate --baseline .fux/upgrade-baseline.json` as a CI step — it must
   exit 0. If it exits 2 (a new blocking finding), STOP — the engine is not backward-compatible; do
   not edit anton's rules. Retire the baseline file once the upgrade lands clean.
2. Make anton's "never commit money docs / PII; plans live in elgar" rule the FIRST constitutional
   rule: run /fux debate to debate it, then `fux ratify` it (tier: constitutional + self-seal);
   create anton/.fux/constitution.lock.
3. Add a `just constitution` recipe running `fux gate`; make it a REQUIRED CI check (CI is the wall —
   local pre-commit is bypassable via --no-verify).
4. Update anton/CLAUDE.md Must-Know Rules (money-docs rule now constitutional + gate-enforced) and
   anton/docs/guardrails.md.
5. Verify: stage a test change adding a personal money figure → `fux gate` blocks it; paste output.
Keep it surgical — do not widen important_globs or touch unrelated rules.
```
Acceptance: migration gate clean; `just constitution` green on clean tree; staged money/PII violation fails it; lock exists; docs updated.

---

## Prompt 9 — Phase 8: audit sweep over existing Anton (anton repo)

```
Phase 8. Run the critic across EXISTING anton once (read-only audit, no auto-edits) over the
constitutional paths — financial decisions, numbers, recommendations, PII, audit. Produce a report
listing where current behavior already violates the ratified principle(s): file, the action, which
principle, and severity. Do NOT change code yet — give me the report; I'll decide what to fix. Then,
on my go, fix only the real violations, surgically. This is how already-built anton comes under the
constitution — by audit, not by re-running build agents over old code.
```
Acceptance: report produced; after fixes, no unresolved constitutional violations on the covered paths.

---

## Review gate (paste before merging each phase)

```
Before I merge, review your own change at a principal bar against docs/constitution-handoff.md §9.
Confirm explicitly: (1) no LLM import reachable from check/gate/verify/seal/constitution/critic/hooks,
and default `pip install fux-engine` is model-free; (2) re-running `fux gate` on an unchanged tree
gives identical output; (3) dependencies = [] unchanged (LLM is an extra only); (4) a constitutional
rule's meaning can't change without tampered/unsealed firing — show me you tried; (5) money/PII/audit/
numbers run deterministically, never through the critic's AI pass; (6) adopting this change is a no-op
on existing repos until opt-in (§5b); (7) docs updated in this same change; (8) files ≤100 lines.
List anything you over-built and cut it.
```
