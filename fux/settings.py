"""Wire Fux hooks into an agent's JSON settings (plan §8). Idempotent.

Claude (`.claude/settings.json`), Codex (`.codex/hooks.json`), and Copilot
(`.copilot/settings.json`) share one event→hook shape, so one writer serves all
three. Hooks invoke the installed `fux` **console script** directly (`fux context`,
`fux hook-touch`, …) — the package is the single source of truth, no copied wrapper
scripts and no dev-checkout paths baked into a committed settings file. Set
`FUX_PYTHON`/PATH so `fux` resolves; for a missing-PATH safety net the bundled
`~/.claude/fux/hooks/*.sh` wrappers (with a `python -m fux` fallback) still ship and
can be referenced by hand.
"""
from __future__ import annotations

import json
from pathlib import Path

# event → (fux subcommand, optional matcher)
_SPEC = {
    "SessionStart": ("fux context", None),
    "PostToolUse": ("fux hook-touch", "Edit|Write"),
    "Stop": ("fux hook-check", None),
}
_RECALL = {"UserPromptSubmit": ("fux hook-recall", None)}

# agent → settings file (relative to project root)
AGENT_FILES = {
    "claude": Path(".claude") / "settings.json",
    "codex": Path(".codex") / "hooks.json",
    "copilot": Path(".copilot") / "settings.json",
}


def _entry(command: str, matcher: str | None) -> dict:
    hook = {"hooks": [{"type": "command", "command": command}]}
    if matcher:
        hook["matcher"] = matcher
    return hook


def wire_file(path: Path, recall: bool = False) -> Path:
    """Wire the Fux hook spec into one agent settings file. Idempotent, and
    *migrating*: a re-install rewrites any stale Fux entry (e.g. an old wrapper-script
    path) to the current `fux <subcommand>` form, leaving foreign hooks untouched."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(path.read_text()) if path.exists() else {}
    hooks = data.setdefault("hooks", {})
    spec = {**_SPEC, **(_RECALL if recall else {})}
    for event, (command, matcher) in spec.items():
        kept = [e for e in hooks.get(event, [])
                if not any("fux" in h.get("command", "") for h in e.get("hooks", []))]
        kept.append(_entry(command, matcher))
        hooks[event] = kept
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
