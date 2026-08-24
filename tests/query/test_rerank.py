"""W-76 Phase 6 — the proximity reranker.

What is pinned here is mostly the **shape**, not the constants. The weights
came off a measured plateau and will move; the properties below are what makes
the lane safe to have at all, and each one is a way it could silently go wrong:

- it reorders and never retrieves, so the committed plane stays sufficient;
- it shares the index's analyzer, so it cannot disagree about what a term is;
- coverage multiplies, so an incomplete match cannot win on tightness;
- a document it cannot read keeps its score rather than being demoted for
  being unreachable.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from fux.query import rerank
from fux.query.analyzer import analyze


@dataclass(frozen=True)
class FakeResult:
    id: str
    title: str
    loc: str
    score: float
    archived: bool = False


def _r(doc_id, score):
    return FakeResult(id=f"file:{doc_id}", title=doc_id, loc=doc_id, score=score)


def _reader(texts):
    return lambda root, doc_id, loc: texts.get(loc)


# -- the three signals --------------------------------------------------------


def test_adjacent_terms_span_better_than_scattered_ones():
    q = analyze("east west traffic")
    tight = analyze("the east west traffic policy")
    loose = analyze("east " + "filler " * 60 + "west " + "filler " * 60 + "traffic")
    assert rerank.signals(q, tight)[1] > rerank.signals(q, loose)[1]


def test_span_is_one_when_the_terms_are_contiguous():
    q = analyze("east west traffic")
    assert rerank.signals(q, analyze("about east west traffic here"))[1] == pytest.approx(1.0)


def test_coverage_counts_distinct_terms_not_occurrences():
    """The failure BM25F has by construction: it sums per term, so many hits
    on one term can outscore one hit on each of several."""
    q = analyze("retry timeout budget")
    repeated = analyze("retry retry retry retry retry retry")
    spread = analyze("retry timeout budget")
    assert rerank.signals(q, repeated)[0] == pytest.approx(1 / 3)
    assert rerank.signals(q, spread)[0] == pytest.approx(1.0)


def test_adjacency_requires_order_not_just_presence():
    q = analyze("gateway rollback")
    assert rerank.signals(q, analyze("the gateway rollback runbook"))[2] == pytest.approx(1.0)
    assert rerank.signals(q, analyze("the rollback gateway runbook"))[2] == pytest.approx(0.0)


def test_a_single_matched_term_reports_no_proximity():
    """One term is trivially adjacent to nothing and spans only itself.
    Reporting a span here would reward a document for a tightness it never
    demonstrated."""
    coverage, span, adjacency = rerank.signals(analyze("east west"), analyze("east east east"))
    assert coverage == pytest.approx(0.5)
    assert (span, adjacency) == (0.0, 0.0)


def test_nothing_matched_is_zero_not_an_error():
    assert rerank.signals(analyze("east west"), analyze("entirely unrelated prose")) == (0.0, 0.0, 0.0)


# -- combining them -----------------------------------------------------------


def test_a_missing_term_costs_more_than_linearly():
    """`COVERAGE_POWER`. Measured on golden q015: linear coverage prices a
    missing term at 20 % and loses to a superseded document; squared prices it
    at 36 % and wins."""
    q = analyze("current decision east west traffic")
    full = rerank.passage_boost(q, analyze("this is the current decision for east west traffic"))
    partial = rerank.passage_boost(q, analyze("this is the decision for east west traffic"))
    assert full > partial
    assert partial / full < 0.8, "a 4-of-5 match must not keep 80% of its proximity"


def test_a_document_scores_as_its_best_passage_not_its_average():
    """Averaging is how a document that answers the question in one section
    and discusses nine other things loses to a vaguely on-topic one."""
    answers_once = "# Rollback\n\nRun the gateway rollback now.\n\n" + "\n\n".join(
        f"## Aside {i}\n\nUnrelated prose about other matters entirely." for i in range(9)
    )
    q = analyze("gateway rollback")
    assert rerank.boost(q, answers_once) == pytest.approx(1.0)


# -- the reranking itself -----------------------------------------------------


def test_it_reorders_and_never_changes_the_membership():
    results = [_r("a.md", 10.0), _r("b.md", 9.0), _r("c.md", 8.0)]
    texts = {"a.md": "unrelated prose", "b.md": "the gateway rollback procedure", "c.md": "gateway"}
    out = rerank.rerank(None, "gateway rollback", results, weight=1.0, read=_reader(texts))
    assert {r.id for r in out} == {r.id for r in results}, "must not add or drop a document"
    assert len(out) == len(results)


def test_a_strong_proximity_match_can_overtake_a_higher_bm25f_score():
    results = [_r("a.md", 10.0), _r("b.md", 9.0)]
    texts = {"a.md": "gateway " * 40, "b.md": "run the gateway rollback procedure"}
    out = rerank.rerank(None, "gateway rollback", results, weight=1.0, read=_reader(texts))
    assert out[0].loc == "b.md"


def test_a_document_that_cannot_be_read_keeps_its_score():
    """Offline, a `url:` document has no text to rerank against. Demoting it
    for being unreachable would make reachability a ranking signal."""
    results = [_r("a.md", 10.0), _r("b.md", 9.0)]
    out = rerank.rerank(None, "gateway rollback", results, weight=1.0, read=lambda *_: None)
    assert [r.loc for r in out] == ["a.md", "b.md"]
    assert [r.score for r in out] == [10.0, 9.0]


def test_zero_weight_is_exactly_the_input():
    results = [_r("a.md", 10.0), _r("b.md", 9.0)]
    assert rerank.rerank(None, "gateway rollback", results, weight=0.0) == results


def test_a_one_term_query_is_left_alone():
    """Proximity is constant across every candidate for a single term, so
    reranking it is arithmetic that cannot change an order."""
    results = [_r("a.md", 10.0), _r("b.md", 9.0)]
    texts = {"a.md": "gateway", "b.md": "gateway gateway gateway"}
    out = rerank.rerank(None, "gateway", results, weight=1.0, read=_reader(texts))
    assert out == results


def test_beyond_the_depth_nothing_is_touched():
    results = [_r(f"{i:02d}.md", 100.0 - i) for i in range(30)]
    texts = {r.loc: "gateway rollback procedure" for r in results}
    out = rerank.rerank(None, "gateway rollback", results, depth=5, weight=1.0, read=_reader(texts))
    assert [r.loc for r in out[5:]] == [r.loc for r in results[5:]], "the tail keeps its order"
    assert [r.score for r in out[5:]] == [r.score for r in results[5:]], "and its scores"


def test_ties_break_on_id_never_on_input_order():
    """The property the whole output's byte-stability rests on."""
    texts = {"b.md": "gateway rollback", "a.md": "gateway rollback"}
    forward = rerank.rerank(None, "gateway rollback", [_r("b.md", 5.0), _r("a.md", 5.0)],
                            weight=1.0, read=_reader(texts))
    backward = rerank.rerank(None, "gateway rollback", [_r("a.md", 5.0), _r("b.md", 5.0)],
                             weight=1.0, read=_reader(texts))
    assert [r.id for r in forward] == [r.id for r in backward] == ["file:a.md", "file:b.md"]


def test_it_is_deterministic_across_repeated_calls():
    results = [_r(f"{i}.md", 10.0 - i) for i in range(6)]
    texts = {r.loc: f"gateway rollback {r.loc}" for r in results}
    runs = [
        [(r.id, round(r.score, 9))
         for r in rerank.rerank(None, "gateway rollback", results, weight=1.0, read=_reader(texts))]
        for _ in range(5)
    ]
    assert all(run == runs[0] for run in runs)


def test_the_reader_is_injected_never_imported(tmp_path):
    """The `refer/source.py` rule, applied again: the default reads local
    files and declines anything that would need the network."""
    (tmp_path / "a.md").write_text("gateway rollback", encoding="utf-8")
    assert rerank._read_local_text(tmp_path, "file:a.md", "a.md") == "gateway rollback"
    assert rerank._read_local_text(tmp_path, "url:https://example.com", "https://example.com") is None
    assert rerank._read_local_text(tmp_path, "file:gone.md", "gone.md") is None
