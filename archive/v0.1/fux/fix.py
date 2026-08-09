"""Mechanical $0 auto-fixes for `fix`/`--fix` mode (plan §8 auto-fix split).

Deterministic repairs only: drop dead ``code_refs``, bump ``updated`` on stale
rules. Semantic drift (prose no longer matches code) is NOT touched here — that is
handed to Claude as a scoped edit prompt in-session (plan §8).
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

from fux import frontmatter, fmwrite
from fux.findings import Finding


def apply(root: Path, findings: list[Finding]) -> list[str]:
    """Apply mechanical fixes in place. Returns a list of applied-change notes."""
    today = _dt.date.today().isoformat()
    by_rule: dict[str, list[Finding]] = {}
    for f in findings:
        if f.fixable:
            by_rule.setdefault(f.rule_id, []).append(f)
    notes: list[str] = []
    for rule_id, group in by_rule.items():
        path = _locate(root, rule_id)
        if path is None:
            continue
        fm, body = frontmatter.split(path.read_text(encoding="utf-8"))
        changed = _drop_dead_refs(fm, group) or False
        if any(f.kind == "stale" for f in group):
            fm["updated"] = today
            changed = True
            notes.append(f"{rule_id}: bumped updated → {today}")
        if changed:
            path.write_text(fmwrite.dump(fm, body), encoding="utf-8")
    return notes


def _drop_dead_refs(fm: dict, group: list[Finding]) -> bool:
    dead = {f.message.split("missing: ")[-1] for f in group if f.kind == "dead-ref"}
    if not dead or "code_refs" not in fm:
        return False
    kept = [r for r in fm["code_refs"] if r.split("#")[0].rstrip("/") not in dead]
    fm["code_refs"] = kept
    return True


def _locate(root: Path, rule_id: str) -> Path | None:
    base = root / ".fux"
    for path in base.rglob("*.md"):
        fm, _ = frontmatter.split(path.read_text(encoding="utf-8"))
        if str(fm.get("id") or path.stem) == rule_id:
            return path
    return None
