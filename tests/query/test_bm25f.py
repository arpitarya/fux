"""BM25F math — adapted from archive/v0.26/tests/test_bm25f.py's hand-computed
values, ported to the M1 shape (two fields, hash-keyed terms) and then to the
W-76 Phase 1 shape: five fields in `[body, heading, title, path, ctx]` order
(`store.TF_FIELDS`), and `score_record`'s second argument renamed `wlen` ->
`flen`. Every `flen=` here is a bare int, which `score_record` accepts as an
already-derived wlen (its own docstring) — the honest translation of a test
that is about the scoring arithmetic, not about how a real `flen` list
derives it.
"""

from __future__ import annotations

import math

from fux.query.bm25f import score_record


def test_single_occurrence_score_is_idf():
    # One doc, term once in body: wlen == avg_wlen, wtf == the body weight (1.0)
    # -> score = idf * wtf*(k1+1)/(wtf + k1*(1-b+b)) = idf (b terms cancel).
    terms = {"h": [1, 0]}
    score = score_record(terms, flen=10, query_hashes=["h"], df={"h": 1}, n=1, avg_wlen=10)
    assert math.isclose(score, math.log(4 / 3), rel_tol=1e-9)


def test_heading_match_outranks_body_match():
    heading_doc = {"h": [0, 1]}
    body_doc = {"h": [1, 0]}
    a = score_record(heading_doc, flen=10, query_hashes=["h"], df={"h": 2}, n=2, avg_wlen=10)
    b = score_record(body_doc, flen=10, query_hashes=["h"], df={"h": 2}, n=2, avg_wlen=10)
    assert a > b


def test_term_frequency_saturates():
    # k1 caps repetition: 10 occurrences must score < 10x one occurrence, but > 1x.
    ten = {"h": [10, 0]}
    one = {"h": [1, 0]}
    df, n, avg_wlen = {"h": 2}, 2, 40
    a = score_record(ten, flen=40, query_hashes=["h"], df=df, n=n, avg_wlen=avg_wlen)
    b = score_record(one, flen=40, query_hashes=["h"], df=df, n=n, avg_wlen=avg_wlen)
    assert b < a < b * 10


def test_deterministic():
    terms = {"h": [3, 1]}
    a = score_record(terms, flen=12, query_hashes=["h"], df={"h": 1}, n=5, avg_wlen=10)
    b = score_record(terms, flen=12, query_hashes=["h"], df={"h": 1}, n=5, avg_wlen=10)
    assert a == b


def test_missing_term_contributes_nothing():
    assert score_record({}, flen=10, query_hashes=["h"], df={"h": 1}, n=5, avg_wlen=10) == 0.0


def test_multiple_query_terms_sum():
    terms = {"a": [0, 1], "b": [1, 0]}
    both = score_record(terms, flen=10, query_hashes=["a", "b"], df={"a": 1, "b": 1}, n=3, avg_wlen=10)
    only_a = score_record(terms, flen=10, query_hashes=["a"], df={"a": 1}, n=3, avg_wlen=10)
    only_b = score_record(terms, flen=10, query_hashes=["b"], df={"b": 1}, n=3, avg_wlen=10)
    assert math.isclose(both, only_a + only_b, rel_tol=1e-9)


def test_empty_corpus_is_zero():
    assert score_record({"h": [1, 1]}, flen=1, query_hashes=["h"], df={"h": 0}, n=0, avg_wlen=0) == 0.0


def test_longer_doc_scores_lower_for_same_tf():
    terms = {"h": [1, 0]}
    short = score_record(terms, flen=10, query_hashes=["h"], df={"h": 1}, n=2, avg_wlen=10)
    long_doc = score_record(terms, flen=100, query_hashes=["h"], df={"h": 1}, n=2, avg_wlen=10)
    assert long_doc < short
