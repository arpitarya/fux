#!/usr/bin/env bash
# PreToolUse(Write|Edit|MultiEdit|NotebookEdit) — per-asset write lock.
# Two sessions editing the SAME file is how a doc starts lying. Two sessions
# editing DIFFERENT files have no conflict and should run in parallel, not
# serialize behind one repo-wide lock.
#
# Each locked asset gets its own lock dir under .claude/.locks/<key>/, keyed
# by a hash of its repo-relative path, holding an `owner` file
# "SESSION TIMESTAMP PATH". `mkdir` is the mutex (atomic — only one process
# can create a given directory), so two hooks racing on the same asset never
# both win. A lock older than TTL is stale and is silently reclaimed.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 0

LOCKS_DIR=.claude/.locks
mkdir -p "$LOCKS_DIR"

ME="${CLAUDE_SESSION_ID:-$PPID}"
NOW=$(date +%s)
TTL=900

INPUT=$(cat)
FILE_PATH=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' 2>/dev/null)

# Unexpected tool_input shape — fail open rather than block on a lock we
# cannot key correctly.
if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Normalize to a repo-relative path so the same file locks the same way
# regardless of how it was addressed (absolute vs relative).
case "$FILE_PATH" in
  /*) REL="${FILE_PATH#"$(pwd)"/}" ;;
  *)  REL="$FILE_PATH" ;;
esac

KEY=$(printf '%s' "$REL" | shasum -a 256 | cut -c1-16)
LOCKDIR="$LOCKS_DIR/$KEY"
OWNERFILE="$LOCKDIR/owner"

acquire() {
  echo "$ME $NOW $REL" > "$OWNERFILE"
}

# Fresh lock on this asset — nobody holds it, take it.
if mkdir "$LOCKDIR" 2>/dev/null; then
  acquire
  exit 0
fi

# Lock dir exists — read who holds it.
if [ -f "$OWNERFILE" ]; then
  OWNER=$(cut -d' ' -f1 "$OWNERFILE"); WHEN=$(cut -d' ' -f2 "$OWNERFILE")
else
  OWNER=""; WHEN=0
fi

# Re-entrant: this session already holds this asset. Refresh and continue.
if [ "$OWNER" = "$ME" ]; then
  acquire
  exit 0
fi

# Someone else holds it, and recently enough that it's a live conflict.
if [ -n "$OWNER" ] && [ $((NOW - WHEN)) -lt $TTL ]; then
  AGE=$((NOW - WHEN))
  jq -n --arg o "$OWNER" --arg f "$REL" --arg age "$AGE" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",
      permissionDecision:"deny",
      permissionDecisionReason:("Another Claude session (" + $o + ") is editing " + $f + " (touched " + $age + "s ago, lock TTL 900s). Do not write to " + $f + " — work on a different asset instead, or wait. This is a per-asset lock: other files are free to edit in parallel; only " + $f + " conflicts.")}}'
  exit 0
fi

# Stale (TTL expired) or unreadable owner file — reclaim.
acquire
exit 0
