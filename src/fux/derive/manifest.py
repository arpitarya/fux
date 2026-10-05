"""`manifest.json` — the per-shard content-sha fingerprint `is_fresh()` compares.

**Owned by [SR-RUNTIME-MANIFEST](../../../records/0123_runtime-manifest.md)** since 2026-10-05 (W-261, Arpit's
ruling that every `kind: component` record owns a file). A pure move out of
`derive/_build.py`, which still decides WHEN this file is written (after the
planes it describes, in `build()`'s order) — SR-T1-ACCELERATOR's. What is here
is the manifest's nine keys and their serialization, so a field added
here is a field `is_fresh()` can compare. Its Node twin is `node/src/derive/manifest.mjs`.
"""

from __future__ import annotations

from pathlib import Path

from .. import store as store_mod
from . import format as fmt

__all__ = ["write"]


def write(directory: Path, *, docs: int, terms: int, blocks: int, shard_stamp) -> int:
    """`manifest.json` for one build. `shard_stamp` is `_read_committed`'s
    `(name, sha, size, mtime)` list; only the sha is the manifest's. Returns
    the bytes written."""
    return fmt.write_json(
        directory / fmt.MANIFEST_NAME,
        {
            "schema": fmt.RUNTIME_SCHEMA,
            "index_schema": store_mod.SCHEMA_ID,
            "analyzer": store_mod.ANALYZER_VERSION,
            "block_size": fmt.BLOCK_SIZE,
            "docs_fields": list(fmt.DOCS_FIELDS),
            "docs": docs,
            "terms": terms,
            "blocks": blocks,
            "shards": {name: sha for name, sha, _, _ in shard_stamp},
        },
    )
