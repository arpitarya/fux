"""The dense lane, and the gated fusion built on it (`query/dense.py`).

The invariant that matters here is a *negative* one: **turning hybrid on must
be the only way to change `ask`'s answer.** The lexical default is what the
differential law protects, and a dense lane that leaked into it would void
every byte-identity claim in this milestone.
"""

from __future__ import annotations

import base64
import json

import pytest

from fux.errors import FuxError

from fux.derive import accel, build, dense
from fux.derive import format as fmt
from fux.query import scan
from fux.store import term_hash, write_index


def _code(bits: int) -> str:
    return base64.urlsafe_b64encode(bits.to_bytes(32, "little")).rstrip(b"=").decode("ascii")


def _chunk(*components: int) -> str:
    """One chunk vector, base64url-encoded int8 components.

    Mirrors `fux.embed.chunkvec.encode` byte-for-byte (raw = each component
    masked to a byte), built directly here rather than through a `Vec` since
    these tests only need the encoded bytes to round-trip through
    `chunkvec.decode` -> `chunkvec.sign_code`, not a real embedding.
    """
    raw = bytes((c & 0xFF) for c in components)
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _rec(doc_id, title, flen, terms, vectors=None) -> dict:
    record = {
        "id": doc_id,
        "src": "git",
        "loc": doc_id.removeprefix("file:"),
        "mode": "extracted",
        "meta": "plain",
        "title": title,
        "phrases": [],
        "terms": terms,
        "flen": flen,
        "edges": [],
    }
    if vectors is not None:
        record["vectors"] = vectors
    return record


@pytest.fixture
def corpus(tmp_path):
    # tf vectors are `[body, heading]` (v2 order — `store.TF_FIELDS`); each
    # `flen` is a single body-token count.
    #
    # Each doc's chunk vector is chosen so its sign code (bit i set iff
    # component i > 0) lands on a small, easy-to-reason-about int: doc a's
    # single chunk sign-codes to 0b0001, b's to 0b0011, c's to 0b1111. Doc d
    # carries no `vectors` at all — the "nothing embeddable" case.
    records = [
        _rec("file:a.md", "A", [20], {term_hash("alpha"): [2, 1]}, [_chunk(1, -1, -1, -1)]),
        _rec("file:b.md", "B", [30], {term_hash("alpha"): [1, 0]}, [_chunk(1, 1, -1, -1)]),
        _rec("file:c.md", "C", [40], {term_hash("beta"): [1, 1]}, [_chunk(1, 1, 1, 1)]),
        _rec("file:d.md", "D", [50], {term_hash("beta"): [1, 0]}),  # no vectors at all
    ]
    write_index(tmp_path, records)
    build(tmp_path)
    return tmp_path


def test_codes_load_docidx_ordered_with_none_for_unembeddable(corpus):
    """W-76 Phase 7 made the sentinel `[]` (a list per document, one code per
    chunk) rather than `None` (one code per document) — `load_codes` now
    mirrors the per-chunk `vectors` field it derives from."""
    codes = dense.load_codes(corpus)
    assert len(codes) == 4
    assert codes[3] == []  # file:d.md, sorted last by id — unembeddable
    assert codes[0] == [0b0001]


def test_unembeddable_documents_are_never_ranked_by_the_dense_lane(corpus):
    """A doc with no codes (`[]`) must be skipped, not treated as an all-zero vector.

    An all-zero code sits at a misleading middle distance from every query,
    which would make documents with nothing embeddable quietly rankable.

    Before W-76 Phase 7 this intent lived on `hamming_ranking`, over a flat
    `list[int | None]`. `load_codes` now returns a per-chunk `list[list[int]]`
    (`hamming_ranking` would raise `TypeError` trying to XOR an `int` against
    a `list`), so `nearest_docs` — which ranks a document by its BEST chunk
    and skips any document with no chunk codes at all — is what actually
    carries this invariant now.
    """
    codes = dense.load_codes(corpus)
    ranking = dense.nearest_docs(0, codes, limit=10)
    assert 3 not in ranking
    assert len(ranking) == 3


def test_hamming_ranking_is_nearest_first_and_tie_breaks_on_docidx():
    """`hamming_ranking` is unchanged by W-76 Phase 7 — it still ranks a flat
    per-document code list (`list[int | None]`), not the per-chunk table
    `load_codes` now returns (`list[list[int]]`). Exercised here with an
    explicit flat code list instead of the `corpus` fixture, since
    `load_codes`'s output no longer has the shape this function expects.
    """
    assert dense.hamming_ranking(0b0001, [0b0001, 0b0011, 0b1111], width=3) == [0, 1, 2]
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


def test_dense_lane_is_empty_without_a_code_table(tmp_path):
    write_index(tmp_path, [_rec("file:a.md", "A", [10], {term_hash("alpha"): [0, 1]})])
    assert dense.load_codes(tmp_path) == []


def test_ask_hybrid_exits_zero_on_a_source_install(corpus, monkeypatch, capsys):
    """The user-visible half of W-46: a traceback must never reach the user.

    W-76 Phase 7 gave `--hybrid` a lane again, over the committed per-chunk
    vectors, fused via `fux.query.dense`. On a source install with no bundled
    model, `query_vector` returns `None`, so `dense_scores` returns `{}` and
    fusion is a no-op — `ask --hybrid` must degrade to the plain lexical
    answer and exit 0, the same graceful behaviour W-46 established, not the
    loud `FuxError` this asserted in the gap between Phase 1 (which removed
    the old lane) and Phase 7 (which brought the lane back).
    """
    import argparse

    import fux.embed as embed_mod
    from fux.query import cmd_ask

    monkeypatch.setattr(embed_mod, "get_model", lambda: None)
    monkeypatch.setattr("fux.query.find_root", lambda: corpus)

    args = argparse.Namespace(
        query="alpha", top=5, json=False, scan=False, explain=False, hybrid=True
    )
    assert cmd_ask(args) == 0
    assert "Traceback" not in capsys.readouterr().out
