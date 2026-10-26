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

# Noon of a YYYY-MM-DD as epoch seconds, by BSD or GNU date; empty if neither parses it.
epoch() { date -j -f "%Y-%m-%d %H:%M" "$1 12:00" +%s 2>/dev/null || date -d "$1 12:00" +%s 2>/dev/null; }

# The inbox stores no age (SR-WORK-OPEN-QUEUE rule 40): add the column here,
# today minus each row's `filed`, on every prompt.
with_age() {
  local today line filed f
  today=$(epoch "$(date +%Y-%m-%d)")
  while IFS= read -r line; do
    filed=$(printf '%s' "$line" | grep -oE '\| [0-9]{4}-[0-9]{2}-[0-9]{2} \|' | head -1 | tr -d '| ')
    case "$line" in
      "| what"*) echo "$line age |" ;;
      "|---"*) echo "$line---|" ;;
      "|"*) f=""; [ -n "$filed" ] && f=$(epoch "$filed")
            if [ -n "$f" ] && [ -n "$today" ]; then echo "$line $(( (today - f + 43200) / 86400 )) d |"
            else echo "$line |"; fi ;;
      *) echo "$line" ;;
    esac
  done
}

if [ -f work/OPEN-WORK.md ]; then
  DECIDER=$(git config user.name 2>/dev/null); DECIDER=${DECIDER:-the decider}
  INBOX=$(sed -n '/^## Blocked on /,/^---$/p' work/OPEN-WORK.md | sed '1d;$d')
  # A queue that stores its own age column (fux's) keeps it; any other gets one computed.
  case "$INBOX" in *'| age |'*) ;; *) INBOX=$(printf '%s\n' "$INBOX" | with_age) ;; esac
  case "$INBOX" in
    *"*Empty since"*|"") ;;
    *) echo "<inbox>"; echo "$INBOX"; echo "</inbox>"
       echo "These are waiting on $DECIDER. Name them in your first three lines, with their age." ;;
  esac
fi

if [ -s work/NOW.md ]; then
  N=$(grep -v '^---' work/NOW.md | grep -v '^type:' | grep -v '^description:' | grep -v '^<!--' | grep -v '^-->' | grep -v '^ ' | grep -v '^$' | head -1)
  case "$N" in
    idle*|"") ;;
    *) echo "<in-flight>$N</in-flight>"
       echo "That is where the last session stopped. Confirm or correct it in your first line." ;;
  esac
fi
exit 0
