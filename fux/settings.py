"""Wire Fux hooks into an agent's JSON settings (plan §8). Idempotent.

Claude (`.claude/settings.json`), Codex (`.codex/hooks.json`), and Copilot
(`.copilot/settings.json`) share one event→hook shape, so one writer serves all
three. Prefers the installed wrapper scripts (~/.claude/fux/hooks/*.sh, which carry
a `python -m fux` fallback) so hooks fire even when the `fux` console script is not
on PATH; falls back to the bare `fux <subcommand>` form otherwise.
"""
from __future__ import annotations

import json
from pathlib import Path

from fux import paths

# event → (wrapper script name, bare-command fallback, optional matcher)
_SPEC = {
    "SessionStart": ("session_start.sh", "fux context", None),
    "PostToolUse": ("post_tool_use.sh", "fux hook-touch", "Edit|Write"),
    "Stop": ("stop.sh", "fux hook-check", None),
}
_RECALL = {"UserPromptSubmit": ("user_prompt_submit.sh", "fux hook-recall", None)}

# agent → settings file (relative to project root)
AGENT_FILES = {
    "claude": Path(".claude") / "settings.json",
    "codex": Path(".codex") / "hooks.json",
    "copilot": Path(".copilot") / "settings.json",
}


def _command(script: str, fallback: str) -> str:
    wrapper = paths.claude_home() / "fux" / "hooks" / script
    return str(wrapper) if wrapper.exists() else fallback


def _entry(script: str, fallback: str, matcher: str | None) -> dict:
    hook = {"hooks": [{"type": "command", "command": _command(script, fallback)}]}
    if matcher:
        hook["matcher"] = matcher
    return hook


def wire_file(path: Path, recall: bool = False) -> Path:
    """Wire the Fux hook spec into one agent settings file. Idempotent per event."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(path.read_text()) if path.exists() else {}
    hooks = data.setdefault("hooks", {})
    spec = {**_SPEC, **(_RECALL if recall else {})}
    for event, (script, fallback, matcher) in spec.items():
        existing = hooks.setdefault(event, [])
        if not _already(existing):
            existing.append(_entry(script, fallback, matcher))
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def wire(root: Path, recall: bool = False) -> Path:
    """Wire Claude's `.claude/settings.json` (the original entry point)."""
    return wire_file(root / AGENT_FILES["claude"], recall=recall)


def unwire_file(path: Path) -> bool:
    """Remove every Fux hook entry from an agent settings file. True if changed."""
    if not path.exists():
        return False
    data = json.loads(path.read_text())
    hooks = data.get("hooks", {})
    changed = False
    for event in list(hooks):
        kept = [e for e in hooks[event]
                if not any("fux" in h.get("command", "") for h in e.get("hooks", []))]
        if len(kept) != len(hooks[event]):
            changed = True
        hooks[event] = kept
        if not hooks[event]:
            del hooks[event]
    if changed:
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return changed


def is_wired(path: Path) -> bool:
    """True if any Fux hook is present in this agent settings file."""
    if not path.exists():
        return False
    hooks = json.loads(path.read_text()).get("hooks", {})
    return any("fux" in h.get("command", "")
               for evs in hooks.values() for e in evs for h in e.get("hooks", []))


def _already(existing: list) -> bool:
    """True if any Fux hook (either wiring form) is already present for this event."""
    cmds = [h.get("command", "") for e in existing for h in e.get("hooks", [])]
    return any("fux" in c for c in cmds)
