"""Wire Fux hooks into a project's .claude/settings.json (plan §8). Idempotent."""
from __future__ import annotations

import json
from pathlib import Path

# The 3 core hooks `fux init` registers. UserPromptSubmit recall is opt-in.
HOOKS = {
    "SessionStart": [{"hooks": [{"type": "command", "command": "fux context"}]}],
    "PostToolUse": [{"matcher": "Edit|Write",
                     "hooks": [{"type": "command", "command": "fux hook-touch"}]}],
    "Stop": [{"hooks": [{"type": "command", "command": "fux hook-check"}]}],
}
RECALL_HOOK = {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": "fux hook-recall"}]}]}


def wire(root: Path, recall: bool = False) -> Path:
    """Merge Fux hooks into .claude/settings.json without clobbering existing ones."""
    path = root / ".claude" / "settings.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(path.read_text()) if path.exists() else {}
    hooks = data.setdefault("hooks", {})
    wanted = {**HOOKS, **(RECALL_HOOK if recall else {})}
    for event, entries in wanted.items():
        existing = hooks.setdefault(event, [])
        if not _already(existing, entries[0]):
            existing.extend(entries)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def _already(existing: list, entry: dict) -> bool:
    """True if a Fux command hook is already present for this event."""
    cmds = {h.get("command") for e in existing for h in e.get("hooks", [])}
    new_cmds = {h.get("command") for h in entry.get("hooks", [])}
    return bool(cmds & new_cmds)
