# Fux Constitution — Enforcement Hardening Handoff (make the wall real)

**Owner:** Arpit · **Repos:** `fux`, `anton` · **Driving model:** Claude Code / Cowork.
**Status:** the constitution and its `fux gate` CI workflow are implemented. **One gap remains, and it is the load-bearing one:** the gate workflow runs on PRs but is **not a required status check**. This handoff makes it binding.

---

## 0. The gap, precisely

Throughout the build we relied on one promise: *local pre-commit is convenience; **CI is the wall** (`--no-verify` bypasses local hooks).* That promise is currently false. The workflow executing on a PR ≠ a merge-blocking gate. Right now a PR can be merged while `fux gate` is **red, pending, or absent**, and (if the branch isn't protected) someone can push straight to `main`. The constitution is fully enforced *in code* and *not enforced at the boundary that matters.*

"Required" is a **branch-protection** setting, configured via the GitHub API / repo settings — it is not something the workflow can grant itself.

---

## 1. The honest trust boundary (read this first)

Branch protection lives in **GitHub, outside the repo**. Fux cannot `seal` it, `fux check` cannot verify it, and `constitution.lock` cannot cover it. This is the one part of the system the constitution cannot make self-enforcing. So the fix has **two halves**, and skipping the second recreates the gap silently:

1. **Set it** — make the gate a required check + protect the branch.
2. **Keep it set** — capture the intended config as code and add a drift audit, because a setting nobody can diff is a setting that quietly reverts.

---

## 2. Set it — required check + branch protection (both repos)

> **Status (`fux` repo, 2026-06-18): §2a–2d DONE.** The required check context is
> **`fux gate`** — the *bare job name*, not `CI / fux gate`. The check-runs API
> (`repos/OWNER/REPO/commits/<sha>/check-runs`) reports the job name alone, and
> the modern `required_status_checks.checks[].context` must match *that*, not the
> `workflow / job` form shown in the PR UI. A new `gate` job was added to
> `ci.yml` (no `fux gate` workflow existed before). Protection applied with
> `repo` scope alone — `administration` scope was *not* needed for an
> owner-managed github.com repo. `scripts/apply-branch-protection.sh` is the
> committed wrapper. `restrictions` is `null`. **Solo-repo decision:**
> `required_pull_request_reviews` is `null` — a sole developer cannot approve
> their own PR, so a review requirement is unsatisfiable friction, not a control.
> The wall is therefore the required `fux gate` check + `enforce_admins: true` +
> no force-push/deletion, confirmed via `…/branches/main` (`protected: true`).
> That still routes every change through a green-gate PR (no direct commit to
> `main` by anyone). Restore the 1-review requirement if a second maintainer
> joins. §2e (CODEOWNERS), §2f live-push test, §2g (ratify-opens-PR),
> §3 (drift audit), §4 (full proof) still open.

Prerequisites: admin on the repo; a `gh` token with `repo` scope (the
`administration` scope is *not* required for branch protection on an
owner-managed github.com repo — `repo` alone sufficed here).

### 2a. Get the exact check name (the #1 footgun)
The required `context` string must match **exactly** what appears in the PR's checks — for a GitHub Actions job that's the **job name** (often shown as `workflow / job`). A typo here means the rule is configured but silently enforces nothing. Read the real name from a recent run, do not guess:

```
gh pr checks <pr-number> --repo OWNER/REPO        # lists the exact check names
# or inspect the latest Actions run for the constitution workflow
```

### 2b. Capture the intended protection as code
Check in `.github/branch-protection.json` per repo so the config is diffable and reproducible:

```json
{
  "required_status_checks": {
    "strict": true,
    "checks": [{ "context": "<EXACT-CHECK-NAME-FROM-2a>" }]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": { "required_approving_review_count": 1 },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
```

Notes: `strict: true` requires the branch be up to date, so the gate ran against the actual merge result. `enforce_admins: true` closes the "admin merges past it" hole — decide consciously; if you need an admin escape hatch, set `false` and document *why* (it is a real weakening of the wall).

### 2c. Apply it
```
gh api -X PUT repos/OWNER/REPO/branches/BRANCH/protection \
  -H "Accept: application/vnd.github+json" \
  --input .github/branch-protection.json
```
Add a reproducible `scripts/apply-branch-protection.sh OWNER REPO BRANCH` wrapper so re-applying is one command, not a memory of clicks.

### 2d. Confirm it took
```
gh api repos/OWNER/REPO/branches/BRANCH/protection/required_status_checks
```
The `contexts`/`checks` array must contain the exact name from 2a.

### 2e. (Recommended) CODEOWNERS on the constitution
Add `.github/CODEOWNERS` requiring your review on the files that *are* the constitution, so a constitutional change can't be self-merged even by a collaborator:
```
/.fux/                @arpit
/.fux/constitution.lock @arpit
```
Pair with `required_pull_request_reviews.require_code_owner_reviews: true`.

### 2f. Force the branch → PR workflow (no direct commits)
A required check gates **PRs only** — if anyone can push to the protected branch, the gate is bypassed entirely. So the branch must be configured to make a PR the *only* way in:

- `required_pull_request_reviews` present + `enforce_admins: true` ⇒ **no one, including you, commits directly to the protected branch.** Every change goes through a new branch → PR → required `fux gate` → review → merge.
- Confirm by the verification in §4.3 (a direct commit/push to the protected branch is rejected). Add this to `.github/branch-protection.json` review note so the intent is explicit, not incidental.

The enforced loop is therefore: **`git switch -c <branch>` → push → PR → `fux gate` (required) → code-owner review → merge.** There is no other path.

### 2g. Make the amendment ritual open the branch + PR itself
So the loop above is the path of least resistance, not friction: `/fux debate` / `fux ratify` should perform their write on a **new branch** and **open a PR** automatically (e.g. `git switch -c constitution/<id>` then `gh pr create`), never committing to the protected branch. This keeps every constitutional change routed through the gate by construction — the agent and the human both physically *cannot* land a ratification except via PR. Deterministic git/gh plumbing only; no model call. Document the new behavior in `cli.md`.

---

## 2R. PR review enforcement — who reviews when agents author (Claude Code scope)

Context: §2 set `required_pull_request_reviews: null` because a solo human can't approve his own PR — an approval *count* is unsatisfiable friction. That decision stands. But "no approval requirement" must not become "no review." With Claude Code as a PR author (and Codex/Copilot later), the reviewer role is **split**, and review is enforced as *checks*, not an approval click.

### 2R.1 Mechanical reviewers — required checks, always
- `fux gate` (constitution integrity) **plus** a new **AI-review check**: a CI job where a *different* agent reviews the PR diff against the constitution and exits non-zero on problems. Because it's a *check*, not a GitHub approval, it works for a solo author — it is the second set of eyes the missing human approval would otherwise provide.
- **Separation of duties:** the reviewing identity must differ from the PR author; the job refuses if `author == reviewer`. This mirrors the two-signature correction lane — the reviewer is never the author.

### 2R.2 Human reviewer — you, reserved for the constitution
You read and merge. CODEOWNERS (§2e) routes `.fux/**` + `constitution.lock` to you specifically, so constitutional changes always get human judgment. Ordinary code PRs merge on the mechanical reviewers + your merge.

### 2R.3 Agent identity — NOW, Claude Code only (no new GitHub account)
**Do not create a new GitHub username/password account yet.** A separate account buys exactly one thing — making the agent the GitHub-level PR *author* so GitHub can force your approval click — and a solo dev merging his own reviewed PRs doesn't need it. Instead:

- Give Claude Code a distinct **git author identity** — `git config user.name "Claude (agent)"`, a dedicated email — plus an `Agent: claude-code` commit trailer, so authorship is auditable in history. No account, no credential to manage.
- Claude Code opens PRs via the forced branch → PR flow (§2f/§2g); merge is gated by the required checks; you review the diff and merge.

This fully covers Claude-Code-only review for a solo maintainer: **the wall is `fux gate` + AI-review check + your merge.**

### 2R.4 Bot identity — DEFERRED (later, and how)
Create a dedicated agent identity only when **(a)** you want GitHub to force an explicit approval *click* (true "agent authors → human approves"), or **(b)** you add Codex/Copilot and must tell agents apart at the GitHub level. When that day comes:

- Prefer a **GitHub App** over a username/password account — no password to leak, scoped, revocable, proper bot attribution.
- **Least privilege, never admin:** the agent identity gets only `contents` + `pull requests` on these repos; it must not be a repo admin and must not hold branch-protection rights — *the author cannot be allowed to move the wall* (same separation-of-duties as the constitution).
- Re-enable `required_pull_request_reviews` (count 1, `require_code_owner_reviews: true`), `dismiss_stale_reviews: true`, and **"require review from someone other than the most recent pusher"** at that point.

---

## 3. Keep it set — drift audit (the second half)

Because §1: a one-time setting is not a guarantee. Add a **scheduled drift audit** that fails/alerts if the required check is ever removed or renamed:

- A small scheduled GitHub Action (e.g. weekly) — or a `just audit-protection` recipe — that runs `gh api .../protection/required_status_checks`, asserts the expected context is present and `enforce_admins` is true, and **fails loudly** otherwise.
- It compares live protection against the checked-in `.github/branch-protection.json`; a diff = drift = alert. This is the only mechanical guard available for a setting Fux can't seal — treat the checked-in JSON as the source of truth and the audit as its enforcement.

Disclose in `anton/docs/guardrails.md` and `fux` docs: branch protection is enforced by GitHub config audited on a schedule, **not** by `fux gate` itself — so the one link in the chain Fux cannot seal is at least watched.

---

## 4. Verify — prove the wall (don't assume)

Run these for real in each repo; a green config readout is not proof, a blocked merge is:

1. Open a PR that **fails** `fux gate` (e.g. a staged constitutional violation). Confirm the **Merge button is blocked** and the required check is named as the blocker.
2. Confirm a PR with the gate **pending** cannot be merged (pending ≠ pass).
3. Attempt a **direct commit/push** to the protected branch (as yourself) → rejected; the only way in is a new branch + PR.
4. (If `enforce_admins: true`) attempt an **admin merge** past the red check → blocked.
5. Run `/fux ratify` (or `/fux debate` → ratify) and confirm it lands on a **new branch and opens a PR**, not on the protected branch (§2g).
6. Open a PR and confirm the **AI-review check** runs, blocks on a planted violation, and **refuses when author == reviewer** (separation of duties, §2R.1).
7. Confirm Claude Code's PRs carry the distinct author identity + `Agent: claude-code` trailer (§2R.3).
8. Run the §3 drift audit; then manually remove the required check and confirm the audit **fails**; restore it.

---

## 5. Acceptance criteria

- `fux gate` (by its exact check name) is a **required** status check on the protected branch of **both** `fux` and `anton`.
- Direct pushes and force-pushes to the protected branch are blocked for **everyone** (incl. you, via `enforce_admins`); deletions disabled. The only path to the branch is a new branch + PR.
- `/fux debate` / `fux ratify` write to a new branch and open a PR automatically — a ratification can never land except through the gated PR (§2g).
- Admin-enforcement decision made explicitly (enforced, or documented exception).
- Intended protection captured in `.github/branch-protection.json` + an apply script, both committed.
- A scheduled drift audit exists and demonstrably fails when the required check is removed.
- An **AI-review check** is required and enforces reviewer ≠ author (§2R.1); the human is the required reviewer on constitutional paths via CODEOWNERS (§2R.2).
- Claude Code authors under a distinct git identity + `Agent:` trailer; **no new GitHub account created** (§2R.3). Bot-identity path documented as deferred (§2R.4).
- §4 verification all pass — a failing PR genuinely cannot merge.

---

## 6. Execution prompt (paste into Claude Code, per repo)

```
The constitution's `fux gate` workflow runs on PRs but is NOT a required status check — the wall isn't
real yet. Close it for THIS repo, following docs/constitution-enforcement-handoff.md:
1. Read the EXACT check name from a recent PR (`gh pr checks`); do not guess it.
2. Write .github/branch-protection.json (required_status_checks.strict=true with that exact context,
   enforce_admins=true, block force-push/deletion, require 1 review). Show me the file first.
3. Apply via `gh api -X PUT .../branches/<branch>/protection --input`, and add
   scripts/apply-branch-protection.sh as a reproducible wrapper.
4. Confirm with `gh api .../protection/required_status_checks` (the exact context must be present).
5. Add .github/CODEOWNERS requiring my review on /.fux/ and constitution.lock; enable
   require_code_owner_reviews.
6. Add a scheduled drift-audit (weekly Action or `just audit-protection`) that fails if the required
   check is removed/renamed or differs from the committed JSON.
7. PROVE it: open a PR that fails the gate and confirm merge is blocked; try a direct push and confirm
   it's rejected. Paste the blocked-merge evidence.
Prereqs: I have admin + a token with repo+administration scope. Stop and tell me if a step needs perms
I haven't granted. Surgical — touch only .github/ and the audit recipe.
```

### 6b. PR review model — Claude Code only (paste into Claude Code)

```
Set up PR review enforcement for THIS repo per §2R of docs/constitution-enforcement-handoff.md.
Scope: Claude Code only — do NOT create a new GitHub account.
1. Add an AI-review required CI check: a job where a SEPARATE agent reviews the PR diff against the
   constitution and exits non-zero on problems. It must refuse if the reviewer identity == the PR
   author (separation of duties). Make it a required status check alongside `fux gate`.
2. Give Claude Code a distinct git author identity (user.name "Claude (agent)", a dedicated email) and
   add an `Agent: claude-code` commit trailer to its commits. No GitHub account, no new credential.
3. Confirm .github/CODEOWNERS routes /.fux/ and constitution.lock to me (human review on constitutional
   paths only).
4. PROVE it: open a PR, confirm the AI-review check runs and blocks a planted violation, refuses when
   author==reviewer, and that the PR carries the Agent trailer + distinct author. Paste evidence.
Leave the bot-identity / GitHub-App path for later (§2R.4) — do not build it now. Surgical: only the
CI workflow, CODEOWNERS, and git-identity config.
```
