"""`fux hooks install` — wire Fux across every agent surface from one command.

Four surfaces, all pointing at the *installed package* scripts (~/.claude/fux/hooks),
never a sibling dev checkout:
  git      → .git/hooks/pre-commit shim → packaged pre_commit.sh (build + stage views)
  claude   → .claude/settings.json      (SessionStart/PostToolUse/Stop hooks)
  codex    → .codex/hooks.json
  copilot  → .copilot/settings.json
Idempotent; `uninstall` / `status` mirror it. Git is non-blocking by design.
"""
from __future__ import annotations

import stat
from pathlib import Path

from fux import gitutil, paths, settings

SURFACES = ["git", "claude", "codex", "copilot"]
_MARK = "fux-hook"


def _packaged_precommit() -> Path:
    return paths.claude_home() / "fux" / "hooks" / "pre_commit.sh"


def _shim(target: Path) -> str:
    return (f"#!/bin/sh\n# {_MARK} — installed by `fux hooks install`. Delegates to the\n"
            f"# packaged Fux pre-commit (build derived views + stage them).\n"
            f'HOOK="{target}"\n'
            '[ -x "$HOOK" ] && exec "$HOOK" "$@"\n'
            'exit 0\n')


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
    hook.write_text(_shim(_packaged_precommit()), encoding="utf-8")
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
