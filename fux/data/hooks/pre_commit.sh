#!/usr/bin/env bash
# Fux pre-commit — rebuild the derived views ($0, AST-only) and stage them so
# .fux/out/ always matches the committed code IN THE SAME COMMIT. Non-blocking:
# a build failure warns but never aborts the commit (use `fux gate` to *block* on
# drift). git invokes this with cwd at the repo root. Installed by `fux hooks install`.
set -uo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
. "$DIR/_common.sh"

# Skip during rebase/merge/cherry-pick — don't fight --continue with new changes.
GIT_DIR="$(git rev-parse --git-dir 2>/dev/null || echo .git)"
[ -d "$GIT_DIR/rebase-merge" ] && exit 0
[ -d "$GIT_DIR/rebase-apply" ] && exit 0
[ -f "$GIT_DIR/MERGE_HEAD" ] && exit 0
[ -f "$GIT_DIR/CHERRY_PICK_HEAD" ] && exit 0

# Only act inside a project that has a .fux/ footprint.
fux_run context >/dev/null 2>&1 || exit 0

echo "[fux hook] rebuilding derived views..."
if fux_run build >/dev/null 2>&1; then
  git add .fux/out 2>/dev/null || true   # .session-*.json is gitignored, so skipped
else
  echo "[fux hook] build failed — committing without refreshed views (run \`fux build\`)."
fi
exit 0
