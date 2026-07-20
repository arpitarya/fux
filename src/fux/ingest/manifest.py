"""Manifest read/write/check — one canonical JSON line per ingested file.

The manifest is machine provenance (the cache frontmatter is the human-facing
copy): sorted by source path, canonical serialization, so two identical ingest
runs are byte-identical and git diffs stay one-line-per-file.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from ..config import Config
from .walk import walk

MANIFEST_REL = ".fux/manifest.jsonl"


def manifest_path(root: Path) -> Path:
    return root / MANIFEST_REL


def read(root: Path) -> dict[str, dict]:
    path = manifest_path(root)
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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class Drift:
    changed: list[str] = field(default_factory=list)
    new: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)  # in manifest, gone on disk

    @property
    def clean(self) -> bool:
        return not (self.changed or self.new or self.missing)


def check_drift(config: Config) -> Drift:
    """Full sha comparison of sources vs the manifest (`fux ingest --check`)."""
    entries = read(config.root)
    drift = Drift()
    walked = {sf.rel: sf for sf in walk(config).files}
    for rel, sf in walked.items():
        entry = entries.get(rel)
        if entry is None:
            drift.new.append(rel)
        elif sha256_bytes(sf.abspath.read_bytes()) != entry.get("sha256"):
            drift.changed.append(rel)
    drift.missing = sorted(set(entries) - set(walked))
    return drift


def quick_drift(config: Config) -> Drift:
    """Stat-only staleness probe (size + existence) — cheap enough for every ask."""
    entries = read(config.root)
    drift = Drift()
    for rel, entry in entries.items():
        path = config.root / rel
        if not path.is_file():
            drift.missing.append(rel)
        elif isinstance(entry.get("size"), int) and path.stat().st_size != entry["size"]:
            drift.changed.append(rel)
    return drift
