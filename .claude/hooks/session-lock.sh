#!/usr/bin/env bash
# PreToolUse(Write|Edit|MultiEdit) — one writer at a time.
# Two sessions editing work/OPEN-WORK.md is how the queue starts lying.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 0
LOCK=.claude/.session-lock
ME="${CLAUDE_SESSION_ID:-$PPID}"
NOW=$(date +%s)

if [ -f "$LOCK" ]; then
  OWNER=$(cut -d' ' -f1 "$LOCK"); WHEN=$(cut -d' ' -f2 "$LOCK")
  if [ "$OWNER" != "$ME" ] && [ $((NOW - WHEN)) -lt 900 ]; then
    jq -n --arg o "$OWNER" '{hookSpecificOutput:{hookEventName:"PreToolUse",
      permissionDecision:"deny",
      permissionDecisionReason:("Another Claude session (" + $o + ") holds the write lock and was active in the last 15 minutes. Do not write. Tell Arpit two sessions are running in this repo and stop.")}}'
    exit 0
  fi
fi
echo "$ME $NOW" > "$LOCK"
exit 0
