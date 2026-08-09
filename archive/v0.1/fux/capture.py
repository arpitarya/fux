"""Opt-in session capture — a deterministic observation queue for `distill` (§17.2).

Borrows the agent-memory "capture" idea but keeps Fux's *authored, not captured*
guarantee: this never writes a `memory` entry and never calls an LLM. On Stop (when
`capture = true`) it records *which* important files changed this session — split
into governed (a rule may need its **why** updated) and uncovered (a candidate new
rule) — with a secret/PII path filter and SHA-256 dedup, into `.fux/capture/`. The
`distill` skill (human-confirmed, in-session) turns the queue into durable entries.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from fux import config, explain, globs, gitutil, paths

# Paths that must never be queued (secrets / credentials / local env).
SECRET_GLOBS = ["**/.env*", "**/*secret*", "**/*.key", "**/*.pem", "**/*.p12",
                "**/*credential*", "**/*.keystore", "**/id_rsa*", "**/*.pfx"]


@dataclass
class Observation:
    path: str
    governed: bool          # a rule already governs this file
    ts: str

    def as_dict(self) -> dict:
        return {"path": self.path, "governed": self.governed, "ts": self.ts}


def _dir(root: Path) -> Path:
    d = paths.Footprint(root).base / "capture"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _seen(root: Path) -> set[str]:
    f = _dir(root) / "seen.json"
    return set(json.loads(f.read_text())) if f.exists() else set()


def _save_seen(root: Path, seen: set[str]) -> None:
    (_dir(root) / "seen.json").write_text(json.dumps(sorted(seen)), encoding="utf-8")


def observe(root: Path, cfg: dict | None = None) -> list[Observation]:
    """Record newly-changed important files as observations; return the new ones."""
    cfg = cfg or config.load(paths.Footprint(root).config)
    important, ignore = cfg["important_globs"], cfg["ignore_globs"]
    seen, new = _seen(root), []
    today = _dt.date.today().isoformat()
    for rel in gitutil.changed_files(root):
        if rel.startswith(".fux/") or not globs.match_any(rel, important):
            continue
        if globs.match_any(rel, ignore) or globs.match_any(rel, SECRET_GLOBS):
            continue
        key = hashlib.sha256(f"{today}:{rel}".encode()).hexdigest()[:16]
        if key in seen:
            continue
        seen.add(key)
        new.append(Observation(rel, bool(explain.refs(root, rel)), today))
    if new:
        with (_dir(root) / "pending.jsonl").open("a", encoding="utf-8") as fh:
            for o in new:
                fh.write(json.dumps(o.as_dict()) + "\n")
        _save_seen(root, seen)
    return new


def pending(root: Path) -> list[dict]:
    f = _dir(root) / "pending.jsonl"
    if not f.exists():
        return []
    return [json.loads(line) for line in f.read_text().splitlines() if line.strip()]


def clear(root: Path) -> None:
    for name in ("pending.jsonl", "seen.json"):
        (_dir(root) / name).unlink(missing_ok=True)


def summary(observations: list[dict]) -> str:
    if not observations:
        return "fux capture: nothing pending."
    gov = [o for o in observations if o["governed"]]
    new = [o for o in observations if not o["governed"]]
    lines = [f"fux capture — {len(observations)} pending observation(s):"]
    if new:
        lines.append(f"  {len(new)} uncovered file(s) (candidate rules): "
                     + ", ".join(o["path"] for o in new[:8]))
    if gov:
        lines.append(f"  {len(gov)} governed file(s) (rule why may need updating): "
                     + ", ".join(o["path"] for o in gov[:8]))
    lines.append("  → run `/fux distill` to turn these into durable memory/adr entries.")
    return "\n".join(lines)
