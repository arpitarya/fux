from __future__ import annotations

import pytest

from fux.errors import FuxError
from fux.store.collisions import CollisionTracker


def test_distinct_terms_get_distinct_hashes():
    tracker = CollisionTracker()
    assert tracker.hash_of("alpha") != tracker.hash_of("beta")


def test_same_term_reused_is_not_a_collision():
    tracker = CollisionTracker()
    assert tracker.hash_of("alpha") == tracker.hash_of("alpha")


def test_crafted_collision_fails_loudly():
    # Two distinct terms forced to the same digest via an injected hash
    # function — a real 8-byte blake2b collision isn't findable by search.
    def colliding_hash(term: str) -> str:
        return "deadbeefcafebabe"

    tracker = CollisionTracker(hash_fn=colliding_hash)
    tracker.hash_of("alpha")
    with pytest.raises(FuxError, match="term-hash collision"):
        tracker.hash_of("beta")


def test_collision_error_names_both_terms():
    def colliding_hash(term: str) -> str:
        return "deadbeefcafebabe"

    tracker = CollisionTracker(hash_fn=colliding_hash)
    tracker.hash_of("alpha")
    with pytest.raises(FuxError) as exc_info:
        tracker.hash_of("beta")
    assert "alpha" in str(exc_info.value)
    assert "beta" in str(exc_info.value)


def test_shared_tracker_catches_collision_across_two_documents_via_write_index():
    """The end-to-end law, not just the unit: a build using one tracker
    across two documents' postings refuses on a term-hash collision."""
    from fux.store.writer import hash_terms, write_index

    def colliding_hash(term: str) -> str:
        return "deadbeefcafebabe"

    tracker = CollisionTracker(hash_fn=colliding_hash)
    hash_terms({"alpha": (1, 0)}, tracker)  # doc 1's postings
    with pytest.raises(FuxError, match="term-hash collision"):
        hash_terms({"beta": (1, 0)}, tracker)  # doc 2's postings — refused


def test_real_term_hash_produces_distinct_postings_keys_through_hash_terms(tmp_path):
    """With the real hash function and a shared tracker, two documents with
    different vocabularies build cleanly through write_index."""
    from fux.store.writer import hash_terms, write_index

    tracker = CollisionTracker()
    doc1_terms = hash_terms({"pruning": (2, 5), "gate": (1, 3)}, tracker)
    doc2_terms = hash_terms({"index": (1, 1), "format": (0, 4)}, tracker)
    records = [
        {"id": "file:a.md", "src": "git", "loc": "a.md", "mode": "extracted", "terms": doc1_terms},
        {"id": "file:b.md", "src": "git", "loc": "b.md", "mode": "extracted", "terms": doc2_terms},
    ]
    write_index(tmp_path, records)
    from fux.store.reader import read_index

    got = read_index(tmp_path)
    assert got["file:a.md"]["terms"] == doc1_terms
    assert got["file:b.md"]["terms"] == doc2_terms
    # every stored key really is the 16-hex term_hash, not an arbitrary label
    from fux.store.format import term_hash

    assert doc1_terms[term_hash("pruning")] == [2, 5]
