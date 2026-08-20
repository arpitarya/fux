#!/usr/bin/env bash
# UserPromptSubmit — the ONLY hook whose stdout Claude sees as context.
# Prepends anything waiting on a human, so a blocker cannot go unmentioned.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 0
rm -f .claude/.stop-attempts .claude/.progress-nudged

if [ -s work/BLOCKED.json ] && ! jq -e '.decision == "PROCEED"' work/BLOCKED.json >/dev/null 2>&1; then
  echo "<blocked>"; cat work/BLOCKED.json; echo "</blocked>"
  echo "A blocker is open. Say so in your first sentence before anything else."
fi

if [ -f work/OPEN-WORK.md ]; then
  INBOX=$(sed -n '/## Blocked on Arpit/,/^---$/p' work/OPEN-WORK.md | sed '1d;$d')
  case "$INBOX" in
    *"**Empty.**"*|"") ;;
    *) echo "<inbox>"; echo "$INBOX"; echo "</inbox>"
       echo "These are waiting on Arpit. Name them in your first three lines, with their age." ;;
  esac
fi
if [ -s work/NOW.md ]; then
  N=$(grep -v '^<!--' work/NOW.md | grep -v '^ ' | grep -v '^-->' | grep -v '^$' | head -1)
  case "$N" in
    idle*|"") ;;
    *) echo "<in-flight>$N</in-flight>"
       echo "That is where the last session stopped. Confirm or correct it in your first line." ;;
  esac
fi

exit 0
