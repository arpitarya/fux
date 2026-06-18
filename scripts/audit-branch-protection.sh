#!/usr/bin/env bash
# Drift audit — branch protection is GitHub config Fux cannot seal, so it is
# WATCHED on a schedule (§1, §3). Fails LOUDLY if live protection ever drifts
# from the committed source of truth (.github/branch-protection.json).
#
#   scripts/audit-branch-protection.sh OWNER REPO BRANCH
#   scripts/audit-branch-protection.sh arpitarya fux main
#
# Asserts, against LIVE protection:
#   1. required_status_checks.contexts ⊇ the committed contexts (exact strings)
#   2. enforce_admins == true
#   3. strict, allow_force_pushes, allow_deletions match the committed JSON
# Treats the committed JSON as the source of truth; any difference = drift = exit 1.
# Requires: gh authenticated (read access is enough — no admin needed to audit).
set -euo pipefail

OWNER="${1:?usage: audit-branch-protection.sh OWNER REPO BRANCH}"
REPO="${2:?usage: audit-branch-protection.sh OWNER REPO BRANCH}"
BRANCH="${3:?usage: audit-branch-protection.sh OWNER REPO BRANCH}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$REPO_ROOT/.github/branch-protection.json"
[ -f "$CONFIG" ] || { echo "DRIFT: missing source of truth $CONFIG" >&2; exit 1; }

echo "Auditing branch protection: $OWNER/$REPO@$BRANCH vs $CONFIG"

# Reading branch protection requires admin (administration:read). Distinguish
# three outcomes so a token problem never masquerades as "protected" or as
# benign drift: 404 = genuinely unprotected (real drift); 403 = the token lacks
# admin (config error, must be fixed, not a pass); other = transient.
err="$(mktemp)"
if LIVE="$(gh api "repos/$OWNER/$REPO/branches/$BRANCH/protection" 2>"$err")"; then
  rm -f "$err"
else
  msg="$(cat "$err")"; rm -f "$err"
  if echo "$msg" | grep -q "Branch not protected"; then
    echo "DRIFT: branch $BRANCH is NOT protected (Branch not protected)." >&2
    exit 1
  fi
  if echo "$msg" | grep -qiE "403|must have admin|administration"; then
    echo "AUDIT ERROR: token lacks admin to read branch protection (need a PAT with" >&2
    echo "  'repo'/administration:read). This is a config error, NOT a pass." >&2
    echo "  Detail: $msg" >&2
    exit 2
  fi
  echo "AUDIT ERROR: could not read protection: $msg" >&2
  exit 2
fi

fail=0
note() { echo "  DRIFT: $*" >&2; fail=1; }

# --- 1. required contexts: every committed context must be live -------------
want_ctx="$(jq -r '.required_status_checks.checks[].context' "$CONFIG" | sort)"
live_ctx="$(echo "$LIVE" | jq -r '.required_status_checks.contexts[]?' | sort)"
echo "  expected required checks: $(echo "$want_ctx" | tr '\n' ' ')"
echo "  live required checks:     $(echo "$live_ctx" | tr '\n' ' ')"
missing="$(comm -23 <(echo "$want_ctx") <(echo "$live_ctx"))"
[ -z "$missing" ] || note "required check(s) missing from live protection: $(echo "$missing" | tr '\n' ' ')"
extra="$(comm -13 <(echo "$want_ctx") <(echo "$live_ctx"))"
[ -z "$extra" ] || note "unexpected required check(s) live (not in committed JSON): $(echo "$extra" | tr '\n' ' ')"

# --- 2. enforce_admins must be true ----------------------------------------
[ "$(echo "$LIVE" | jq -r '.enforce_admins.enabled')" = "true" ] \
  || note "enforce_admins is NOT true (the wall is bypassable by admins)"

# --- 3. boolean toggles must match the committed JSON -----------------------
check_bool() { # jq-path-in-config  jq-path-in-live  label
  want="$(jq -r "$1" "$CONFIG")"
  got="$(echo "$LIVE" | jq -r "$2")"
  [ "$want" = "$got" ] || note "$3 drifted (committed=$want, live=$got)"
}
check_bool '.required_status_checks.strict' '.required_status_checks.strict' 'strict'
check_bool '.allow_force_pushes'            '.allow_force_pushes.enabled'    'allow_force_pushes'
check_bool '.allow_deletions'               '.allow_deletions.enabled'       'allow_deletions'

if [ "$fail" -ne 0 ]; then
  echo "✗ branch-protection drift detected — live config differs from $CONFIG." >&2
  echo "  Re-apply with: scripts/apply-branch-protection.sh $OWNER $REPO $BRANCH" >&2
  exit 1
fi
echo "✔ branch protection matches the committed source of truth (no drift)."
