"""Bounded LRU for the lean profile — derived chunks, kept warm in fux.db.

The lean profile stores no chunk plane, so a query re-derives its candidates'
text. That is cheap for markdown and noticeable for a 200-page PDF, which is
what this cache is for: the working set stays warm and only the long tail pays
the cold-derive cost, once.

Two properties keep it honest:

- **Bounded** by `[index] lean_cache_mb`, evicted least-recently-touched first.
- **Deterministic**: "recently" is a monotonic counter, not a wall clock, so a
  cached entry's content is exactly what a fresh derive would produce and the
  cache can never change a result — only how fast it arrives.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import sqlstore

SCHEMA = """
CREATE TABLE IF NOT EXISTS lean_cache (
    doc_id TEXT PRIMARY KEY, sha12 TEXT, chunks TEXT, bytes INTEGER, touch INTEGER
);
CREATE INDEX IF NOT EXISTS lean_cache_touch ON lean_cache(touch);
"""


def _connect(root: Path, write: bool):
    conn = sqlstore.connect(root, write=write)
    conn.executescript(SCHEMA)
    return conn


def get(root: Path, doc_id: str, sha12: str) -> list[dict] | None:
    """Cached chunks for a document, or None. A changed sha is a miss, not stale data."""
    if not sqlstore.db_path(root).is_file():
        return None
    conn = _connect(root, write=True)
    try:
        row = conn.execute(
            "SELECT chunks, sha12 FROM lean_cache WHERE doc_id=?", (doc_id,)
        ).fetchone()
        if row is None or row[1] != sha12:
            return None
        conn.execute(
            "UPDATE lean_cache SET touch=? WHERE doc_id=?", (_next_touch(conn), doc_id)
        )
        conn.commit()
        return json.loads(row[0])
    finally:
        conn.close()


def put(root: Path, doc_id: str, sha12: str, chunks: list[dict], budget_mb: int) -> None:
    conn = _connect(root, write=True)
    try:
        blob = json.dumps(chunks, ensure_ascii=False, separators=(",", ":"))
        conn.execute(
            "INSERT OR REPLACE INTO lean_cache VALUES (?,?,?,?,?)",
            (doc_id, sha12, blob, len(blob.encode("utf-8")), _next_touch(conn)),
        )
        _evict(conn, budget_mb)
        conn.commit()
    finally:
        conn.close()


def _next_touch(conn) -> int:
    """A counter, not a clock: determinism forbids wall time in stored state."""
    row = conn.execute("SELECT COALESCE(MAX(touch), 0) + 1 FROM lean_cache").fetchone()
    return row[0]


def _evict(conn, budget_mb: int) -> None:
    budget = budget_mb * 1024 * 1024
    total = conn.execute("SELECT COALESCE(SUM(bytes), 0) FROM lean_cache").fetchone()[0]
    if total <= budget:
        return
    for doc_id, size in conn.execute(
        "SELECT doc_id, bytes FROM lean_cache ORDER BY touch ASC, doc_id ASC"
    ).fetchall():
        if total <= budget:
            break
        conn.execute("DELETE FROM lean_cache WHERE doc_id=?", (doc_id,))
        total -= size


def stats(root: Path) -> tuple[int, int]:
    """(entries, bytes) — for tests and `--explain`."""
    if not sqlstore.db_path(root).is_file():
        return (0, 0)
    conn = _connect(root, write=True)
    try:
        row = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(bytes), 0) FROM lean_cache"
        ).fetchone()
        return (row[0], row[1])
    finally:
        conn.close()


def clear(root: Path) -> None:
    if not sqlstore.db_path(root).is_file():
        return
    conn = _connect(root, write=True)
    try:
        conn.execute("DELETE FROM lean_cache")
        conn.commit()
    finally:
        conn.close()
