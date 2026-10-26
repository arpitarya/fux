#!/usr/bin/env bash
# PreToolUse(Write|Edit|MultiEdit|NotebookEdit) — per-asset write lock.
# Two sessions editing the SAME file is how a doc starts lying; two sessions
# editing DIFFERENT files run in parallel. mkdir is the mutex; TTL reclaims.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 0

LOCKS_DIR=.claude/.locks
mkdir -p "$LOCKS_DIR"
NOW=$(date +%s)
TTL=900

# Sweep every lock past its TTL (SR-WORK-CLEANUP decision 8).
for d in "$LOCKS_DIR"/*/; do
  [ -f "$d/owner" ] || continue
  [ $((NOW - $(cut -d' ' -f2 "$d/owner"))) -ge $TTL ] && rm -rf "$d"
done

INPUT=$(cat)
# The owner is the hook input's session_id: $PPID differs per tool call, so a
# session would otherwise lock itself out of the file it just wrote.
ME=$(printf '%s' "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
ME="${ME:-${CLAUDE_SESSION_ID:-$PPID}}"
FILE_PATH=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' 2>/dev/null)
[ -z "$FILE_PATH" ] && exit 0

case "$FILE_PATH" in
  /*) REL="${FILE_PATH#"$(pwd)"/}" ;;
  *)  REL="$FILE_PATH" ;;
esac

KEY=$(printf '%s' "$REL" | shasum -a 256 | cut -c1-16)
LOCKDIR="$LOCKS_DIR/$KEY"
OWNERFILE="$LOCKDIR/owner"

acquire() { echo "$ME $NOW $REL" > "$OWNERFILE"; }

if mkdir "$LOCKDIR" 2>/dev/null; then acquire; exit 0; fi

if [ -f "$OWNERFILE" ]; then
  OWNER=$(cut -d' ' -f1 "$OWNERFILE"); WHEN=$(cut -d' ' -f2 "$OWNERFILE")
else
  OWNER=""; WHEN=0
fi

if [ "$OWNER" = "$ME" ]; then acquire; exit 0; fi

if [ -n "$OWNER" ] && [ $((NOW - WHEN)) -lt $TTL ]; then
  AGE=$((NOW - WHEN))
  jq -n --arg o "$OWNER" --arg f "$REL" --arg age "$AGE" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",
      permissionDecision:"deny",
      permissionDecisionReason:("Another Claude session (" + $o + ") is editing " + $f + " (touched " + $age + "s ago, lock TTL 900s). Do not write to " + $f + " — work on a different asset instead, or wait.")}}'
  exit 0
fi

acquire
exit 0
