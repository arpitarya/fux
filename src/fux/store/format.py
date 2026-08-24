"""Constants and address functions for the committed store.

Everything here is pure and dependency-free: shard/term hashing and the
`_format` header shape. See `work/compare/index-format.compare.md` §5/§7.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

INDEX_DIR = ".fux/index"

# v2 (W-76 Phase 1 record half, 2026-08-23): five tf fields instead of two,
# trailing zeros omitted, and `wlen` replaced by `flen` (per-field token
# counts) so the length normaliser stops being a function of a tunable.
SCHEMA_ID = "fux.index.v2"
# v2 (W-76 Phase 1, 2026-08-23): identifier splitting before lowercasing,
# plus Porter stemming before hashing. A v1 shard is refused by
# `store/reader.py` rather than silently mixed -- two analyzers in one
# index is undetectable at query time and corrupts every df.
ANALYZER_VERSION = "v2"
#: **Order is load-bearing, and body comes first on purpose.**
#:
#: A tf vector is written with trailing zeros omitted, so the cheapest shape to
#: encode is whichever field is most often the only one present. Measured on
#: this repo (411 documents, 186 799 postings, 2026-08-23):
#:
#:     body only              92.5 %      ->  [1]        3 bytes
#:     heading and body        5.1 %      ->  [1,2]      5 bytes
#:     heading only            2.4 %      ->  [0,2]      5 bytes
#:
#: Body-first plus trailing-zero omission measured **-36.7 %** on the tf
#: vectors in the live index (941 130 B -> 595 492 B) *while going from two
#: fields to five*. Heading-first would have cost +24 %.
#:
#: Reordering this tuple changes every record and is an ADR-recorded format
#: bump, not a refactor.
TF_FIELDS = ("body", "heading", "title", "path", "ctx")

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


def display_title(record: dict, cache=None) -> str:
    """The title a verb shows: `title` when plain, else the P5 display cache's
    materialised title when hashed and warm, else a labelled opaque hash.

    One definition on purpose. Both candidate generators feed the same
    `rank()`, so a display fallback implemented twice is a differential-law
    failure waiting for the two copies to drift. `rank()`'s two call sites
    pass no `cache` — ranking must stay a pure function of the record, so
    that path always returns the bare hash, exactly as before P5. `cache`
    (anything with `.get(sha) -> str | None`, i.e. `store.displaycache.
    DisplayCache` — duck-typed so this module stays import-free of it) is
    for a second, later call on the *same* record, purely for what a reader
    sees, after the accelerator and scan paths have already agreed.
    """
    title = record.get("title")
    if title is not None:
        return title
    hexpart = record.get("title_h", "").removeprefix(TITLE_HASH_PREFIX)
    if cache is None:
        return hexpart
    materialised = cache.get(record.get("sha", ""))
    if materialised is not None:
        return materialised
    return f"{hexpart} (uncached — title unavailable)"


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
