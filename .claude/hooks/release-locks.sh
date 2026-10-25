#!/usr/bin/env bash
# Stop + SessionEnd — every lock a session takes is cleaned (SR-WORK-CLEANUP
# decisions 8-9).
#
# 1. Per-asset write locks under .claude/.locks/<key>/ (session-lock.sh):
#    this session's own are released; anyone's past the 900-second TTL is swept.
# 2. A git lock file — index.lock, HEAD.lock, a ref's or a worktree's .lock —
#    older than 10 minutes while no git process runs is removed; where unlink
#    fails it is renamed into .git/_stale_locks/.
#
# Never blocks: a hook that cannot clean says nothing and exits 0.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 0

INPUT=$(cat 2>/dev/null || true)
SID=$(printf '%s' "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
ME="${CLAUDE_SESSION_ID:-${SID:-$PPID}}"
NOW=$(date +%s)
TTL=900

# 1 — per-asset write locks.
for owner in .claude/.locks/*/owner; do
  [ -f "$owner" ] || continue
  who=$(cut -d' ' -f1 "$owner"); when=$(cut -d' ' -f2 "$owner")
  case "$when" in ''|*[!0-9]*) when=0 ;; esac
  if [ "$who" = "$ME" ] || [ $((NOW - when)) -gt "$TTL" ]; then
    rm -rf "$(dirname "$owner")"
  fi
done

# 2 — stale git lock files, only while no git process runs.
GITDIR=$(git rev-parse --git-common-dir 2>/dev/null) || exit 0
if pgrep -x git >/dev/null 2>&1; then
  exit 0
fi
find "$GITDIR" -path "$GITDIR/_stale_locks" -prune -o -type f -name '*.lock' -mmin +10 -print 2>/dev/null |
while IFS= read -r lock; do
  rm -f "$lock" 2>/dev/null && continue
  mkdir -p "$GITDIR/_stale_locks" 2>/dev/null &&
    mv "$lock" "$GITDIR/_stale_locks/$(printf '%s' "$lock" | tr '/' '_').$NOW" 2>/dev/null
done
exit 0
