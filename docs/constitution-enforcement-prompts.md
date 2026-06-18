# Fux Constitution — Enforcement Hardening Prompts (make the wall real)

Paste in order, **once per repo** (`fux`, then `anton`). Full spec: `docs/constitution-enforcement-handoff.md`.

The gap: `fux gate` runs on PRs but isn't a **required** status check, so a PR can merge while it's red/pending/absent. These prompts make it binding and keep it that way. Branch protection lives in GitHub, outside the repo — Fux can't seal it, so E3 (drift audit) is not optional.

**Prereqs:** admin on the repo + a `gh` token with `repo` scope (`administration` was *not* needed for an owner-managed github.com repo). Any prompt should stop and tell you if it needs perms you haven't granted. Keep changes surgical — only `.github/`, the audit recipe, and git-identity config.

---

## E-ALL — one-shot: implement everything (per repo)

Paste this single prompt to run E1–E5 + the review model in one pass. The granular prompts below remain for re-running a single phase.

```
Implement the FULL constitution enforcement hardening for THIS repo in one pass, following
docs/constitution-enforcement-handoff.md (§2–§5 incl. §2R). Plan briefly first, then execute the phases
in order. Stop ONLY at the one checkpoint marked below. Scope: Claude Code only — do NOT create a new
GitHub account. Surgical: touch only .github/, scripts/, the audit recipe, git-identity config, and the
ritual/CLI plumbing. Update the relevant docs in the same pass.

PHASE 1 — make the checks exist and report
- Ensure a `fux gate` job exists in ci.yml that runs `fux gate` (add it if only pytest/dogfood exist).
- Add an AI-review CI job: a SEPARATE agent reviews the PR diff against the constitution and exits
  non-zero on problems; it MUST refuse if the reviewer identity == the PR author (separation of duties).
- Open a THROWAWAY branch + PR so both checks register; run `gh pr checks <n>` to read the EXACT context
  strings — do NOT guess (a mismatch enforces nothing). The required context is the BARE job name, not
  `workflow / job`. Keep the PR open until Phase 2 has the names, then close it.

PHASE 2 — branch protection  [CHECKPOINT: show me the JSON and STOP for my OK before applying]
- Write .github/branch-protection.json: required_status_checks.strict=true with
  checks=[{context:"<fux gate name>"},{context:"<ai-review name>"}], enforce_admins=true,
  required_pull_request_reviews=null (solo dev — review is via CHECKS not approvals; restore =1 only if a
  2nd human joins), allow_force_pushes=false, allow_deletions=false, restrictions=null.
- If enforce_admins must be false for any reason, STOP and ask me — it weakens the wall.
- On my OK: apply via `gh api -X PUT repos/OWNER/REPO/branches/BRANCH/protection --input`, add
  scripts/apply-branch-protection.sh OWNER REPO BRANCH as the committed wrapper, and confirm via
  `gh api .../protection/required_status_checks` that BOTH exact contexts are present.

PHASE 3 — review routing + forced PR path + agent identity
- Add .github/CODEOWNERS routing /.fux/ and /.fux/constitution.lock to @arpit (human review on
  constitutional paths only).
- Confirm protection makes a PR the ONLY path to the branch (no direct commit by anyone, including me).
- Update `/fux debate` and `fux ratify` to write on a NEW branch and open a PR (git switch -c
  constitution/<id> → gh pr create), never committing to the protected branch. Deterministic git/gh
  only, no model call. Document in cli.md.
- Give Claude Code a distinct git author identity (user.name "Claude (agent)", a dedicated email) + an
  `Agent: claude-code` commit trailer. No GitHub account, no new credential.

PHASE 4 — keep it set (drift audit, NOT optional)
- Add a scheduled GitHub Action (weekly) AND a `just audit-protection` recipe that runs
  `gh api .../protection/required_status_checks`, asserts the expected contexts + enforce_admins=true,
  diffs live protection against the committed branch-protection.json, and FAILS LOUDLY on any difference.
  Treat the committed JSON as source of truth. Note in guardrails docs that branch protection is GitHub
  config audited on a schedule, not sealed by `fux gate`.

PHASE 5 — PROVE the wall (a green readout is not proof — paste BLOCKED/ALLOWED evidence for each)
1. PR that FAILS `fux gate` → merge blocked, names the check.
2. PR with the gate PENDING → cannot merge.
3. Direct commit/push to the protected branch (as me) → rejected.
4. Admin merge past a red check (enforce_admins) → blocked.
5. `fux ratify` → lands on a new branch + PR, not the protected branch.
6. AI-review check runs, blocks a planted violation, and REFUSES when author==reviewer; the PR carries
   the `Agent: claude-code` trailer + distinct author.
7. Drift audit passes; then remove the required check, confirm the audit FAILS, restore it.
Use scratch branches for test PRs and clean them up.

PHASE 6 — standing coverage
- Add red-team rows to docs/constitution-verification-prompts.md (R1) and the §2 matrix in the
  verification handoff: merge while gate red→BLOCKED; direct push→REJECTED; reviewer==author→REFUSED;
  AI-review red→BLOCKED.

FINISH: one-line verdict — is the wall real? List anything you could NOT enforce and why.
```

