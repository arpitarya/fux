"""Build-time term-hash collision detection — fails loudly (archived ADR-0008
discipline). Two distinct terms sharing an 8-byte blake2b digest would
silently merge their postings; that must never happen quietly.
"""

from __future__ import annotations

from ..errors import FuxError
from .format import term_hash as _default_term_hash


class CollisionTracker:
    """Tracks every term hashed during one ingest run; raises on collision.

    Must be a SINGLE instance shared across the entire run, not one per
    document — a document's own terms are already deduplicated by
    construction, so only cross-document collisions are possible, and a
    fresh tracker per document would never see one.

    `hash_fn` is injectable so tests can craft a collision without needing an
    actual 8-byte digest clash (astronomically unlikely to hit by accident).
    """

    def __init__(self, hash_fn=_default_term_hash) -> None:
        self._hash_fn = hash_fn
        self._seen: dict[str, str] = {}

    def hash_of(self, term: str) -> str:
        digest = self._hash_fn(term)
        prior = self._seen.get(digest)
        if prior is not None and prior != term:
            raise FuxError(
                f"term-hash collision: {prior!r} and {term!r} both hash to {digest} — "
                "build refused (two distinct terms cannot share a postings key)"
            )
        self._seen[digest] = term
        return digest
