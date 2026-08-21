"""The canonical committed store — sharded doc-major JSONL under
`.fux/index/`. See `work/compare/index-format.compare.md` §5/§7 and
`work/adr/0004_index-format.md` for the frozen schema.
"""

from __future__ import annotations

from .canonical import canonical_dumps
from .collisions import CollisionTracker
from .displaycache import DisplayCache
from .fuxdir import COMMITTED, DECLARED, DERIVED, FUX_DIR, derived_dir, ensure_layout, fux_dir
from .format import (
    ANALYZER_VERSION,
    HEADER,
    INDEX_DIR,
    SCHEMA_ID,
    TF_FIELDS,
    TITLE_HASH_PREFIX,
    content_sha,
    display_title,
    index_dir,
    shard_for,
    shard_path,
    term_hash,
    title_hash,
)
from .reader import iter_shard_paths, raw_record_lines, read_index, read_shard
from .writer import HEADER_LINE, hash_terms, write_index

__all__ = [
    "ANALYZER_VERSION",
    "COMMITTED",
    "DECLARED",
    "DERIVED",
    "FUX_DIR",
    "HEADER",
    "HEADER_LINE",
    "INDEX_DIR",
    "SCHEMA_ID",
    "TF_FIELDS",
    "TITLE_HASH_PREFIX",
    "CollisionTracker",
    "DisplayCache",
    "canonical_dumps",
    "content_sha",
    "display_title",
    "derived_dir",
    "ensure_layout",
    "fux_dir",
    "hash_terms",
    "index_dir",
    "iter_shard_paths",
    "raw_record_lines",
    "read_index",
    "read_shard",
    "shard_for",
    "shard_path",
    "term_hash",
    "title_hash",
    "write_index",
]
