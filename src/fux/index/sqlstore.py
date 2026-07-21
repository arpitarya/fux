"""SQLite substrate — `.fux/index/fux.db` (handoff 0004 §A, format_version 2).

One file on disk at any corpus size. `sqlite3` is stdlib, so this costs the
`$0` guarantee nothing; SQLite is **storage, not scoring** — Fux's own BM25F
stays the ranker, and :func:`load` hands back exactly the dict shape the JSON
store returns so the two backends are provably interchangeable (goldens prove
it, rather than a comment asserting it).

Determinism rules, all load-bearing:

- every write is sorted by primary key, so the file is reproducible;
- ingest is the single writer and holds `.fux/index/.lock`; a second ingest
  exits with a clear error rather than corrupting a half-built db;
- queries open read-only; WAL keeps a reader and the writer from blocking.

The db is *derived state*. Recovery is always delete-and-re-ingest, verified
against `fux.lock` — which is why an incompatible ``format_version`` rebuilds
instead of migrating.
"""

from __future__ import annotations

import os
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from ..errors import FuxError

DB_REL = ".fux/index/fux.db"
LOCKFILE_REL = ".fux/index/.lock"
FORMAT_VERSION = 2

_SLUG_RE = re.compile(r"[^a-z0-9]+")

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta      (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS docs      (doc_id TEXT PRIMARY KEY, kind TEXT, source TEXT, sha256 TEXT,
                                      fidelity TEXT, converter TEXT, title TEXT, outline TEXT,
                                      top_terms TEXT, converted_at TEXT, bytes INTEGER);
CREATE TABLE IF NOT EXISTS docs_text (doc_id TEXT PRIMARY KEY REFERENCES docs, text BLOB);
CREATE TABLE IF NOT EXISTS chunks    (chunk_id TEXT PRIMARY KEY, doc_id TEXT, ordinal INTEGER,
                                      heading_path TEXT, line_start INTEGER, line_end INTEGER,
                                      text TEXT, words INTEGER);
CREATE TABLE IF NOT EXISTS postings  (term TEXT, chunk_id TEXT, tf_heading INTEGER, tf_path INTEGER,
                                      tf_body INTEGER, PRIMARY KEY (term, chunk_id));
CREATE INDEX IF NOT EXISTS postings_term ON postings(term);
CREATE TABLE IF NOT EXISTS vectors   (chunk_id TEXT PRIMARY KEY, v BLOB);
CREATE TABLE IF NOT EXISTS doc_codes (doc_id TEXT PRIMARY KEY, code BLOB);
CREATE TABLE IF NOT EXISTS edges     (src TEXT, kind TEXT, dst TEXT, grade TEXT,
                                      PRIMARY KEY (src, kind, dst));
CREATE INDEX IF NOT EXISTS edges_src ON edges(src);
CREATE INDEX IF NOT EXISTS edges_dst ON edges(dst);
CREATE TABLE IF NOT EXISTS frontier  (url TEXT PRIMARY KEY, state TEXT, sha256 TEXT,
                                      fetched_at TEXT);
"""


def db_path(root: Path) -> Path:
    return root / DB_REL


def chunk_id(doc_id: str, heading_path: str, ordinal: int) -> str:
    """`doc_id#<heading-slug>#<ordinal>` — stable under unrelated edits.

    Citations survive re-ingest because the id derives from position in the
    document's own structure, not from a global counter: editing doc A cannot
    renumber doc B, and a doc that genuinely changed legitimately changes its
    own citations (proposal §12).
    """
    slug = _SLUG_RE.sub("-", heading_path.lower()).strip("-")
    return f"{doc_id}#{slug}#{ordinal}"


def connect(root: Path, *, write: bool = False) -> sqlite3.Connection:
    path = db_path(root)
    if not write and not path.is_file():
        raise FuxError("no index found — run `fux ingest` first")
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        if write:
            conn.executescript(SCHEMA)
    except sqlite3.DatabaseError as exc:
        # The db is derived state, so recovery is always the same: throw it away
        # and rebuild, verified against fux.lock. Say that, don't just re-raise.
        conn.close()
        raise FuxError(
            f"fux.db is corrupt ({exc}) — delete {DB_REL} and re-run `fux ingest`"
        ) from exc
    return conn


@contextmanager
def writer(root: Path):
    """Single-writer ingest scope: takes `.fux/index/.lock`, commits or rolls back."""
    lockfile = root / LOCKFILE_REL
    lockfile.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(lockfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise FuxError(
            f"another ingest is running (lock: {LOCKFILE_REL}) — "
            "wait for it, or delete the lock file if no ingest is active"
        ) from None
    os.close(fd)
    conn = connect(root, write=True)
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()
        lockfile.unlink(missing_ok=True)


def save(
    root: Path,
    files: dict[str, dict],
    *,
    profile: str = "full",
    bulk_text: dict[str, str] | None = None,
    edges: list | None = None,
) -> None:
    """Persist the chunk index. ``files``: doc_id → the JSON store's dict shape.

    ``bulk_text`` holds mirror-tier documents whose converted markdown has no
    file on disk; it becomes `docs_text` rows, which is what keeps a 100k-page
    crawl to one file instead of 100k inodes.
    """
    from .bm25f import path_tokens, tokenize
    from collections import Counter

    bulk_text = bulk_text or {}
    with writer(root) as conn:
        conn.execute("DELETE FROM docs")
        conn.execute("DELETE FROM chunks")
        conn.execute("DELETE FROM postings")
        conn.execute("DELETE FROM docs_text")
        conn.execute("DELETE FROM edges")
        conn.executemany(
            "INSERT INTO docs_text VALUES (?,?)",
            [(doc_id, bulk_text[doc_id].encode("utf-8")) for doc_id in sorted(bulk_text)],
        )
        conn.executemany(
            "INSERT INTO edges VALUES (?,?,?,?)",
            sorted(e.as_row() for e in (edges or [])),
        )
        _set_meta(conn, "format_version", str(FORMAT_VERSION))
        _set_meta(conn, "profile", profile)
        doc_rows, chunk_rows, posting_rows = [], [], []
        for doc_id in sorted(files):
            meta = files[doc_id]
            doc_rows.append(
                (
                    doc_id, meta.get("kind", "file"), meta.get("source", doc_id),
                    meta["sha256"], meta.get("fidelity", "inferred"),
                    meta.get("converter", ""), meta.get("title", ""),
                    meta.get("outline", ""), meta.get("top_terms", ""),
                    meta.get("converted_at", ""), meta.get("bytes", 0),
                )
            )
            ptoks = Counter(path_tokens(doc_id))
            title = meta.get("title", "")
            for ordinal, chunk in enumerate(meta["chunks"]):
                cid = chunk_id(doc_id, chunk["heading"], ordinal)
                chunk_rows.append(
                    (
                        cid, doc_id, ordinal, chunk["heading"], chunk["start"],
                        chunk["end"], chunk["text"], chunk.get("words", 0),
                    )
                )
                htoks = Counter(tokenize(chunk["heading"]) + tokenize(title))
                btoks = Counter(tokenize(chunk["text"]))
                for term in sorted(set(htoks) | set(ptoks) | set(btoks)):
                    posting_rows.append(
                        (term, cid, htoks[term], ptoks[term], btoks[term])
                    )
        conn.executemany("INSERT INTO docs VALUES (?,?,?,?,?,?,?,?,?,?,?)", doc_rows)
        conn.executemany("INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?)", chunk_rows)
        conn.executemany(
            "INSERT INTO postings VALUES (?,?,?,?,?)", sorted(posting_rows)
        )


def load(root: Path) -> dict[str, dict]:
    """Read back the JSON store's exact dict shape — this is what buys parity."""
    conn = connect(root)
    try:
        version = _get_meta(conn, "format_version")
        if version != str(FORMAT_VERSION):
            raise FuxError(
                f"fux.db format {version!r} unsupported — re-run `fux ingest`"
            )
        files: dict[str, dict] = {}
        for row in conn.execute(
            "SELECT doc_id, sha256, fidelity, title, outline, top_terms FROM docs "
            "ORDER BY doc_id"
        ):
            files[row[0]] = {
                "sha256": row[1], "fidelity": row[2], "title": row[3],
                # the thin doc-level layer: what `explain` and node-seeded
                # retrieval read instead of re-opening the document
                "outline": row[4], "top_terms": row[5], "chunks": [],
            }
        for row in conn.execute(
            "SELECT doc_id, heading_path, text, line_start, line_end, words "
            "FROM chunks ORDER BY doc_id, ordinal"
        ):
            if row[0] in files:
                files[row[0]]["chunks"].append(
                    {
                        "heading": row[1], "text": row[2],
                        "start": row[3], "end": row[4], "words": row[5],
                    }
                )
        return files
    except sqlite3.DatabaseError as exc:
        raise FuxError(f"fux.db is corrupt ({exc}) — delete it and re-run `fux ingest`") from exc
    finally:
        conn.close()


def load_text(root: Path, doc_id: str) -> str | None:
    """Converted text for a bulk-tier document, or None if it isn't stored here."""
    if not db_path(root).is_file():
        return None
    conn = connect(root)
    try:
        row = conn.execute("SELECT text FROM docs_text WHERE doc_id=?", (doc_id,)).fetchone()
        return row[0].decode("utf-8") if row else None
    finally:
        conn.close()


def load_edges(root: Path) -> list[tuple[str, str, str, str]]:
    """Every edge, sorted — the adjacency the kernel's expansion walks."""
    if not db_path(root).is_file():
        return []
    conn = connect(root)
    try:
        return list(
            conn.execute("SELECT src, kind, dst, grade FROM edges ORDER BY src, kind, dst")
        )
    finally:
        conn.close()


def list_docs(root: Path) -> list[str]:
    conn = connect(root)
    try:
        return [r[0] for r in conn.execute("SELECT doc_id FROM docs ORDER BY doc_id")]
    finally:
        conn.close()


def _set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (key, value))


def _get_meta(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row[0] if row else None
