"""Repo root discovery and `fux.toml` config loading.

Root = the nearest ancestor (starting at `start`, default cwd) that holds
`fux.toml` or a `.git` directory — `fux.toml` wins when both are present at
the same level. No root found is not an error here; callers decide whether
that's fatal.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from .errors import FuxError

CONFIG_NAME = "fux.toml"
FIXED_SHARDS = 256  # not yet configurable — shard = blake2b(id, digest_size=1); see ADR-0004


def find_root(start: Path | None = None) -> Path | None:
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / CONFIG_NAME).is_file() or (candidate / ".git").exists():
            return candidate
    return None


@dataclass
class Config:
    root: Path
    source_dirs: list[str]
    shards: int


def load(root: Path) -> Config:
    """Parse `fux.toml`. Minimal this slice: `[sources] dirs`, `[index] shards`."""
    path = root / CONFIG_NAME
    if not path.is_file():
        raise FuxError(f"no {CONFIG_NAME} at {root} — run from a configured repo")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise FuxError(f"{path}: invalid TOML ({exc})") from exc

    sources = data.get("sources", {})
    dirs = sources.get("dirs")
    if not isinstance(dirs, list) or not dirs or not all(isinstance(d, str) for d in dirs):
        raise FuxError(f"{path}: [sources] dirs must be a non-empty list of strings")

    shards = data.get("index", {}).get("shards", FIXED_SHARDS)
    if shards != FIXED_SHARDS:
        raise FuxError(f"{path}: [index] shards must be {FIXED_SHARDS} this milestone (got {shards!r})")

    return Config(root=root, source_dirs=dirs, shards=shards)
