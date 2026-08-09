"""Unit tests for the KL selector.

These travel with the selector when it is ported into `src/fux/ingest/` at M2 —
they are the selector's contract, not the harness's.
"""

from __future__ import annotations

import math

import pytest

from pruning.kl_select import (
    CollectionModel,
    build_collection_model,
    select_top_k,
    term_scores,
)


def test_collection_model_sums_the_unpruned_corpus():
    model = build_collection_model([{"a": 2, "b": 1}, {"a": 1, "c": 3}])
    assert model.total_tokens == 7
    assert model.cf("a") == 3
    assert model.cf("c") == 3
    assert model.cf("missing") == 0
    assert model.p("a") == pytest.approx(3 / 7)


def test_a_term_distributed_exactly_as_the_collection_scores_zero():
    """No discriminative power → no KL contribution → first to be pruned."""
    docs = [{"a": 1, "b": 1}, {"a": 1, "b": 1}, {"a": 1, "b": 1}]
    model = build_collection_model(docs)
    scores = term_scores({"a": 1, "b": 1}, model)
    assert scores["a"] == 0.0
    assert scores["b"] == 0.0


def test_ranking_follows_the_kl_formula_on_a_known_distribution():
    # `rare` is 1/10 of this document but 1/100 of the collection → strongly
    # positive. `common` is under-represented in the document → negative.
    model = build_collection_model([{"common": 89, "rare": 1}] + [{"common": 10}] * 1)
    doc = {"common": 9, "rare": 1}
    scores = term_scores(doc, model)
    assert scores["rare"] > 0 > scores["common"]
    expected = 0.1 * math.log(0.1 / (1 / 100))
    assert scores["rare"] == pytest.approx(expected, abs=1e-9)
    assert select_top_k(doc, model, 1) == ["rare"]


def test_ties_break_lexicographically_and_are_stable():
    model = build_collection_model([{"beta": 1, "alpha": 1, "gamma": 1}])
    doc = {"gamma": 1, "beta": 1, "alpha": 1}  # identical scores by symmetry
    assert select_top_k(doc, model, 2) == ["alpha", "beta"]
    # Insertion order of the document must not affect the outcome.
    reordered = {"beta": 1, "gamma": 1, "alpha": 1}
    assert select_top_k(reordered, model, 3) == select_top_k(doc, model, 3)


def test_k_larger_than_vocabulary_keeps_everything():
    model = build_collection_model([{"a": 1, "b": 2}])
    kept = select_top_k({"a": 1, "b": 2}, model, 99)
    assert sorted(kept) == ["a", "b"]


def test_k_none_is_a_no_op_and_k_zero_keeps_nothing():
    model = build_collection_model([{"a": 1, "b": 2, "c": 3}])
    doc = {"a": 1, "b": 2, "c": 3}
    assert sorted(select_top_k(doc, model, None)) == ["a", "b", "c"]
    assert select_top_k(doc, model, 0) == []


def test_empty_document_selects_nothing():
    model = build_collection_model([{"a": 1}])
    assert select_top_k({}, model, 5) == []
    assert select_top_k({"a": 0}, model, 5) == []


def test_negative_k_is_a_caller_bug():
    model = build_collection_model([{"a": 1}])
    with pytest.raises(ValueError):
        select_top_k({"a": 1}, model, -1)


def test_negative_term_frequency_is_rejected():
    with pytest.raises(ValueError):
        build_collection_model([{"a": -1}])
    model = build_collection_model([{"a": 1}])
    with pytest.raises(ValueError):
        term_scores({"a": -1}, model)


def test_unseen_term_does_not_blow_up_the_log():
    """Defensive: a document scored against a foreign collection model."""
    model = build_collection_model([{"a": 10}])
    scores = term_scores({"zzz": 1}, model)
    assert math.isfinite(scores["zzz"])


def test_selection_is_monotone_in_k():
    """A smaller k must keep a prefix of what a larger k keeps."""
    model = build_collection_model([{"a": 5, "b": 3, "c": 2, "d": 1}, {"a": 1, "e": 9}])
    doc = {"a": 5, "b": 3, "c": 2, "d": 1}
    big = select_top_k(doc, model, 4)
    for k in range(5):
        assert select_top_k(doc, model, k) == big[:k]


def test_empty_collection_model_is_usable():
    model = CollectionModel({}, 0)
    assert math.isfinite(model.p("anything"))
    assert select_top_k({"a": 1}, model, 1) == ["a"]
