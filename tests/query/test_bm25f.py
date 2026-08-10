"""BM25F math — adapted from archive/v0.26/tests/test_bm25f.py's hand-computed
values, ported to the M1 shape: two fields (heading/body), hash-keyed terms.
"""

from __future__ import annotations

import math

from fux.query.bm25f import score_record


def test_single_occurrence_score_is_idf():
    # One doc, term once in body: wlen == avg_wlen, wtf == body_weight(1.0)
    # -> score = idf * wtf*(k1+1)/(wtf + k1*(1-b+b)) = idf (b terms cancel).
    terms = {"h": [0, 1]}
    score = score_record(terms, wlen=10, query_hashes=["h"], df={"h": 1}, n=1, avg_wlen=10)
    assert math.isclose(score, math.log(4 / 3), rel_tol=1e-9)


def test_heading_match_outranks_body_match():
    heading_doc = {"h": [1, 0]}
    body_doc = {"h": [0, 1]}
    a = score_record(heading_doc, wlen=10, query_hashes=["h"], df={"h": 2}, n=2, avg_wlen=10)
    b = score_record(body_doc, wlen=10, query_hashes=["h"], df={"h": 2}, n=2, avg_wlen=10)
    assert a > b


def test_term_frequency_saturates():
    # k1 caps repetition: 10 occurrences must score < 10x one occurrence, but > 1x.
    ten = {"h": [0, 10]}
    one = {"h": [0, 1]}
    df, n, avg_wlen = {"h": 2}, 2, 40
    a = score_record(ten, wlen=40, query_hashes=["h"], df=df, n=n, avg_wlen=avg_wlen)
    b = score_record(one, wlen=40, query_hashes=["h"], df=df, n=n, avg_wlen=avg_wlen)
    assert b < a < b * 10


def test_deterministic():
    terms = {"h": [1, 3]}
    a = score_record(terms, wlen=12, query_hashes=["h"], df={"h": 1}, n=5, avg_wlen=10)
    b = score_record(terms, wlen=12, query_hashes=["h"], df={"h": 1}, n=5, avg_wlen=10)
    assert a == b


def test_missing_term_contributes_nothing():
    assert score_record({}, wlen=10, query_hashes=["h"], df={"h": 1}, n=5, avg_wlen=10) == 0.0


def test_multiple_query_terms_sum():
    terms = {"a": [1, 0], "b": [0, 1]}
    both = score_record(terms, wlen=10, query_hashes=["a", "b"], df={"a": 1, "b": 1}, n=3, avg_wlen=10)
    only_a = score_record(terms, wlen=10, query_hashes=["a"], df={"a": 1}, n=3, avg_wlen=10)
    only_b = score_record(terms, wlen=10, query_hashes=["b"], df={"b": 1}, n=3, avg_wlen=10)
    assert math.isclose(both, only_a + only_b, rel_tol=1e-9)


def test_empty_corpus_is_zero():
    assert score_record({"h": [1, 1]}, wlen=1, query_hashes=["h"], df={"h": 0}, n=0, avg_wlen=0) == 0.0


def test_longer_doc_scores_lower_for_same_tf():
    terms = {"h": [0, 1]}
    short = score_record(terms, wlen=10, query_hashes=["h"], df={"h": 1}, n=2, avg_wlen=10)
    long_doc = score_record(terms, wlen=100, query_hashes=["h"], df={"h": 1}, n=2, avg_wlen=10)
    assert long_doc < short
