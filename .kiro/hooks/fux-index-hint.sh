#!/bin/sh
# fux — PreToolUse hint. ADVISORY ONLY: it never blocks a tool call.
#
# This repo ships a committed fux index. The most common failure is an agent
# grepping for a phrase the documents do not use, finding nothing, and
# concluding the repo has no answer. `fux ask` ranks the words that ARE in the
# documents and reports what is missing.
#
# 🔴 Exit 0, always. A hook that blocks `grep` breaks every legitimate use of
# it — reading code, counting matches, checking a log — to serve a suggestion.
# SR-AGENT-SURFACES decision 4: a surface that instructs may not also enforce
# unless the rule is exact. "You might have wanted fux here" is not exact.
set -eu

payload=$(cat 2>/dev/null || true)

case "$payload" in
  *'"tool_name":"Grep"'*|*'"tool_name": "Grep"'*|*grep\ *|*ripgrep*|*' rg '*) ;;
  *) exit 0 ;;
esac

# Only worth saying where an index actually exists.
[ -d "${CLAUDE_PROJECT_DIR:-.}/.fux/index" ] || exit 0

echo "[fux] This repo has a committed fux index. If you are searching for a" >&2
echo "      CONCEPT rather than an exact string, 'fux ask \"<q>\" --json --band'" >&2
echo "      ranks documents and tells you which of your words the corpus lacks." >&2
echo "      Grep is still right for exact strings, code and logs." >&2
exit 0