---

## E1 — Required status check + branch protection (per repo)

```
Make `fux gate` a REQUIRED status check on this repo's protected branch, per
docs/constitution-enforcement-handoff.md §2.
1. Read the EXACT check name from a recent PR: `gh pr checks <pr-number>`. Do NOT guess it — a mismatch
   means the rule enforces nothing. Show me the name you found.
2. Write .github/branch-protection.json: required_status_checks.strict = true with checks=[{context:
   "<exact name>"}], enforce_admins = true, required_pull_request_reviews = null, allow_force_pushes =
   false, allow_deletions = false, restrictions = null. Show me the file before applying.
   (Solo dev: a self-approval is unsatisfiable, so review is NOT an approval count — it's enforced via
   required CHECKS, see E2c. Restore required_pull_request_reviews=1 only if a second human maintainer
   joins.)
3. Apply: `gh api -X PUT repos/OWNER/REPO/branches/BRANCH/protection -H "Accept: application/vnd.github+json"
   --input .github/branch-protection.json`.
4. Add scripts/apply-branch-protection.sh OWNER REPO BRANCH as a reproducible wrapper (committed).
5. Confirm: `gh api repos/OWNER/REPO/branches/BRANCH/protection/required_status_checks` — the exact
   context must be present. Paste the output.
The wall here = required `fux gate` check + enforce_admins + no force-push/deletion. That must still
mean NO direct commits to the protected branch by anyone, including me — every change goes via a new
branch + PR. If enforce_admins must be false for an escape hatch, stop and ask me first — it weakens the wall.
```

---

## E2 — CODEOWNERS on the constitution (per repo)

```
Add .github/CODEOWNERS requiring MY review on the files that ARE the constitution, so a constitutional
change can't be self-merged:
  /.fux/                 @arpit
  /.fux/constitution.lock @arpit
Then set required_pull_request_reviews.require_code_owner_reviews = true in .github/branch-protection.json
and re-apply via scripts/apply-branch-protection.sh. Confirm via the protection API and paste output.
```

---

## E2b — Force branch → PR; make the ritual open it (per repo)

```
Per §2f/§2g of docs/constitution-enforcement-handoff.md, make a PR the ONLY path to the protected branch
and make the amendment ritual use it automatically:
1. Confirm the protection from E1/E2 blocks direct commits to the protected branch for everyone (PR
   required + enforce_admins). If not, fix the JSON and re-apply.
2. Update `/fux debate` and `fux ratify` so their write lands on a NEW branch and opens a PR — e.g.
   `git switch -c constitution/<id>` then `gh pr create` — never committing to the protected branch.
   Deterministic git/gh plumbing only, no model call. Document in cli.md.
3. Test: run `fux ratify <id>` and confirm it created a new branch + PR (not a commit on the protected
   branch); the PR shows `fux gate` as a required check. Paste the branch name + PR URL.
Enforced loop must be: git switch -c <branch> → push → PR → fux gate (required) → review → merge. No
other path exists.
```

