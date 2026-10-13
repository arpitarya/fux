"""The canonical committed store — sharded doc-major JSONL under
`.fux/index/`. See `work/compare/index-format.compare.md` §5/§7 and
`work/adr/0004_index-format.md` for the frozen schema.
"""

from __future__ import annotations

from . import recordschema
from .canonical import canonical_dumps
from .collisions import CollisionTracker
from .fuxdir import COMMITTED, DECLARED, DERIVED, FUX_DIR, derived_dir, ensure_layout, fux_dir
from .format import (
    ANALYZER_VERSION,
    HEADER,
    IDENTIFIERS_KEY,
    INDEX_DIR,
    SCHEMA_ID,
    TF_FIELDS,
    content_sha,
    display_title,
    header_for,
    index_dir,
    shard_for,
    shard_path,
    term_hash,
    SECTIONS_DIR,
    SECTION_SEP,
    SECTION_SLOTS,
    section_id,
    section_parent,
    section_shard_path,
    sections_dir,
)
from .reader import (
    foreign_url_ids,
    index_header,
    index_is_foreign,
    iter_section_paths,
    iter_shard_paths,
    raw_record_lines,
    read_index,
    read_sections,
    read_shard,
)
from .writer import HEADER_LINE, trim, hash_terms, write_index

__all__ = [
    "recordschema",
    "ANALYZER_VERSION",
    "COMMITTED",
    "DECLARED",
    "DERIVED",
    "FUX_DIR",
    "HEADER",
    "HEADER_LINE",
    "IDENTIFIERS_KEY",
    "header_for",
    "INDEX_DIR",
    "SCHEMA_ID",
    "TF_FIELDS",
    "CollisionTracker",
    "canonical_dumps",
    "content_sha",
    "display_title",
    "derived_dir",
    "foreign_url_ids",
    "ensure_layout",
    "fux_dir",
    "hash_terms",
    "index_dir",
    "index_header",
    "index_is_foreign",
    "iter_section_paths",
    "iter_shard_paths",
    "read_sections",
    "SECTIONS_DIR",
    "SECTION_SEP",
    "SECTION_SLOTS",
    "section_id",
    "section_parent",
    "section_shard_path",
    "sections_dir",
    "raw_record_lines",
    "read_index",
    "read_shard",
    "shard_for",
    "shard_path",
    "term_hash",
    "trim",
    "write_index",
]
