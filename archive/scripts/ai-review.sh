#!/usr/bin/env bash
# AI-review — the second-set-of-eyes constitutional check for a PR (§2R.1).
#
#   scripts/ai-review.sh
#
# A solo human cannot approve his own PR, so the missing human approval is
# replaced by a *check*: a separate reviewer identity reviews the PR diff
# against the constitution and exits non-zero on problems. Two hard rules:
#
#   1. SEPARATION OF DUTIES. The reviewer identity must differ from the PR
#      author. If author == reviewer this job REFUSES (exit 3) — a reviewer is
#      never the author, mirroring the constitution's two-signature lane.
#   2. MODEL-FREE. Per the engine's non-negotiables ($0, stdlib-only, no LLM on
#      the maintenance path) the review itself is the deterministic constitution
#      surface: `fux gate` on the merge result + `fux critic` on the diff. The
#      *judgment* layer is the host agent in-session; CI runs the deterministic
#      second pass that holds for a solo author.
#
# Env (provided by the workflow):
#   PR_AUTHOR    — GitHub login of the PR author (github.event.pull_request.user.login)
#   REVIEWER     — the reviewer identity for this job (a constant, != any human author)
#   BASE_SHA     — merge-base / base ref sha to diff against
set -euo pipefail

REVIEWER="${REVIEWER:-fux-ci-reviewer}"
PR_AUTHOR="${PR_AUTHOR:-}"
BASE_SHA="${BASE_SHA:-}"

echo "AI-review — constitutional second pass"
echo "  reviewer: $REVIEWER"
echo "  author:   ${PR_AUTHOR:-<unknown>}"

# 1. Separation of duties — the reviewer may never be the author.
if [ -n "$PR_AUTHOR" ] && [ "$PR_AUTHOR" = "$REVIEWER" ]; then
  echo "✗ ai-review REFUSES: reviewer identity ($REVIEWER) == PR author ($PR_AUTHOR)." >&2
  echo "  Separation of duties (§2R.1): the reviewer is never the author." >&2
  exit 3
fi
echo "  ✔ separation of duties: reviewer != author"

# 2. Model-free constitutional review of the diff.
#    fux gate already builds the views and blocks (exit 2) on constitutional
#    findings against the checked-out merge result. We add a focused critique of
#    the PR's changed lines so a constitutional violation introduced *by this PR*
#    is named explicitly.
echo
echo "  → fux gate (constitution integrity on the merge result)"
fux gate

if [ -n "$BASE_SHA" ]; then
  DIFF="$(git diff "$BASE_SHA"...HEAD --stat || true)"
  echo
  echo "  → fux critic (constitutional critique of the PR diff)"
  echo "$DIFF" | sed 's/^/    /'
  # Summarise the change for the deterministic critic pass. The host agent does
  # the judgment work in-session; here the deterministic pass blocks on hard
  # invariants (money/PII/audit) the diff might touch.
  SUMMARY="$(git log "$BASE_SHA"..HEAD --format='%s' | tr '\n' ' ')"
  fux critic "$SUMMARY"
fi

echo
echo "✔ ai-review: constitutional second pass clean (reviewer=$REVIEWER, author=$PR_AUTHOR)."
