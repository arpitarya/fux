"""`fux touch <file>` — map a changed file → affected rules (plan §8 PostToolUse).

Session-aware: rules whose own source was edited this session are skipped, so the
PostToolUse hook only nags about rules that drifted, not ones you just updated.
Session state lives in ``.fux/out/.session-<id>.json`` (gitignored).
"""
from __future__ import annotations

import json
from pathlib import Path

from fux import explain, paths
from fux.model import Rule


def _state_path(root: Path, session: str) -> Path:
    fp = paths.Footprint(root)
    fp.out.mkdir(parents=True, exist_ok=True)
    return fp.out / f".session-{session or 'default'}.json"


def mark_rule_edited(root: Path, session: str, rule_id: str) -> None:
    sp = _state_path(root, session)
    edited = set(json.loads(sp.read_text())) if sp.exists() else set()
    edited.add(rule_id)
    sp.write_text(json.dumps(sorted(edited)), encoding="utf-8")


def affected(root: Path, file_rel: str, session: str = "") -> list[Rule]:
    """Rules governing ``file_rel`` that were NOT edited this session."""
    sp = _state_path(root, session)
    edited = set(json.loads(sp.read_text())) if sp.exists() else set()
    return [r for r in explain.refs(root, file_rel) if r.id not in edited]


def is_rule_file(root: Path, file_rel: str) -> bool:
    return file_rel.replace("\\", "/").startswith(".fux/")
