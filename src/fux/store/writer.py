"""The canonical writer: records in, deterministic shard files out.

Always a full, deterministic rewrite of every shard implied by the given
record set — never an in-place patch (§6 non-negotiable). "Incremental" is an
emergent property: a record whose fields haven't changed serializes to the
same bytes it did last run, so a shard whose content is unchanged is left
untouched on disk too (no mtime churn, no spurious rebuild trigger for M2's
accelerator). Deletion is implicit — a doc absent from `records` disappears
from its shard, and a shard with zero current records is removed rather than
left stale.
"""

from __future__ import annotations

import os
from pathlib import Path

from ..errors import FuxError
from .canonical import canonical_dumps
from .collisions import CollisionTracker
from .format import HEADER, index_dir, shard_for, shard_path

HEADER_LINE = canonical_dumps(HEADER)


def write_index(root: Path, records: list[dict]) -> list[Path]:
    """Write the full index from `records` (each must carry a unique `id`).

    Returns the shard paths whose bytes actually changed this call (unchanged
    shards are left untouched, not just byte-identically rewritten). Raises
    `FuxError` on a duplicate id. Term-hash collisions are not this
    function's concern — the caller is expected to hash postings through one
    `CollisionTracker` shared across the whole ingest run (a fresh tracker
    per document catches nothing, since collisions only matter *across*
    documents) before records ever reach here; see `hash_terms`.
    """
    by_shard: dict[str, list[dict]] = {}
    seen_ids: set[str] = set()
    for record in records:
        try:
            doc_id = record["id"]
        except KeyError:
            raise FuxError("record missing required 'id' field") from None
        if doc_id in seen_ids:
            raise FuxError(f"duplicate id in index write: {doc_id!r}")
        seen_ids.add(doc_id)
        by_shard.setdefault(shard_for(doc_id), []).append(record)

    directory = index_dir(root)
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except FileExistsError as exc:
        raise FuxError(f"cannot create index dir, a file is in the way: {directory}") from exc

    written: list[Path] = []
    for shard, group in by_shard.items():
        path = shard_path(root, shard)
        group.sort(key=lambda r: r["id"])
        data = HEADER_LINE + b"".join(canonical_dumps(record) for record in group)
        if not path.exists() or path.read_bytes() != data:
            _atomic_write(path, data)
            written.append(path)

    for shard in {format(i, "02x") for i in range(256)} - by_shard.keys():
        path = shard_path(root, shard)
        path.unlink(missing_ok=True)

    return written


def _atomic_write(path: Path, data: bytes) -> None:
    """Write via a sibling temp file + rename — never leaves a truncated shard."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def hash_terms(terms: dict[str, tuple], tracker: CollisionTracker) -> dict[str, list[int]]:
    """Map raw term -> per-field tf tuple into hashed-key -> tf-list for storage.

    `tracker` must be the single `CollisionTracker` for the whole ingest run —
    passing a fresh one per document silently defeats collision detection,
    since only cross-document collisions are possible (a document's own
    `terms` dict is already deduplicated by construction).
    """
    out: dict[str, list[int]] = {}
    for term, tf in terms.items():
        out[tracker.hash_of(term)] = list(tf)
    return out
