"""Constants and address functions for the committed store.

Everything here is pure and dependency-free: shard/term hashing and the
`_format` header shape. See `work/compare/index-format.compare.md` §5/§7.
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


#: `title_h`'s value is the term hash behind this prefix, never a bare one.
#:
#: `query/scan.py` finds a term's `df` by looking for `"<16 hex>"` in the raw
#: bytes of a record, and the accelerator counts the same `df` from the parsed
#: postings. A bare 16-hex `title_h` is a quoted 16-hex token outside `terms`,
#: so the scan counts it and the accelerator does not, and the two paths score
#: the corpus differently. The build refuses such an index rather than
#: diverging (ADR-INDEX-LIFECYCLE decision 6) — which meant the `hashed` meta
#: default, an L5 default, produced an index no `fux build` would accept.
#:
#: **The field shape is the bug, not the check.** Prefixing puts a character
#: between the opening quote and the hex, `"h:30aef0..."`, so the scan's
#: pattern cannot match it and the two paths agree *by construction*. Relaxing
#: the invariant instead would have traded a slow answer for a wrong one.
TITLE_HASH_PREFIX = "h:"


def title_hash(title: str) -> str:
    """`title_h`'s value for a `hashed` record — enough to identify, not to read."""
    return TITLE_HASH_PREFIX + term_hash(title)


def display_title(record: dict) -> str:
    """The title a verb shows: `title` when plain, the opaque hash when hashed.

    One definition on purpose. Both candidate generators feed the same
    `rank()`, so a display fallback implemented twice is a differential-law
    failure waiting for the two copies to drift.
    """
    title = record.get("title")
    if title is not None:
        return title
    return record.get("title_h", "").removeprefix(TITLE_HASH_PREFIX)


def content_sha(content: bytes) -> str:
    """40-hex (20-byte) blake2b digest of raw file bytes — the ledger `sha`.

    Same hash family as `term_hash`/`shard_for`, deliberately not a literal
    git blob sha1 (decided during M1 build; see ADR-RECORD).
    """
    return hashlib.blake2b(content, digest_size=20).hexdigest()


def shard_for(doc_id: str) -> str:
    """2-hex (1-byte) blake2b digest of the doc id — its shard bucket."""
    return hashlib.blake2b(doc_id.encode("utf-8"), digest_size=1).hexdigest()


def shard_path(root: Path, shard: str) -> Path:
    return root / INDEX_DIR / f"{shard}.jsonl"


def index_dir(root: Path) -> Path:
    return root / INDEX_DIR
