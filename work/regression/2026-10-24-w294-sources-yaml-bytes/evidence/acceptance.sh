#!/usr/bin/env bash
# W-294 step 10 — the conversion changes no committed index byte.
#
#   OLD_PY  a python whose `fux` is the pre-W-294 engine (main before the merge)
#   NEW_PY  a python whose `fux` is the W-294 engine
#   BASE    the pre-W-294 commit to check out (it holds .fux/sources/{dirs,urls})
#   NEWTREE a checkout of the W-294 commit (its .fux/sources.yaml, .fuxignore, fux.toml)
#
# A: BASE + OLD engine + old lists, `fux ingest`, committed in a scratch worktree.
# B: the same tree with ONLY the three converted source files swapped in,
#    `fux ingest --full` by the NEW engine. Expect: `git diff -- .fux/index` empty.
set -euo pipefail
: "${OLD_PY:?}" "${NEW_PY:?}" "${BASE:?}" "${NEWTREE:?}"
S="$(mktemp -d)/accept"
git worktree add -q --detach "$S" "$BASE"
trap 'git worktree remove --force "$S"' EXIT
cd "$S"
"$OLD_PY" -m fux.cli ingest >/dev/null 2>&1
git add -A .fux/index
git -c commit.gpgsign=false commit -qm "A: old engine, old lists" --no-verify
cp "$NEWTREE/.fux/sources.yaml" .fux/sources.yaml
cp "$NEWTREE/.fux/.fuxignore" .fux/.fuxignore
cp "$NEWTREE/fux.toml" fux.toml
git rm -rq .fux/sources/dirs .fux/sources/urls
"$NEW_PY" -m fux.cli ingest --full 2>&1 | head -1
echo "index diff lines: $(git diff -- .fux/index | wc -l | tr -d ' ')"
git diff --stat -- .fux/.fuxignore | tail -1
