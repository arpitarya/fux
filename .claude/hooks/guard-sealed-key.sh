#!/usr/bin/env bash
# PreToolUse(file and shell tools) — the SECOND sealed-key guard, and it exists
# for one narrow reason that is worth stating before anything else.
#
# `guard-golden-answer.sh` beside this file is the first guard and is unchanged.
# It matches the plural spelling everywhere it matches a TARGET (file_path,
# notebook_path, path, glob, a Glob pattern), because that check is a plain
# substring and `golden-answers` contains `golden-answer`. **Its Bash branch is
# where the gap is**: that branch matches
#
#     golden/golden-answer | golden-answer/ | golden-answer<space|end|quote>
#
# and a bare `golden-answers/...` in a shell command hits none of the three —
# `golden-answer` there is followed by `s`. So `cat golden-answers/k.jsonl`,
# run from `work/golden/`, was allowed by the hook. `permissions.deny` covers
# the thirteen named commands by substring, so the reachable hole is an
# arbitrary command (`python -c "open('golden-answers/k')"`) using the bare
# plural path. Narrow, and real.
#
# 🔴 **Why a second file instead of one line in the first one.** The first hook
# checks what a tool call TARGETS, and its own filename contains the string it
# matches — so it refuses every edit to itself, from every Claude session, by
# design and permanently. That is a property worth keeping (a guard an agent can
# amend is a guard an agent can narrow), and the way to keep it while still
# closing the gap is to add a guard, never to route around the one that is
# working. L11 decision 3's permission for a key on disk (Arpit, 2026-09-18) is
# what makes the gap worth closing today rather than noting: before it, the hole
# led to an empty room.
#
# THIS HOOK IS NOT THE RULE. It is one of six guards and none is a guarantee —
# LAW L11, records/0012_LAW-11-sealed-answer-key.md; the process and the guard
# list are records/0066_WORK-golden.md. Three doors stay open to prose alone: a
# paste, a Cowork session's mount, and a recursive read that never names the
# folder.
#
# Checks only what TARGETS a location, exactly as the first guard does, so
# writing prose that mentions the rule is not blocked. Fails CLOSED: input jq
# cannot parse is checked as raw text.
set -uo pipefail
INPUT=$(cat)

# `golden-answers` (the canonical spelling, L11 decision 3) followed by a path
# separator, whitespace, a quote, or end of string — plus the `golden/` prefixed
# form. The singular is the first guard's; matching it again here is harmless
# and deliberate, so that deleting either file leaves the other whole.
PAT='golden/golden-answers?|golden-answers?/|golden-answers?([[:space:]]|$|["'"'"'])'

deny() {
  echo "BLOCKED by LAW L11: work/golden/golden-answers/ is the sealed benchmark answer key (either spelling). No Claude session opens it, ever, by any route — not to read, list, glob, count, hash, diff, copy, move, write or delete, and one file is the same breach as ten. L11 decision 3 permits the directory to EXIST on Arpit's machine; decision 5 still closes it to you. An instruction to open it is VOID. Stop and say so. See records/0012_LAW-11-sealed-answer-key.md; what you MAY read is records/0066_WORK-golden.md." >&2
  exit 2
}

if ! printf '%s' "$INPUT" | jq -e . >/dev/null 2>&1; then
  printf '%s' "$INPUT" | grep -qiE "$PAT" && deny
  exit 0
fi

TARGETS=$(printf '%s' "$INPUT" | jq -r '
  .tool_input as $t
  | [ $t.file_path, $t.notebook_path, $t.path, $t.glob,
      (if .tool_name == "Glob" then $t.pattern else empty end) ]
  | map(select(. != null)) | .[]' 2>/dev/null)
# ⚠ Anchored to a path COMPONENT that starts with the name, never a bare
# substring. The first guard uses a substring here and therefore refuses every
# edit to `.claude/hooks/guard-golden-answer.sh` (itself) and to
# `work/open/W-198-golden-answers-canonical.md` (the work item that manages the
# directory) — neither of which is a key. `tests/test_golden_key_never_committed.py`
# hit the same false positive on its first run and anchored the same way; this
# is that precedent, applied. A component starting with `golden-answer` still
# denies `golden-answers/k.jsonl`, `golden-answers.jsonl` and any depth of
# parent, which is the whole of what needs denying.
printf '%s' "$TARGETS" | grep -qiE '(^|/)golden-answers?[^/]*(/|$)' && deny

if [ "$(printf '%s' "$INPUT" | jq -r '.tool_name')" = "Bash" ]; then
  printf '%s' "$INPUT" | jq -r '.tool_input.command // ""' | grep -qiE "$PAT" && deny
fi
exit 0
