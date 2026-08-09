"""Hook stdin/event helpers (plan §8 I/O contract). Small, side-effect-light."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from fux import config, paths


def event() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}


def root_of(ev: dict) -> Path | None:
    return paths.find_project_root(Path(ev.get("cwd") or Path.cwd()))


def mode_of(root: Path) -> str:
    return config.load(paths.Footprint(root).config).get("mode", "fix")


def edited_rel(ev: dict, root: Path) -> str | None:
    """Repo-relative path of the edited file from a PostToolUse event, if any."""
    fpath = (ev.get("tool_input") or {}).get("file_path")
    if not fpath:
        return None
    try:
        return Path(fpath).resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None
