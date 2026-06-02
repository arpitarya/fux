"""Wire Fux hooks into a project's .claude/settings.json (plan §8). Idempotent.

Prefers the installed wrapper scripts (~/.claude/fux/hooks/*.sh, which carry a
`python -m fux` fallback) so hooks work even when the `fux` console script is not
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


def _command(script: str, fallback: str) -> str:
    wrapper = paths.claude_home() / "fux" / "hooks" / script
    return str(wrapper) if wrapper.exists() else fallback


def _entry(script: str, fallback: str, matcher: str | None) -> dict:
    hook = {"hooks": [{"type": "command", "command": _command(script, fallback)}]}
    if matcher:
        hook["matcher"] = matcher
    return hook


def wire(root: Path, recall: bool = False) -> Path:
    path = root / ".claude" / "settings.json"
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


def _already(existing: list) -> bool:
    """True if any Fux hook (either wiring form) is already present for this event."""
    cmds = [h.get("command", "") for e in existing for h in e.get("hooks", [])]
    return any("fux" in c for c in cmds)
