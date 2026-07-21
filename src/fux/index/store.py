"""Index (de)serialization: versioned JSON at `.fux/index/index.json`.

Format decision (handoff 0001 open question 1): JSON, not struct-packed binary —
measured load on a ~5k-chunk corpus is tens of milliseconds, well under CLI
startup noise, and JSON keeps the index diffable and debuggable. Recorded in
ADR 0003. Postings are derived in memory at load time from the stored chunks;
only chunks + per-file shas persist, which is what incremental rebuild needs.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..errors import FuxError

INDEX_REL = ".fux/index/index.json"
FORMAT_VERSION = 1


def index_path(root: Path) -> Path:
    return root / INDEX_REL


def save(root: Path, files: dict[str, dict], *, edges: list | None = None) -> None:
    """``files``: source rel → {sha256, line_offset, title, chunks: [chunk dicts]}.

    Edges ride along so the graph verbs work on the small-corpus backend too —
    `fux explain` should not require opting into sqlite.
    """
    path = index_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format": FORMAT_VERSION,
        "files": {k: files[k] for k in sorted(files)},
        "edges": sorted(e.as_row() for e in (edges or [])),
    }
    text = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    if not path.is_file() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")


def load(root: Path) -> dict[str, dict]:
    path = index_path(root)
    if not path.is_file():
        raise FuxError("no index found — run `fux ingest` first")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise FuxError(f"index is corrupt ({exc}) — re-run `fux ingest`") from exc
    if payload.get("format") != FORMAT_VERSION:
        raise FuxError(
            f"index format {payload.get('format')!r} unsupported — re-run `fux ingest`"
        )
    return payload["files"]


def load_edges(root: Path) -> list[tuple[str, str, str, str]]:
    path = index_path(root)
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return []
    return [tuple(e) for e in payload.get("edges", [])]
