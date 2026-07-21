"""BM25F index build — from the cache at ingest time, incremental by file sha.

Two interchangeable backends live behind this module: the v1 JSON store
(`index.json`) and the SQLite substrate (`fux.db`). They persist the *same
dict shape*, so the `Searcher` — and therefore every score — cannot tell them
apart; `[index] format` only decides where the bytes land.

`auto` keeps small corpora on JSON (a few tens of ms to load, diffable,
debuggable) and switches past `[index] sqlite_threshold` chunks, where loading
one big JSON blob per CLI call stops being free.
"""

from __future__ import annotations

from ..config import Config
from ..frontmatter import parse as fm_parse
from ..graph import edges_from_scans, scan_document
from ..ingest.chunk import chunk_markdown
from . import sqlstore, store
from .bm25f import Searcher, ScoredChunk, tokenize

__all__ = [
    "build_index", "load_searcher", "backend_for", "Searcher", "ScoredChunk", "tokenize",
]


def backend_for(config: Config, chunk_count: int | None = None, *, bulk: bool = False):
    """Pick the persistence backend. ``chunk_count`` is None at read time."""
    fmt = config.index.format
    if bulk:
        return sqlstore  # mirror-tier text has nowhere to live in the JSON store
    if fmt == "json":
        return store
    if fmt == "sqlite":
        return sqlstore
    if chunk_count is None:  # reading: believe the disk, not the heuristic
        if sqlstore.db_path(config.root).is_file():
            return sqlstore
        return store
    return sqlstore if chunk_count >= config.index.sqlite_threshold else store


def build_index(
    config: Config, entries: list[dict], bulk_text: dict[str, str] | None = None
) -> int:
    """(Re)build the chunk index; unchanged files reuse their stored chunks.

    ``bulk_text`` carries mirror-tier documents whose converted text never
    touched the filesystem — it goes into `docs_text` instead of a cache file.
    """
    root = config.root
    bulk_text = bulk_text or {}
    prev = _load_any(config)
    files: dict[str, dict] = {}
    total = 0
    for entry in entries:
        rel = doc_id_for(entry)
        if entry.get("duplicate_of") or not (entry.get("cache") or rel in bulk_text):
            continue  # deduped web content: indexed once, under the first URL
        if rel in bulk_text:  # mirror tier: text lives in the db, not on disk
            body, meta = bulk_text[rel], {}
        else:
            parsed = fm_parse((root / entry["cache"]).read_text(encoding="utf-8"))
            body, meta = parsed.body, parsed.meta
        # Scanned every run, even for unchanged documents: link *resolution* is
        # corpus-wide, so caching a doc's resolved edges would freeze a link
        # that a newly added document has since made resolvable. A regex pass
        # is cheap; the expensive work (chunking, embedding) still gets skipped.
        scan = scan_document(body, meta, entry)

        cached = prev.get(rel)
        if (
            cached
            and cached.get("sha256") == entry["sha256"]
            and cached.get("fidelity") == entry.get("fidelity")
        ):  # an --advanced upgrade changes cache text without changing the source sha
            files[rel] = {
                **cached, "outline": scan["outline"], "top_terms": scan["top_terms"],
                "scan": scan, **_doc_meta(entry),
            }
            total += len(cached["chunks"])
            continue
        offset = entry.get("line_offset")
        chunks = []
        for c in chunk_markdown(body):
            chunks.append(
                {
                    "heading": c.heading_path,
                    "text": c.text,
                    "start": c.start_line + offset if offset is not None else None,
                    "end": c.end_line + offset if offset is not None else None,
                    "words": c.words,
                }
            )
        files[rel] = {
            "sha256": entry["sha256"],
            "fidelity": entry.get("fidelity", "inferred"),
            "title": entry.get("title", ""),
            "chunks": chunks,
            "outline": scan["outline"],
            "top_terms": scan["top_terms"],
            "scan": scan,
            **_doc_meta(entry),
        }
        total += len(chunks)

    # Resolution needs the whole corpus: a newly added document can make an
    # existing link resolve, so edges are rebuilt every ingest from cached scans.
    edges = edges_from_scans(
        {rel: meta["scan"] for rel, meta in files.items() if meta.get("scan")}
    )
    backend = backend_for(config, total, bulk=bool(bulk_text))
    if backend is sqlstore:
        backend.save(root, files, bulk_text=bulk_text, edges=edges)
    else:
        backend.save(root, files, edges=edges)
    _drop_other_backend(config, backend)
    return total


def doc_id_for(entry: dict) -> str:
    """The corpus-wide identity of a source.

    Local files are their POSIX relative path; fetched pages get a logical
    `web:<host>/<path>` id so the same page keeps one identity across the lock,
    the index and the committed state — and so a mirror-tier document, which
    has no file on disk, still has a name you can `fux cat`.
    """
    if entry.get("origin") in ("url", "attachment"):
        from ..ingest.lock import web_doc_id

        return web_doc_id(entry["source"])
    return entry["source"]


def _doc_meta(entry: dict) -> dict:
    """Provenance the sqlite `docs` row carries; the JSON store ignores extras."""
    return {
        "kind": "url" if entry.get("origin") in ("url", "attachment") else "file",
        "source": entry["source"],
        "converter": entry.get("converter", ""),
        "converted_at": entry.get("converted_at", ""),
        "bytes": entry.get("size", 0),
    }


def _load_any(config: Config) -> dict[str, dict]:
    """Previous index from whichever backend wrote it (for incremental reuse)."""
    for backend in (sqlstore, store):
        try:
            return backend.load(config.root)
        except Exception:  # first build / other backend / corrupt: try the next
            continue
    return {}


def _drop_other_backend(config: Config, chosen) -> None:
    """One index on disk, never two — a stale sibling would silently win later."""
    if chosen is sqlstore:
        store.index_path(config.root).unlink(missing_ok=True)
    else:
        for name in (sqlstore.DB_REL, f"{sqlstore.DB_REL}-wal", f"{sqlstore.DB_REL}-shm"):
            (config.root / name).unlink(missing_ok=True)


def load_searcher(config: Config) -> Searcher:
    return Searcher(backend_for(config).load(config.root), config.bm25f)


def load_edges(config: Config) -> list[tuple[str, str, str, str]]:
    """The graph, from whichever backend holds it — sorted, so traversal is stable."""
    return backend_for(config).load_edges(config.root)
