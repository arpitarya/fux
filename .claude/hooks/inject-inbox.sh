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
  # The decider is whoever this checkout's git names, so the hook carries no
  # person and can be copied to another repository unchanged.
  DECIDER=$(git config user.name 2>/dev/null); DECIDER=${DECIDER:-the decider}
  INBOX=$(sed -n '/^## Blocked on /,/^---$/p' work/OPEN-WORK.md | sed '1d;$d')
  # An empty inbox is its table plus one `*Empty since YYYY-MM-DD …*` line —
  # SR-WORK-OPEN-QUEUE rule 45a. Matching the rule's own marker is what keeps
  # an empty inbox from being announced as a waiting one.
  case "$INBOX" in
    *"*Empty since "*|"") ;;
    *) echo "<inbox>"; echo "$INBOX"; echo "</inbox>"
       echo "These are waiting on $DECIDER. Name them in your first three lines, with their age." ;;
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
