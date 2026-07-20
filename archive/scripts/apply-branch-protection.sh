#!/usr/bin/env bash
# Apply the checked-in branch-protection config to a repo branch.
#
#   scripts/apply-branch-protection.sh OWNER REPO BRANCH
#   scripts/apply-branch-protection.sh arpitarya fux main
#
# The intended protection lives in .github/branch-protection.json (the source of
# truth). This wrapper makes re-applying it one command, not a memory of clicks.
# Requires: gh authenticated with a token that has admin on the repo.
set -euo pipefail

OWNER="${1:?usage: apply-branch-protection.sh OWNER REPO BRANCH}"
REPO="${2:?usage: apply-branch-protection.sh OWNER REPO BRANCH}"
BRANCH="${3:?usage: apply-branch-protection.sh OWNER REPO BRANCH}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$REPO_ROOT/.github/branch-protection.json"

[ -f "$CONFIG" ] || { echo "missing $CONFIG" >&2; exit 1; }

# Strip the human-readable "_note" key the API does not accept.
PAYLOAD="$(jq 'del(._note)' "$CONFIG")"

echo "Applying $CONFIG to $OWNER/$REPO@$BRANCH ..."
echo "$PAYLOAD" | gh api -X PUT "repos/$OWNER/$REPO/branches/$BRANCH/protection" \
  -H "Accept: application/vnd.github+json" \
  --input -

echo
echo "Required status checks now on $OWNER/$REPO@$BRANCH:"
gh api "repos/$OWNER/$REPO/branches/$BRANCH/protection/required_status_checks"
