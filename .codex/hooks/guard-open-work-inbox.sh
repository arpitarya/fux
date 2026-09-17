#!/usr/bin/env bash
# PostToolUse(shell) advisory — catches a malformed "Blocked on Arpit"
# section right after a session writes one.
#
# The rule enforced is SR-WORK-OPEN-QUEUE rule 45a — stated once there, NOT
# here (L0). See .claude/hooks/guard-open-work-inbox.sh for the fuller note
# and the 2026-09-15 failure this guards against (work/LESSONS.md).
#
# 🔴 Advisory here, unlike its Claude counterpart: Codex's file edits run
# through the `shell` tool via apply_patch rather than a separate structured
# Edit call, and this repo has not confirmed Codex's exact deny/block
# contract for PostToolUse. Exiting non-zero on an unconfirmed protocol risks
# a hook that fails closed for the wrong reason (SR-AGENT-SURFACES decision
# 5's silent-failure trap, from the other direction) — so this prints to
# stderr and exits 0, always, until that contract is confirmed and this is
# promoted to match the Claude side.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
[ -f work/OPEN-WORK.md ] || exit 0

REASON=$(python3 scripts/check-open-work-inbox.py 2>/dev/null)
[ -z "$REASON" ] && exit 0

echo "[fux] $REASON — fix before ending the turn." >&2
exit 0
