#!/usr/bin/env bash
# Stop hook — if the tree changed but work/NOW.md did not, the session worked
# silently. Nudge once, then relent; a nag that cannot be satisfied is noise.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
[ -n "$(git status --porcelain -- ':!work/NOW.md' 2>/dev/null)" ] || exit 0
[ -z "$(git status --porcelain -- work/NOW.md 2>/dev/null)" ] || exit 0
F=.claude/.progress-nudged
[ -f "$F" ] && exit 0
touch "$F"
jq -n '{hookSpecificOutput:{hookEventName:"Stop",decision:"block",
  reason:"Files changed and work/NOW.md was never updated — the session worked without saying what it was doing. Write one line to work/NOW.md (or `idle` if you are stopping), state the transition, then stop."}}'
exit 0
