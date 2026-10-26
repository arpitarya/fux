#!/usr/bin/env bash
# Stop hook — refuse to end a turn while a blocker is unsurfaced.
# Loop guard: three refusals, then let it stop and let the human read the file.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 0
B=work/BLOCKED.json
[ -s "$B" ] || exit 0
jq -e '.decision == "PROCEED"' "$B" >/dev/null 2>&1 && exit 0
jq -e '.surfaced == true'      "$B" >/dev/null 2>&1 && exit 0

N=$(cat .claude/.stop-attempts 2>/dev/null || echo 0)
if [ "$N" -ge 3 ]; then rm -f .claude/.stop-attempts; exit 0; fi
echo $((N + 1)) > .claude/.stop-attempts

REASON=$(jq -r '"\(.decision): \(.reason)"' "$B" 2>/dev/null || echo "work/BLOCKED.json is unresolved")
DECIDER=$(git config user.name 2>/dev/null); DECIDER=${DECIDER:-the decider}
jq -n --arg r "$REASON" --arg d "$DECIDER" '{hookSpecificOutput:{hookEventName:"Stop",decision:"block",
  reason:("A blocker is recorded and has not been surfaced to " + $d + " — " + $r +
  "  State it in one short paragraph, set .surfaced=true in work/BLOCKED.json, and stop. Do not work around it.")}}'
exit 0
