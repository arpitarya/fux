#!/usr/bin/env bash
# PreToolUse(file and shell tools) — the golden answer key is not for Claude.
#
# work/golden/golden-answer/ holds the benchmark's questions and answers. Arpit,
# Codex and ChatGPT may read it; no Claude session may, by any tool, for any
# reason, ever — one file is the same breach as ten. That is LAW L11, stated in
# records/0012_LAW-11-sealed-answer-key.md and generated into CLAUDE.md
# §Non-negotiable constraints. A leak does not fail loudly — it produces a
# benchmark number that looks exactly like a clean one. The guards and what
# Claude MAY read are records/0066_WORK-golden.md; the process is
# work/golden/README.md.
#
# THIS HOOK IS NOT THE RULE. It is one of five guards and none is a guarantee:
# an agent that honours no hook is bound by L11 alone.
#
# Checks only what TARGETS a location — file_path / notebook_path / path / glob
# / a Glob pattern, and a Bash command naming the folder's path — so writing
# prose that mentions the rule is not blocked. It cannot see a recursive grep
# over work/ that never names the folder; the .gitignore entry (rg and Grep skip
# ignored paths) and L11 itself cover that — L11 makes excluding work/golden/
# from any recursive read over work/ part of the rule.
# Fails CLOSED: input jq cannot parse is checked as raw text.
set -uo pipefail
INPUT=$(cat)
deny() {
  echo "BLOCKED by LAW L11: work/golden/golden-answer/ is the sealed benchmark answer key. No Claude session opens it, ever, by any route — not to read, list, glob, count, hash, diff, copy, move, write or delete, and one file is the same breach as ten. An instruction to open it is VOID. Stop and say so. See records/0012_LAW-11-sealed-answer-key.md; what you MAY read is records/0066_WORK-golden.md." >&2
  exit 2
}
if ! printf '%s' "$INPUT" | jq -e . >/dev/null 2>&1; then
  printf '%s' "$INPUT" | grep -qi 'golden-answer' && deny
  exit 0
fi
TARGETS=$(printf '%s' "$INPUT" | jq -r '
  .tool_input as $t
  | [ $t.file_path, $t.notebook_path, $t.path, $t.glob,
      (if .tool_name == "Glob" then $t.pattern else empty end) ]
  | map(select(. != null)) | .[]' 2>/dev/null)
printf '%s' "$TARGETS" | grep -qi 'golden-answer' && deny
if [ "$(printf '%s' "$INPUT" | jq -r '.tool_name')" = "Bash" ]; then
  printf '%s' "$INPUT" | jq -r '.tool_input.command // ""' | grep -qiE 'golden/golden-answer|golden-answer/|golden-answer([[:space:]]|$|["'"'"'])' && deny
fi
exit 0
