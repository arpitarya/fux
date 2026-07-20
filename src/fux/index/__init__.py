"""BM25F index build — from the cache at ingest time, incremental by file sha."""

from __future__ import annotations

from ..config import Config
from ..frontmatter import parse as fm_parse
from ..ingest.chunk import chunk_markdown
from . import store
from .bm25f import Searcher, ScoredChunk, tokenize

__all__ = ["build_index", "load_searcher", "Searcher", "ScoredChunk", "tokenize"]


def build_index(config: Config, entries: list[dict]) -> int:
    """(Re)build `.fux/index/index.json`; unchanged files reuse their chunks."""
    root = config.root
    try:
        prev = store.load(root)
    except Exception:  # first build / older format / corrupt: full rebuild
        prev = {}
    files: dict[str, dict] = {}
    total = 0
    for entry in entries:
        rel = entry["source"]
        cached = prev.get(rel)
        if cached and cached.get("sha256") == entry["sha256"]:
            files[rel] = cached
            total += len(cached["chunks"])
            continue
        cache_path = root / entry["cache"]
        body = fm_parse(cache_path.read_text(encoding="utf-8")).body
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
            "title": entry.get("title", ""),
            "chunks": chunks,
        }
        total += len(chunks)
    store.save(root, files)
    return total


def load_searcher(config: Config) -> Searcher:
    return Searcher(store.load(config.root), config.bm25f)