---

## E2c — PR review enforcement: Claude Code only, no new account (per repo)

```
Set up PR review enforcement per §2R of docs/constitution-enforcement-handoff.md.
Scope: Claude Code ONLY — do NOT create a new GitHub account.
1. Add an AI-review REQUIRED check: a CI job where a SEPARATE agent reviews the PR diff against the
   constitution and exits non-zero on problems. It MUST refuse if the reviewer identity == the PR author
   (separation of duties). Add its exact context to .github/branch-protection.json checks[] alongside
   `fux gate`, and re-apply via scripts/apply-branch-protection.sh.
2. Give Claude Code a distinct git author identity (user.name "Claude (agent)", a dedicated email) and an
   `Agent: claude-code` commit trailer on its commits. No GitHub account, no new credential.
3. Confirm .github/CODEOWNERS routes /.fux/ and constitution.lock to me (human review on constitutional
   paths only — E2).
4. PROVE it: open a PR; confirm the AI-review check runs, blocks a planted violation, refuses when
   author==reviewer, and the PR carries the Agent trailer + distinct author. Paste evidence.
Leave the bot-identity / GitHub-App path for LATER (§2R.4) — do not build it now. Surgical: only the CI
workflow, branch-protection.json, CODEOWNERS, and git-identity config.
```

---

## E3 — Drift audit: keep it set (per repo, NOT optional)

```
Branch protection isn't sealed by Fux, so a one-time setting can silently revert. Add a drift audit per
§3:
- A scheduled GitHub Action (weekly) OR a `just audit-protection` recipe that runs
  `gh api .../protection/required_status_checks`, asserts the expected context is present and
  enforce_admins is true, and FAILS LOUDLY otherwise.
- It diffs live protection against the committed .github/branch-protection.json; any difference = drift =
  fail/alert. Treat the committed JSON as source of truth.
- Note in guardrails docs (anton/docs/guardrails.md; fux docs) that branch protection is enforced by
  GitHub config audited on a schedule, not by `fux gate` itself.
Test it: run the audit (should pass), manually remove the required check, run again (must FAIL), restore.
```

---

## E4 — Prove the wall (per repo — the decisive step)

```
Prove enforcement for real per §4 — a green config readout is not proof, a blocked merge is. Do each and
paste evidence:
1. Open a PR that FAILS `fux gate` (stage a constitutional violation). Confirm the merge button is BLOCKED
   and names the required check as the blocker.
2. Confirm a PR with the gate PENDING cannot merge.
3. Attempt a direct commit/push to the protected branch (as yourself) → must be rejected; only a new
   branch + PR is accepted.
4. If enforce_admins=true, attempt an admin merge past the red check → must be blocked.
5. Run `fux ratify` and confirm it lands on a new branch + opens a PR, not on the protected branch (E2b).
6. Confirm the AI-review check (E2c) runs on a PR, blocks a planted violation, and refuses when
   author==reviewer; confirm Claude Code's PR carries the distinct author identity + `Agent:` trailer.
7. Run the E3 drift audit and confirm it passes.
Report each as BLOCKED/ALLOWED with evidence. End with a one-line verdict: is the wall real?
```

---

## E5 — Fold into standing verification (fux repo, optional)

```
Add these rows to the red-team in docs/constitution-verification-prompts.md (R1) so the gap stays covered
in standing verification, not just this one-off:
  - "merge a PR while `fux gate` is red/pending" → expected: BLOCKED by required check
  - "push directly to the protected branch" → expected: REJECTED
  - "open a PR where the AI-reviewer is the same identity as the author" → expected: REFUSED (sep. of duties)
  - "merge a PR with the AI-review check red" → expected: BLOCKED
Update the §2 verification matrix in the verification handoff to match.
```
