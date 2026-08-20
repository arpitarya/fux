"""The canonical writer: records in, deterministic shard files out.

## L5 is enforced here, at write time, and that placement is the point

**Hashed meta is the default for non-git sources, enforced at write time**
(L5). Until M5 that enforcement lived in `ingest/run.py`, which is to say it
lived in *one caller* — so it was a convention that happened to hold rather
than a property of the index. Any second writer (an enrichment pass, a
migration script, a test fixture, a consumer using the library) could write a
record carrying a private document's title into a committed file, and nothing
would have said no.

It closes an **ACL-mismatch leak**: a document readable by fifty people inside
Confluence becomes a title readable by everyone with the repo. That is why L5
is a law rather than a configuration preference, and why the check is here
rather than in the path that happens to be used today.

The rule, in full:

- A `git` record may say what it likes; the repo already holds its bytes.
- A **non-git** record must state `meta` explicitly. A missing value means
  something bypassed the resolution layer, and guessing on its behalf is
  exactly the failure this prevents.
- `meta: "hashed"` must carry **no display text** — no `title`, no `phrases` —
  and must carry `title_h`.
- `meta: "plain"` is legal and is an explicit, per-document opt-out
  (ADR-URL-LIST decision 10). It has to be *said*.


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
        assert_meta_policy(record)
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


#: Fields that carry text a human can read. A `hashed` record may hold none of
#: them: the whole point is that the index reveals nothing the source system
#: would not have shown this reader.
DISPLAY_FIELDS = ("title", "phrases")


def assert_meta_policy(record: dict) -> None:
    """Refuse to write a non-git record that leaks display text (L5).

    Raises `FuxError` naming the document and the fix. Called per record by
    `write_index`, so **there is no path into a committed shard that skips
    it** — which is the difference between a law and a habit.
    """
    if record.get("src") == "git":
        return

    doc_id = record.get("id", "<no id>")
    meta = record.get("meta")
    if meta is None:
        raise FuxError(
            f"{doc_id}: a non-git record must state `meta` explicitly. Its absence means the "
            "policy layer was bypassed, and the default (`hashed`, L5) is not applied here on "
            "purpose — guessing on a caller's behalf is the leak this check exists to stop"
        )
    if meta not in ("plain", "hashed"):
        raise FuxError(f"{doc_id}: meta must be 'plain' or 'hashed', got {meta!r}")

    if meta == "hashed":
        leaked = [f for f in DISPLAY_FIELDS if f in record]
        if leaked:
            raise FuxError(
                f"{doc_id}: meta is 'hashed' but the record carries {', '.join(leaked)}. "
                "A hashed record holds `title_h` and no readable text — this is the "
                "ACL-mismatch leak L5 exists to close. Either drop the field, or declare "
                "`meta=plain` on that source line if the document really is public"
            )
        if "title_h" not in record:
            raise FuxError(
                f"{doc_id}: meta is 'hashed' but there is no `title_h`. A record with neither "
                "a title nor a title hash cannot be cited by any verb"
            )


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
