"""Operational manifest — the runtime's private provenance copy.

Since handoff 0004 the *committed* ledger is [`fux.lock`](lock.py) at the repo
root. This file keeps the richer per-source record the runtime needs for
query-time joins (cache path, line offset, title, fidelity) and lives inside
the gitignored runtime plane at `.fux/index/manifest.jsonl`.

The split is deliberate: git carries the recipe (`fux.toml` + `fux.lock`),
never the generated state. Both are written in the same ingest scope, so they
cannot disagree.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from ..config import Config

MANIFEST_REL = ".fux/index/manifest.jsonl"
LEGACY_MANIFEST_REL = ".fux/manifest.jsonl"  # pre-0.23 location; migrated on ingest


def manifest_path(root: Path) -> Path:
    return root / MANIFEST_REL


def read(root: Path) -> dict[str, dict]:
    path = manifest_path(root)
    if not path.is_file():
        path = root / LEGACY_MANIFEST_REL  # readable until the next ingest migrates it
        if not path.is_file():
            return {}
    entries: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue  # permissive: a hand-mangled line loses only itself
        if isinstance(entry, dict) and "source" in entry:
            entries[entry["source"]] = entry
    return entries


def write(root: Path, entries: list[dict]) -> None:
    path = manifest_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(e, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        for e in sorted(entries, key=lambda e: e["source"])
    ]
    text = "\n".join(lines) + ("\n" if lines else "")
    if not path.is_file() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")
    (root / LEGACY_MANIFEST_REL).unlink(missing_ok=True)  # migration: one home only


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class Drift:
    changed: list[str] = field(default_factory=list)
    new: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)  # tracked, gone on disk

    @property
    def clean(self) -> bool:
        return not (self.changed or self.new or self.missing)


def quick_drift(config: Config) -> Drift:
    """Stat-only staleness probe (size + existence) — cheap enough for every ask.

    Reads `fux.lock`, so it stays correct on a fresh clone where the runtime
    manifest does not exist yet.
    """
    from .lock import read as lock_read

    drift = Drift()
    for doc_id, record in lock_read(config.root).items():
        if record.get("kind") == "url":
            continue  # web freshness = age vs re-crawl; never checked passively
        path = config.root / doc_id
        if not path.is_file():
            drift.missing.append(doc_id)
        elif isinstance(record.get("bytes"), int) and path.stat().st_size != record["bytes"]:
            drift.changed.append(doc_id)
    return drift
