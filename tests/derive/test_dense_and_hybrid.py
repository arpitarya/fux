"""The dense lane and the hybrid fusion built on it.

The invariant that matters here is a *negative* one: **turning hybrid on must
be the only way to change `ask`'s answer.** The lexical default is what the
differential law protects, and a dense lane that leaked into it would void
every byte-identity claim in this milestone.
"""

from __future__ import annotations

import base64
import json

import pytest

from fux.derive import accel, build, dense
from fux.derive import format as fmt
from fux.query import scan
from fux.query.hybrid import hybrid_ask
from fux.store import term_hash, write_index


def _code(bits: int) -> str:
    return base64.urlsafe_b64encode(bits.to_bytes(32, "little")).rstrip(b"=").decode("ascii")


def _rec(doc_id, title, wlen, terms, code=None) -> dict:
    record = {
        "id": doc_id,
        "src": "git",
        "loc": doc_id.removeprefix("file:"),
        "mode": "extracted",
        "meta": "plain",
        "title": title,
        "phrases": [],
        "terms": terms,
        "wlen": wlen,
        "edges": [],
    }
    if code is not None:
        record["code"] = code
    return record


@pytest.fixture
def corpus(tmp_path):
    records = [
        _rec("file:a.md", "A", 20, {term_hash("alpha"): [1, 2]}, _code(0b0001)),
        _rec("file:b.md", "B", 30, {term_hash("alpha"): [0, 1]}, _code(0b0011)),
        _rec("file:c.md", "C", 40, {term_hash("beta"): [1, 1]}, _code(0b1111)),
        _rec("file:d.md", "D", 50, {term_hash("beta"): [0, 1]}),  # no code at all
    ]
    write_index(tmp_path, records)
    build(tmp_path)
    return tmp_path


def test_codes_load_docidx_ordered_with_none_for_unembeddable(corpus):
    codes = dense.load_codes(corpus)
    assert len(codes) == 4
    assert codes[3] is None  # file:d.md, sorted last by id
    assert codes[0] == 0b0001


def test_unembeddable_documents_are_never_ranked_by_the_dense_lane(corpus):
    """A `None` code must be skipped, not treated as an all-zero vector.

    An all-zero code sits at a misleading middle distance from every query,
    which would make documents with nothing embeddable quietly rankable.
    """
    codes = dense.load_codes(corpus)
    ranking = dense.hamming_ranking(0, codes, width=10)
    assert 3 not in ranking
    assert len(ranking) == 3


def test_hamming_ranking_is_nearest_first_and_tie_breaks_on_docidx(corpus):
    codes = dense.load_codes(corpus)
    assert dense.hamming_ranking(0b0001, codes, width=3) == [0, 1, 2]
    # Equidistant codes must order by docidx, not by dict iteration.
    assert dense.hamming_ranking(0b0000, [0b1, 0b10, 0b100], width=3) == [0, 1, 2]


def test_code_table_is_part_of_the_deterministic_build(corpus):
    assert dense.CODES_NAME in fmt.DETERMINISTIC_FILES
    before = (fmt.runtime_dir(corpus) / dense.CODES_NAME).read_bytes()
    build(corpus)
    assert (fmt.runtime_dir(corpus) / dense.CODES_NAME).read_bytes() == before


def test_hybrid_does_not_leak_into_the_default_path(corpus):
    """The load-bearing negative: `ask` is lexical unless asked otherwise."""
    assert accel.ask(corpus, "alpha", top=5) == scan.ask(corpus, "alpha", top=5)


def test_hybrid_returns_rrf_scores_not_bm25f_scores(corpus, monkeypatch):
    monkeypatch.setattr("fux.query.hybrid._dense_ids", lambda root, query: ["file:c.md"])
    fused = hybrid_ask(corpus, "alpha", top=5)
    assert fused
    # RRF scores live near 1/(k+rank); BM25F scores on this fixture are >1.
    assert all(r.score < 0.1 for r in fused)


def test_hybrid_can_surface_a_document_the_lexical_lane_never_saw(corpus, monkeypatch):
    """A dense-only hit still needs a title and a loc, from the doc table."""
    monkeypatch.setattr("fux.query.hybrid._dense_ids", lambda root, query: ["file:c.md"])
    ids = [r.id for r in hybrid_ask(corpus, "alpha", top=5)]
    assert "file:c.md" in ids
    hit = next(r for r in hybrid_ask(corpus, "alpha", top=5) if r.id == "file:c.md")
    assert hit.loc == "c.md" and hit.title == "C"


def test_hybrid_degrades_to_lexical_when_the_dense_lane_is_unavailable(corpus, monkeypatch):
    monkeypatch.setattr("fux.query.hybrid._dense_ids", lambda root, query: [])
    fused = [r.id for r in hybrid_ask(corpus, "alpha", top=5)]
    lexical = [r.id for r in scan.ask(corpus, "alpha", top=5)]
    assert fused == lexical


def test_dense_lane_is_empty_without_a_code_table(tmp_path):
    write_index(tmp_path, [_rec("file:a.md", "A", 10, {term_hash("alpha"): [1, 0]})])
    assert dense.load_codes(tmp_path) == []


def test_a_real_dense_lane_bug_is_not_swallowed(corpus, monkeypatch):
    """The narrow `except` clause, asserted.

    A bare `except Exception` would turn every dense-lane defect into "hybrid
    quietly returns the lexical answer" — a silent degradation that looks like
    a working feature.
    """
    def boom(*args, **kwargs):
        raise RuntimeError("dense lane is broken")

    monkeypatch.setattr("fux.derive.dense.load_codes", boom)
    with pytest.raises(RuntimeError, match="dense lane is broken"):
        hybrid_ask(corpus, "alpha", top=5)
