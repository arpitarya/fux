"""`fux hooks install` — wire Fux across every agent surface from one command.

Four surfaces, all invoking the *installed* `fux` console script — the package is
the single source of truth, no copied wrapper scripts or dev-checkout paths:
  git      → .git/hooks/pre-commit (self-contained: `fux build` + stage views)
  claude   → .claude/settings.json      (SessionStart/PostToolUse/Stop hooks)
  codex    → .codex/hooks.json
  copilot  → .copilot/settings.json
Idempotent; `uninstall` / `status` mirror it. Git is non-blocking by design.
"""
from __future__ import annotations

import stat
from pathlib import Path

from fux import gitutil, settings

SURFACES = ["git", "claude", "codex", "copilot"]
_MARK = "fux-hook"

# Self-contained pre-commit: resolve `fux` (or `python -m fux`), then rebuild the
# derived views and stage them so .fux/out/ matches the committed code in the same
# commit. Non-blocking; skips during rebase/merge. No external script reference.
_SHIM = f"""#!/bin/sh
# {_MARK} — installed by `fux hooks install`. Rebuild + stage .fux/out/ ($0).
if command -v fux >/dev/null 2>&1; then FUX="fux"; else
  PY="${{FUX_PYTHON:-$(command -v python3.14 || command -v python3 || command -v python)}}"
  [ -n "$PY" ] && "$PY" -c "import fux" 2>/dev/null && FUX="$PY -m fux" || exit 0
fi
G="$(git rev-parse --git-dir 2>/dev/null || echo .git)"
[ -d "$G/rebase-merge" ] || [ -d "$G/rebase-apply" ] && exit 0
[ -f "$G/MERGE_HEAD" ] || [ -f "$G/CHERRY_PICK_HEAD" ] && exit 0
$FUX context >/dev/null 2>&1 || exit 0
echo "[fux hook] rebuilding derived views..."
$FUX build >/dev/null 2>&1 && git add .fux/out 2>/dev/null
exit 0
"""


def _install_git(root: Path) -> str:
    hooks = gitutil.hooks_dir(root)
    if hooks is None:
        return "skipped (not a git repo)"
    hooks.mkdir(parents=True, exist_ok=True)
    hook = hooks / "pre-commit"
    if hook.exists() and _MARK not in hook.read_text(encoding="utf-8", errors="ignore"):
        backup = hook.with_suffix(".pre-fux")
        hook.rename(backup)
        note = f" (existing hook backed up → {backup.name})"
    else:
        note = ""
    hook.write_text(_SHIM, encoding="utf-8")
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return f"{hook}{note}"


def install(root: Path, surfaces: list[str] | None = None, recall: bool = False) -> dict:
    todo = surfaces or SURFACES
    out: dict[str, str] = {}
    if "git" in todo:
        out["git"] = _install_git(root)
    for agent in ("claude", "codex", "copilot"):
        if agent in todo:
            out[agent] = str(settings.wire_file(root / settings.AGENT_FILES[agent], recall=recall))
    return out


def uninstall(root: Path, surfaces: list[str] | None = None) -> dict:
    todo = surfaces or SURFACES
    out: dict[str, str] = {}
    if "git" in todo:
        hooks = gitutil.hooks_dir(root)
        hook = hooks / "pre-commit" if hooks else None
        if hook and hook.exists() and _MARK in hook.read_text(encoding="utf-8", errors="ignore"):
            hook.unlink()
            out["git"] = "removed"
        else:
            out["git"] = "not installed"
    for agent in ("claude", "codex", "copilot"):
        if agent in todo:
            removed = settings.unwire_file(root / settings.AGENT_FILES[agent])
            out[agent] = "removed" if removed else "not installed"
    return out


def status(root: Path) -> dict:
    out: dict[str, bool] = {}
    hooks = gitutil.hooks_dir(root)
    hook = hooks / "pre-commit" if hooks else None
    out["git"] = bool(hook and hook.exists()
                      and _MARK in hook.read_text(encoding="utf-8", errors="ignore"))
    for agent in ("claude", "codex", "copilot"):
        out[agent] = settings.is_wired(root / settings.AGENT_FILES[agent])
    return out
