"""The canonical writer: records in, deterministic shard files out.

## L5 was enforced here, at write time, and the law retired on 2026-09-20

**Hashed meta was the default for non-git sources, enforced at write time**
(L5). Until M5 that enforcement lived in `ingest/run.py`, which is to say it
lived in *one caller* — so it was a convention that happened to hold rather
than a property of the index. The move here was right: any second writer (an
enrichment pass, a migration script, a test fixture, a consumer using the
library) could otherwise write a private document's title into a committed
file, and nothing would have said no.

It closed an **ACL-mismatch leak**: a document readable by fifty people inside
Confluence becomes a title readable by everyone with the repo. **That leak is
real and is now accepted.** L5 was not wrong about it; it lost on cost.

⚠ **W-194, 2026-09-20 — THE RULE IS GONE, and so is `assert_meta_policy`.**
Arpit ruled `meta=hashed` deleted outright: every record now carries plain
display text, `meta` and `title_h` no longer exist, and **law L5 retires with
the mechanism**. What the check enforced cannot be violated by a shape that no
longer exists.

🔴 **The leak L5 closed is now an ACCEPTED, DOCUMENTED EXPOSURE, not a solved
problem** — a title alone tells a reader that a document they cannot open
exists. [SR-LAW-5](../../../records/0007_LAW-5-hashed-meta.md) is kept at
`status: superseded` with its reopen trigger and its citation, because a reopen
is cheaper than a rediscovery.


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
from . import recordschema
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


#: Fields that carry text a human can read, **read from the record schema**
#: rather than restated here (W-83b). This tuple and the record's shape used to
#: live in different modules and agreed only by habit.
#:
#: ⚠ **Nothing reads it any more** (W-194): `assert_meta_policy` was its only
#: consumer and every record may now carry every one of these. It is kept
#: because `recordschema.display_fields()` is still the one place that says
#: which fields are human-readable, and a future rule about display text
#: should find it here rather than invent a second list.
DISPLAY_FIELDS = recordschema.display_fields()


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
        out[tracker.hash_of(term)] = trim(tf)
    return out


def trim(tf) -> list[int]:
    """Drop trailing zeros from a tf (or flen) vector.

    **The whole reason `body` is first in `store.TF_FIELDS`.** 92.5 % of
    postings in this repo are body-only, so the common case encodes as `[1]`
    rather than `[1,0,0,0,0]` — measured at **-36.7 %** on the tf vectors in
    the live index, while going from two fields to five.

    A vector of all zeros trims to `[]`, which is correct: it contributes
    nothing to any score, and `weighted_tf` iterates the list rather than the
    weights, so the short form costs nothing to read either.
    """
    out = list(tf)
    while out and out[-1] == 0:
        out.pop()
    return out
