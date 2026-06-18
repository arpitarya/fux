#!/usr/bin/env bash
# Give Claude Code a distinct, auditable git author identity (§2R.3).
#
#   scripts/git-identity-claude.sh
#
# No new GitHub account, no new credential — just a local git author identity so
# Claude-Code-authored commits are distinguishable in history, plus an
# `Agent: claude-code` commit trailer. The human merges the gated PR; this only
# marks WHO wrote the diff. Run once per clone where Claude Code commits.
#
# Solo-dev scope: a separate GitHub account is DEFERRED (§2R.4) — it buys only a
# forced approval click, which a solo maintainer reviewing his own gated PRs
# doesn't need. Revisit when a second human or a second agent joins.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$REPO_ROOT/.gitmessage-claude"

git -C "$REPO_ROOT" config user.name  "Claude (agent)"
git -C "$REPO_ROOT" config user.email "claude-code@fux.local"
git -C "$REPO_ROOT" config commit.template "$TEMPLATE"

echo "Claude Code git identity set for $REPO_ROOT:"
echo "  user.name        = $(git -C "$REPO_ROOT" config user.name)"
echo "  user.email       = $(git -C "$REPO_ROOT" config user.email)"
echo "  commit.template  = $(git -C "$REPO_ROOT" config commit.template)"
echo
echo "Commits made here carry an 'Agent: claude-code' trailer (see $TEMPLATE)."
echo "To revert to your human identity: git config --unset user.name; git config --unset user.email;"
echo "  git config --unset commit.template"
