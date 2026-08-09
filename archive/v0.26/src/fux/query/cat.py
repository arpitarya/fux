"""`fux cat <doc-id>` — materialize one document, wherever it lives.

A document's text can sit in three places, and the caller should not have to
care which: a curated cache file, a `docs_text` row (bulk tier, where there is
no file on disk at any corpus size), or nowhere at all — in which case Fux
re-derives it from the source, which determinism guarantees yields the same
bytes the index was built from.

Resolution order follows cost: cache file, then db row, then re-conversion.
"""

from __future__ import annotations

from pathlib import Path

from ..config import Config, find_root, load
from ..errors import FuxError
from ..frontmatter import parse as fm_parse


def document_text(config: Config, doc_id: str) -> str:
    """Converted markdown for ``doc_id``. Raises FuxError when it isn't in the corpus."""
    from ..index import sqlstore
    from ..ingest.manifest import read as manifest_read

    entries = manifest_read(config.root)
    entry = entries.get(doc_id) or _by_doc_id(entries, doc_id)
    if entry is None:
        # Fresh clone: the manifest lives in the gitignored runtime plane, so
        # `fux.lock` is the only record of what the corpus contains.
        entry = _from_lock(config, doc_id)

    if entry and entry.get("cache"):
        path = config.root / entry["cache"]
        if path.is_file():
            return fm_parse(path.read_text(encoding="utf-8")).body

    stored = sqlstore.load_text(config.root, doc_id)
    if stored is not None:
        return stored

    if entry:
        derived = _rederive(config, entry)
        if derived is not None:
            return derived

    hint = Path(doc_id).stem or doc_id
    raise FuxError(f'no document {doc_id!r} in the corpus — try `fux find "{hint}"`')


def _from_lock(config: Config, doc_id: str) -> dict | None:
    """Synthesize the minimum entry needed to re-derive, straight from the lock."""
    from ..ingest.lock import read as lock_read

    record = lock_read(config.root).get(doc_id)
    if record is None or record.get("kind") == "url":
        return None  # a web page cannot be re-derived offline; it must be re-fetched
    return {"source": doc_id, "sha256": record.get("sha256", "")}


def _by_doc_id(entries: dict[str, dict], doc_id: str) -> dict | None:
    """Web docs are manifest-keyed by URL but addressed by their `web:` id."""
    from ..index import doc_id_for

    for entry in entries.values():
        if doc_id_for(entry) == doc_id:
            return entry
    return None


def _rederive(config: Config, entry: dict) -> str | None:
    """Re-convert from the source — the lean profile's whole premise, used here."""
    source = config.root / entry["source"]
    if not source.is_file():
        return None
    from ..ingest.convert import convert
    from ..ingest.walk import walk

    for sf in walk(config).files:
        if sf.rel == entry["source"]:
            result = convert(sf, source.read_bytes(), config.ingest.max_kb)
            return None if result.skipped else result.body
    return None


def cmd_cat(args) -> int:
    root = find_root()
    config = load(root)
    text = document_text(config, args.doc)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        data = text.encode("utf-8")
        out.write_bytes(data)
        print(f"wrote {args.out}  ({len(data)} bytes)")
        return 0
    print(text)
    return 0
