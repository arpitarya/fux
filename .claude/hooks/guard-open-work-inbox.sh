#!/usr/bin/env bash
# PostToolUse(Write|Edit|MultiEdit) — catches a malformed "Blocked on Arpit"
# section the moment a session writes one, instead of at the next test run.
#
# The rule enforced is SR-WORK-OPEN-QUEUE rule 45a — stated once there, NOT
# here (L0): an emptied inbox table is followed by exactly one
# `*Empty since YYYY-MM-DD ...*` line, nothing else. The failure this guards
# against actually happened 2026-09-15: a session emptied the inbox correctly
# but closed it with a multi-paragraph recap of the rulings instead of the
# one-line declaration the record already specifies (see work/LESSONS.md).
#
# THIS HOOK IS NOT THE RULE — tests/test_open_work_is_not_stale.py and
# tests/test_open_work_rows_are_short.py are the gate; this just surfaces the
# same defect inside the session instead of at CI. Advisory would let the
# same mistake ship again silently, and the rule is exact (SR-AGENT-SURFACES
# decision 4), so this one blocks.
#
# Unconditional: re-checks work/OPEN-WORK.md on disk regardless of which file
# the tool call targeted, so it needs no assumption about tool_input's shape.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
[ -f work/OPEN-WORK.md ] || exit 0

REASON=$(python3 scripts/check-open-work-inbox.py 2>/dev/null)
[ -z "$REASON" ] && exit 0

jq -n --arg r "$REASON" '{hookSpecificOutput:{hookEventName:"PostToolUse",decision:"block",
  reason:($r + " — fix the section to match the record before continuing.")}}'
exit 0
