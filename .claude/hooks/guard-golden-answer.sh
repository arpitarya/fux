#!/usr/bin/env bash
# PreToolUse(file and shell tools) — the golden answer key is not for Claude.
#
# work/golden/golden-answer/ holds the benchmark's questions and answers. Arpit,
# Codex and ChatGPT may read it; no Claude session may, by any tool. A leak does
# not fail loudly — it produces a benchmark number that looks exactly like a
# clean one. See work/golden/README.md §The one rule.
#
# Checks only what TARGETS a location — file_path / notebook_path / path / glob
# / a Glob pattern, and a Bash command naming the folder's path — so writing
# prose that mentions the rule is not blocked. It cannot see a recursive grep
# over work/ that never names the folder; the .gitignore entry (rg and Grep skip
# ignored paths) and CLAUDE.md §Golden answer key cover that.
# Fails CLOSED: input jq cannot parse is checked as raw text.
set -uo pipefail
INPUT=$(cat)
deny() {
  echo "BLOCKED: work/golden/golden-answer/ is the sealed benchmark answer key. Claude sessions never read, list, grep, hash or edit it — see work/golden/README.md §The one rule." >&2
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
