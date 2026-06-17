# Fux Constitution — Enforcement Hardening Prompts (make the wall real)

Paste in order, **once per repo** (`fux`, then `anton`). Full spec: `docs/constitution-enforcement-handoff.md`.

The gap: `fux gate` runs on PRs but isn't a **required** status check, so a PR can merge while it's red/pending/absent. These prompts make it binding and keep it that way. Branch protection lives in GitHub, outside the repo — Fux can't seal it, so E3 (drift audit) is not optional.

**Prereqs:** admin on the repo + a `gh` token with `repo` and `administration` scope. Any prompt should stop and tell you if it needs perms you haven't granted. Keep changes surgical — only `.github/` and the audit recipe.

---

## E1 — Required status check + branch protection (per repo)

```
Make `fux gate` a REQUIRED status check on this repo's protected branch, per
docs/constitution-enforcement-handoff.md §2.
1. Read the EXACT check name from a recent PR: `gh pr checks <pr-number>`. Do NOT guess it — a mismatch
   means the rule enforces nothing. Show me the name you found.
2. Write .github/branch-protection.json: required_status_checks.strict = true with checks=[{context:
   "<exact name>"}], enforce_admins = true, required_pull_request_reviews.required_approving_review_count
   = 1, allow_force_pushes = false, allow_deletions = false, restrictions = null. Show me the file before
   applying.
3. Apply: `gh api -X PUT repos/OWNER/REPO/branches/BRANCH/protection -H "Accept: application/vnd.github+json"
   --input .github/branch-protection.json`.
4. Add scripts/apply-branch-protection.sh OWNER REPO BRANCH as a reproducible wrapper (committed).
5. Confirm: `gh api repos/OWNER/REPO/branches/BRANCH/protection/required_status_checks` — the exact
   context must be present. Paste the output.
This combination (required_pull_request_reviews present + enforce_admins true) must mean NO direct
commits to the protected branch by anyone, including me — every change goes via a new branch + PR.
If enforce_admins must be false for an escape hatch, stop and ask me first — it weakens the wall.
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
6. Run the E3 drift audit and confirm it passes.
Report each as BLOCKED/ALLOWED with evidence. End with a one-line verdict: is the wall real?
```

---

## E5 — Fold into standing verification (fux repo, optional)

```
Add two rows to the red-team in docs/constitution-verification-prompts.md (R1) so this gap stays covered
in standing verification, not just this one-off:
  - "merge a PR while `fux gate` is red/pending" → expected: BLOCKED by required check
  - "push directly to the protected branch" → expected: REJECTED
Update the §2 verification matrix in the verification handoff to match.
```
