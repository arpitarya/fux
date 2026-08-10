"""Constants and address functions for the committed store.

Everything here is pure and dependency-free: shard/term hashing and the
`_format` header shape. See `docs/compare/index-format.compare.md` §5/§7.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

INDEX_DIR = ".fux/index"

SCHEMA_ID = "fux.index.v1"
ANALYZER_VERSION = "v1"
TF_FIELDS = ("heading", "body")

# The first line of every shard — pins schema, analyzer, and tf-array order
# so a reader never has to guess field meaning from position alone.
HEADER: dict = {
    "_format": SCHEMA_ID,
    "analyzer": ANALYZER_VERSION,
    "tf_fields": list(TF_FIELDS),
}


def term_hash(term: str) -> str:
    """16-hex (8-byte) blake2b digest of a term — the postings key."""
    return hashlib.blake2b(term.encode("utf-8"), digest_size=8).hexdigest()


def content_sha(content: bytes) -> str:
    """40-hex (20-byte) blake2b digest of raw file bytes — the ledger `sha`.

    Same hash family as `term_hash`/`shard_for`, deliberately not a literal
    git blob sha1 (decided during M1 build; see ADR-0004).
    """
    return hashlib.blake2b(content, digest_size=20).hexdigest()


def shard_for(doc_id: str) -> str:
    """2-hex (1-byte) blake2b digest of the doc id — its shard bucket."""
    return hashlib.blake2b(doc_id.encode("utf-8"), digest_size=1).hexdigest()


def shard_path(root: Path, shard: str) -> Path:
    return root / INDEX_DIR / f"{shard}.jsonl"


def index_dir(root: Path) -> Path:
    return root / INDEX_DIR
