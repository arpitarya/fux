"""`fux.toml` loading and validation.

Config is a frozen dataclass tree parsed with stdlib ``tomllib``. Validation
raises the single :class:`FuxError` with the offending key path; unknown keys
and tables are ignored (permissive, so newer configs open in older engines).
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .errors import FuxError

CONFIG_NAME = "fux.toml"
SOURCE_TYPES = ("docs", "code", "data", "images")
DEFAULT_EXCLUDES = (
    ".fux",
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
)


@dataclass(frozen=True)
class BM25FParams:
    heading: float = 3.0
    path: float = 2.0
    body: float = 1.0
    k1: float = 1.2
    b: float = 0.75


@dataclass(frozen=True)
class IngestParams:
    max_kb: int = 256
    exclude: tuple[str, ...] = DEFAULT_EXCLUDES


@dataclass(frozen=True)
class AnswerParams:
    max_sentences: int = 5


@dataclass(frozen=True)
class Config:
    root: Path
    sources: dict[str, tuple[str, ...]] = field(default_factory=dict)
    ingest: IngestParams = IngestParams()
    bm25f: BM25FParams = BM25FParams()
    answer: AnswerParams = AnswerParams()
    raw: dict = field(default_factory=dict)


def find_root(start: Path | None = None) -> Path:
    """Nearest ancestor (inclusive) containing fux.toml — like git's root walk."""
    cur = (start or Path.cwd()).resolve()
    for candidate in (cur, *cur.parents):
        if (candidate / CONFIG_NAME).is_file():
            return candidate
    raise FuxError(
        f"no {CONFIG_NAME} found (searched from {cur} upward) — run `fux setup` first"
    )


def load(root: Path) -> Config:
    path = root / CONFIG_NAME
    if not path.is_file():
        raise FuxError(f"no {CONFIG_NAME} in {root} — run `fux setup` first")
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise FuxError(f"{CONFIG_NAME} is not valid TOML: {exc}") from exc

    sources: dict[str, tuple[str, ...]] = {}
    for key, dirs in _table(raw, "sources").items():
        if key not in SOURCE_TYPES:
            raise FuxError(
                f"unknown source type {key!r} in [sources] — valid: {', '.join(SOURCE_TYPES)}"
            )
        if not isinstance(dirs, list) or not all(isinstance(d, str) for d in dirs):
            raise FuxError(f"[sources] {key} must be a list of directory strings")
        sources[key] = tuple(dirs)

    ing = _table(raw, "ingest")
    max_kb = ing.get("max_kb", IngestParams.max_kb)
    if not isinstance(max_kb, int) or isinstance(max_kb, bool) or max_kb <= 0:
        raise FuxError("[ingest] max_kb must be a positive integer")
    exclude = ing.get("exclude", list(DEFAULT_EXCLUDES))
    if not isinstance(exclude, list) or not all(isinstance(e, str) for e in exclude):
        raise FuxError("[ingest] exclude must be a list of names")

    bm = _table(_table(raw, "engine"), "bm25f")
    params = {}
    for name, default in (
        ("heading", 3.0),
        ("path", 2.0),
        ("body", 1.0),
        ("k1", 1.2),
        ("b", 0.75),
    ):
        val = bm.get(name, default)
        if not isinstance(val, (int, float)) or isinstance(val, bool) or val < 0:
            raise FuxError(f"[engine.bm25f] {name} must be a non-negative number")
        params[name] = float(val)
    if params["b"] > 1:
        raise FuxError("[engine.bm25f] b must be between 0 and 1")

    ans = _table(raw, "answer")
    max_sentences = ans.get("max_sentences", AnswerParams.max_sentences)
    if not isinstance(max_sentences, int) or isinstance(max_sentences, bool) or max_sentences <= 0:
        raise FuxError("[answer] max_sentences must be a positive integer")

    return Config(
        root=root,
        sources=sources,
        ingest=IngestParams(max_kb=max_kb, exclude=tuple(exclude)),
        bm25f=BM25FParams(**params),
        answer=AnswerParams(max_sentences=max_sentences),
        raw=raw,
    )


def _table(raw: dict, name: str) -> dict:
    value = raw.get(name, {})
    if not isinstance(value, dict):
        raise FuxError(f"[{name}] must be a table")
    return value
