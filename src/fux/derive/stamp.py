"""`stamp.json` — the cheap, non-reproducible size/mtime pre-check ahead of the manifest.

**Owned by [SR-RUNTIME-STAMP](../../../records/0124_runtime-stamp.md)** since 2026-10-05 (W-261, Arpit's
ruling that every `kind: component` record owns a file). A pure move out of
`derive/_build.py`, which still decides WHEN this file is written (after the
planes it describes, in `build()`'s order) — SR-T1-ACCELERATOR's. What is here
is the stamp's bytes — `[size_bytes, mtime_ns]` per shard — and the
reason it is excluded from `DETERMINISTIC_FILES`: mtimes cannot be reproducible. Its Node twin is `node/src/derive/stamp.mjs`.
"""

from __future__ import annotations

from pathlib import Path

from . import format as fmt

__all__ = ["write"]


def write(directory: Path, shard_stamp) -> int:
    """`stamp.json` for one build — written LAST, so a reader racing the build
    sees no stamp or the old one and falls back to the scan. Returns the bytes."""
    return fmt.write_json(
        directory / fmt.STAMP_NAME,
        {"shards": {name: [size, mtime] for name, _, size, mtime in shard_stamp}},
    )
