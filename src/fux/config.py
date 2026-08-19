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
FIXED_SHARDS = 256  # not yet configurable — shard = blake2b(id, digest_size=1); see ADR-RECORD


def find_root(start: Path | None = None) -> Path | None:
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / CONFIG_NAME).is_file() or (candidate / ".git").exists():
            return candidate
    return None


DEFAULT_FETCHER = ".fux/fetchers/cdp.py"
DEFAULT_URLS_FILE = ".fux/sources/urls"


@dataclass
class UrlSource:
    """`[sources.url]` — consumer-fetcher URL ingestion (ADR-URL-INGEST/0011).

    - `fetcher` — repo-root-relative path to a consumer-owned Python file;
      the default path is `.fux/fetchers/cdp.py` (ADR-FETCHER).
    - `urls_file` — repo-root-relative path to the line-oriented URL list. The
      list is a *file*, not a TOML array: a 5k-entry inline array is one diff
      hunk and one merge conflict, the same argument that sharded the index.
    - `meta` — privacy policy for display fields; `"hashed"` by default (the
      non-git default, a CLAUDE.md non-negotiable), `"plain"` an explicit
      per-source opt-in for public content.
    - `config` — the `[sources.url.config]` table, passed **verbatim** to the
      fetcher's optional `configure(config)` hook. Fux validates that it is
      a table and never reads a key inside it: core knows there *is* config,
      never what it *means*. Same discipline as PEP 518's `[tool.*]` tables,
      and it is what keeps the adapter cap from leaking one fetcher's
      vocabulary into fux's config schema.
    """

    fetcher: str
    urls_file: str
    meta: str  # "hashed" | "plain"
    config: dict


@dataclass
class Config:
    root: Path
    source_dirs: list[str]
    shards: int
    url: UrlSource | None = None


def load(root: Path) -> Config:
    """Parse `fux.toml`: `[sources] dirs`, optional `[sources.url]`, `[index] shards`."""
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

    return Config(root=root, source_dirs=dirs, shards=shards, url=_load_url_source(path, sources.get("url")))


def _load_url_source(path: Path, raw) -> UrlSource | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise FuxError(f"{path}: [sources.url] must be a table")
    if "urls" in raw:
        raise FuxError(
            f"{path}: [sources.url] urls is not a TOML key any more — put one URL per line in "
            f"{DEFAULT_URLS_FILE} (or point urls_file elsewhere)"
        )
    if "middleware" in raw:
        raise FuxError(
            f"{path}: [sources.url] middleware was renamed to fetcher — "
            "rename the key, and move the file from .fux/middleware/ to .fux/fetchers/ "
            "(ADR-FETCHER, 2026-08-19)"
        )
    fetcher = raw.get("fetcher", DEFAULT_FETCHER)
    if not isinstance(fetcher, str) or not fetcher.strip():
        raise FuxError(f"{path}: [sources.url] fetcher must be a path to a consumer-owned .py file")
    urls_file = raw.get("urls_file", DEFAULT_URLS_FILE)
    if not isinstance(urls_file, str) or not urls_file.strip():
        raise FuxError(f"{path}: [sources.url] urls_file must be a path to a line-oriented URL list")
    meta = raw.get("meta", "hashed")
    if meta not in ("hashed", "plain"):
        raise FuxError(f"{path}: [sources.url] meta must be \"hashed\" or \"plain\" (got {meta!r})")
    config = raw.get("config", {})
    if not isinstance(config, dict):  # the ONLY validation fux does on it
        raise FuxError(f"{path}: [sources.url.config] must be a table (got {type(config).__name__})")
    return UrlSource(
        fetcher=fetcher.strip(),
        urls_file=urls_file.strip(),
        meta=meta,
        config=dict(config),
    )
