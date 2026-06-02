#!/usr/bin/env bash
# Install the Fux engine into the global layout (plan §4):
#   ~/.claude/fux/engine/   ~/.claude/fux/global/ (git repo)   ~/.claude/fux/packs/
#   ~/.claude/fux/hooks/    ~/.claude/fux/schema.json          ~/.claude/skills/fux/
# $0, idempotent. Run from the repo root.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_FUX="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/fux"
SKILLS="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"

PY="$(command -v python3.14 || command -v python3.13 || command -v python3.12 || command -v python3.11 || command -v python3)"
echo "Using interpreter: $PY ($($PY --version 2>&1))"
case "$($PY -c 'import sys;print(sys.version_info>=(3,11))')" in
  True) ;; *) echo "Fux needs Python ≥3.11 (tomllib). Found $($PY --version)"; exit 1;;
esac

echo "→ engine (editable: repo edits live-reflect in the installed binary)"
mkdir -p "$HOME_FUX"
"$PY" -m pip install -q --user -e "$REPO" || "$PY" -m pip install -q --user --break-system-packages -e "$REPO"
ln -sfn "$REPO" "$HOME_FUX/engine"
cp "$REPO/schema.json" "$HOME_FUX/schema.json"

echo "→ hooks"
mkdir -p "$HOME_FUX/hooks"
cp "$REPO"/hooks/*.sh "$HOME_FUX/hooks/" && chmod +x "$HOME_FUX"/hooks/*.sh

echo "→ packs"
mkdir -p "$HOME_FUX/packs"
cp -R "$REPO"/packs/* "$HOME_FUX/packs/" 2>/dev/null || true

echo "→ global rules (git repo in place — global-rules-home.compare.md verdict B)"
if [ ! -d "$HOME_FUX/global" ]; then
  cp -R "$REPO/global" "$HOME_FUX/global"
  ( cd "$HOME_FUX/global" && git init -q && git add -A && git commit -qm "seed global best practices" )
  echo "  initialised $HOME_FUX/global as a git repo — add a private remote to sync across machines"
else
  echo "  $HOME_FUX/global exists — leaving your versioned rules untouched"
fi

echo "→ /fux skill"
mkdir -p "$SKILLS/fux"
cp -R "$REPO"/skills/fux/* "$SKILLS/fux/"
for s in plan adr trace; do mkdir -p "$SKILLS/fux-$s"; cp -R "$REPO/skills/$s/"* "$SKILLS/fux-$s/" 2>/dev/null || true; done

echo
echo "✔ Fux installed. Verify:  fux --version   (or: $PY -m fux --version)"
echo "  In any project:        fux init  →  fux new formula <id>  →  fux build"
if ! command -v fux >/dev/null 2>&1; then
  echo "  Note: 'fux' is not on PATH yet — add your user-base bin dir:"
  echo "    export PATH=\"\$($PY -c 'import site,os;print(os.path.join(site.USER_BASE,\"bin\"))'):\$PATH\""
fi
