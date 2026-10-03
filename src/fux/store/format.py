"""Constants and address functions for the committed store.

Everything here is pure and dependency-free: shard/term hashing and the
`_format` header shape. See `work/compare/index-format.compare.md` §5/§7.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from ..constants import fixed

INDEX_DIR = fixed("index", "dir")

# v2 (W-76 Phase 1 record half, 2026-08-23): five tf fields instead of two,
# trailing zeros omitted, and `wlen` replaced by `flen` (per-field token
# counts) so the length normaliser stops being a function of a tunable.
# v3 (W-168 step 1, 2026-09-15): a `ref` edge carries `at` (anchor term hash ->
# count) and `al` (the token total), taken from the link text the SOURCE
# document wrote. **A property appeared**, which is exactly what
# SR-INDEX-LIFECYCLE decision 9.1 bumps `_format` for: a v2 index has no `at`
# anywhere, and a reader cannot tell "this corpus links without words" from
# "this index predates anchor text" — the W-48 trap, on the edge.
# `analyzer` is UNTOUCHED (decision 9.2): anchor terms go through the same
# `query/tokenize.py` every other term does, so no hash changes meaning.
# v4 (W-194, 2026-09-20): `meta` and `title_h` are GONE from the record. Arpit
# ruled hashed display meta deleted outright rather than deprecated, so a URL
# record carries a plain `title` and `phrases` like every other record and law
# ex-L5 retires with the mechanism. **A property disappeared**, which bumps
# `_format` for the same reason a property appearing does
# (SR-INDEX-LIFECYCLE decision 9.1): a v3 index can hold records a v4 reader
# has no rule for, and "this record has no title" would otherwise be
# indistinguishable from "this index predates plain titles" — the W-48 trap.
# `analyzer` is UNTOUCHED: no term changed meaning, only which display fields
# a record may carry. **v3 indexes must be rebuilt** — `fux ingest` then
# `fux build`.
# v5 (W-168 step 4, 2026-09-27): a record may carry `abbr`, the hashed
# `Long Form (ABBR)` pairs its own text declares. **A property appeared**
# (SR-INDEX-LIFECYCLE decision 9.1): a v4 index has no `abbr` anywhere, and a
# reader could not tell "this corpus declares no abbreviations" from "this
# index predates the miner". `analyzer` is UNTOUCHED: the pairs go through the
# same analyzer and the same hash as `terms`. **v4 indexes must be rebuilt.**
# v6 (W-168 step 8, 2026-09-30): a git-sourced record carried `authors` and
# `commits`, two counts for the git authority prior. Never released.
# v7 (2026-10-03): the prior FAILED and Arpit ruled it removed with its counts
# (option (c)), so **a property disappeared** (SR-INDEX-LIFECYCLE decision 9.1)
# and the number moves forward, never back to v5: a v6 index holds counts a v7
# reader has no rule for. A v7 record has v5's property set exactly.
# `analyzer` is UNTOUCHED. **v5 and v6 indexes must be rebuilt** — `fux ingest
# --full`.
SCHEMA_ID = fixed("index", "schema")
# v2 (W-76 Phase 1, 2026-08-23): identifier splitting before lowercasing,
# plus Porter stemming before hashing. A v1 shard is refused by
# `store/reader.py` rather than silently mixed -- two analyzers in one
# index is undetectable at query time and corrupts every df.
#
# v3 (W-205 part 2, family (a), 2026-09-21): `-`, `.` and `/` are identifier
# separators exactly as `_` already was, so `RF-118` yields the whole token
# `rf-118` beside its parts instead of only `rf` and `118`.
#
# 🔴 **This is an ANALYZER bump and NOT a `_format` bump, deliberately.** No
# property appeared and no field changed meaning -- every record has the same
# shape it had, and what moved is which terms are in it. The header carries
# `analyzer` as its own field precisely so that case has its own refusal, and
# `store/reader.py` already refuses a shard written by another analyzer. Bumping
# `_format` as well would claim a schema change that did not happen and would
# force consumers through a migration path for a re-ingest they need anyway.
ANALYZER_VERSION = fixed("index", "analyzer")
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
#: Reordering this tuple changes every record and is an SR-recorded format
#: bump, not a refactor.
TF_FIELDS = tuple(fixed("index", "tf_fields"))

_TERM_HASH_BYTES = fixed("index", "term_hash_bytes")
_CONTENT_SHA_BYTES = fixed("index", "content_sha_bytes")

# The first line of every shard — pins schema, analyzer, and tf-array order
# so a reader never has to guess field meaning from position alone.
HEADER: dict = {
    "_format": SCHEMA_ID,
    "analyzer": ANALYZER_VERSION,
    "tf_fields": list(TF_FIELDS),
}

#: The key the repo's identifier-family digest is stamped under (W-233).
IDENTIFIERS_KEY = fixed("identifiers", "header_key")


def header_for(ids_digest: str) -> dict:
    """The header THIS repo's shards carry: `HEADER`, plus the effective
    identifier-family digest when the repo declares any families.

    **Absent means no families, and that is true of every index written before
    W-233** — no families existed — so the field needs no `_format` bump
    (SR-INDEX-LIFECYCLE decision 9.1 concerns a property whose absence is
    ambiguous; this one's is not). The readers check `_format`, `analyzer` and
    `tf_fields` by name and ignore it: they see a shard, not a repo, and cannot
    know which families it should carry. `doctor`, `ingest --check` and
    ingest's own reuse gate compare it against `.fux/identifiers.toml`.
    """
    return {**HEADER, IDENTIFIERS_KEY: ids_digest} if ids_digest else dict(HEADER)


def term_hash(term: str) -> str:
    """16-hex (8-byte) blake2b digest of a term — the postings key."""
    return hashlib.blake2b(term.encode("utf-8"), digest_size=_TERM_HASH_BYTES).hexdigest()


def display_title(record: dict) -> str:
    """The title a verb shows.

    ⚠ **W-194, 2026-09-20 — this used to be the interesting function here**,
    and it is now a `.get`. It carried the three-way fallback a `hashed`
    record needed: `title` when plain, the display cache's materialised title
    when hashed and warm, else a labelled opaque hash. `meta`, `title_h` and
    the cache are all deleted, so every record carries a readable `title` and
    there is nothing to fall back to.

    **It is kept as a function anyway**, for the reason it was one: both
    candidate generators feed the same `rank()`, and a display rule
    implemented at six call sites is a differential-law failure waiting for
    two of them to drift. The `cache=` parameter is gone; every caller passed
    `None` except the one display-only path in `query/__init__.py`, which is
    deleted with it.
    """
    return record.get("title", "")


def content_sha(content: bytes) -> str:
    """40-hex (20-byte) blake2b digest of raw file bytes — the ledger `sha`.

    Same hash family as `term_hash`/`shard_for`, deliberately not a literal
    git blob sha1 (decided during M1 build; see SR-RECORD).
    """
    return hashlib.blake2b(content, digest_size=_CONTENT_SHA_BYTES).hexdigest()


def shard_for(doc_id: str) -> str:
    """2-hex (1-byte) blake2b digest of the doc id — its shard bucket."""
    return hashlib.blake2b(doc_id.encode("utf-8"), digest_size=1).hexdigest()


def shard_path(root: Path, shard: str) -> Path:
    return root / INDEX_DIR / f"{shard}.jsonl"


def index_dir(root: Path) -> Path:
    return root / INDEX_DIR
