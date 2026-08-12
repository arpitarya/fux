"""RRF — ported from `archive/v0.26/tests/test_hybrid.py` and
`archive/v0.26/tests/test_supersession_penalty.py`, per port-don't-rewrite.

The four `offsets` tests come forward even though nothing in this build passes
`offsets` yet: they pin the *calibrated* arithmetic of archived ADR-0015, and
re-deriving it later from prose would be re-doing measurement already paid for.
"""

from __future__ import annotations

import pytest

from fux.query.fuse import RRF_K, rrf


def test_rrf_math():
    """The literature formula, unchanged from the archived engine."""
    assert rrf([["a", "b"], ["a", "b"]], k=60) == {
        "a": pytest.approx(2 / 61),
        "b": pytest.approx(2 / 62),
    }
    fused = rrf([["a", "b"], ["b"]], k=60)
    assert fused["b"] == pytest.approx(1 / 62 + 1 / 61)
    assert fused["a"] == pytest.approx(1 / 61)


def test_default_k_is_the_literature_value():
    """60, per Cormack et al. 2009 — not a tuned knob."""
    assert RRF_K == 60
    assert rrf([["a"]]) == rrf([["a"]], k=60)


def test_rrf_without_offsets_is_untouched():
    lists = [["a", "b", "c"], ["c", "a"]]
    assert rrf(lists, k=60) == rrf(lists, k=60, offsets=None)
    assert rrf(lists, k=60) == rrf(lists, k=60, offsets={})


def test_rrf_zero_offset_equals_no_offset():
    """0 is exact identity, not an approximation of it."""
    lists = [["a", "b", "c"], ["c", "a"]]
    assert rrf(lists, k=60, offsets={"a": 0, "b": 0}) == rrf(lists, k=60)


def test_rrf_offset_demotes_only_the_named_item():
    lists = [["a", "b"]]
    base = rrf(lists, k=60)
    penalised = rrf(lists, k=60, offsets={"a": 5})
    assert penalised["a"] < base["a"]
    assert penalised["b"] == base["b"]
    assert penalised["a"] == pytest.approx(1.0 / (60 + 1 + 5))


def test_rrf_penalty_demotes_but_never_removes():
    """A rank penalty, not a filter — a question genuinely *about* the retired
    decision can still reach it."""
    penalised = rrf([["a", "b"]], k=60, offsets={"a": 10_000})
    assert penalised["a"] > 0.0


def test_an_item_absent_from_every_ranking_scores_nothing():
    assert "z" not in rrf([["a"], ["b"]])


def test_empty_rankings_fuse_to_nothing():
    assert rrf([]) == {}
    assert rrf([[], []]) == {}
