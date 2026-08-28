"""The byte budget — and the two biases it exists to correct."""

from __future__ import annotations

import pytest

from fux.refer._assemble import CITATION_OVERHEAD, PER_DOC_FRACTION, assemble
from fux.refer._chunk import Passage
from fux.refer._rescore import ScoredPassage


def sp(doc: str, ordinal: int, nbytes: int, score: float, sha: str = "sha") -> ScoredPassage:
    return ScoredPassage(
        doc_id=f"file:{doc}",
        loc=doc,
        sha=sha,
        passage=Passage(heading="h", text="x" * nbytes, ordinal=ordinal),
        score=score,
    )


def test_the_budget_is_never_exceeded():
    scored = [sp(f"{i}.md", 0, 200, 5.0) for i in range(20)]
    result = assemble(scored, budget=1000)
    assert result.used <= 1000


def test_overhead_is_charged_before_any_citation():
    """The budget bounds the *rendered* answer, not just the payload."""
    scored = [sp("a.md", 0, 100, 5.0)]
    plain = assemble(scored, budget=1000)
    with_overhead = assemble(scored, budget=1000, overhead=400)
    assert with_overhead.used == plain.used + 400


def test_the_best_answer_is_not_crowded_out_by_cheaper_fragments():
    """The floor, and the reason it exists.

    Greedy score-per-byte is systematically biased toward short passages: a
    50-byte passage scoring 3 is 0.060/byte, a 400-byte passage scoring 8 is
    0.020/byte. Without seating the best answer first, the cheap fragment is
    taken and the passage that actually answers the question no longer fits.
    """
    cheap = sp("short.md", 0, 50, 3.0)
    real = sp("long.md", 0, 400, 8.0)
    # A budget that fits either one alone, but not both.
    budget = real.nbytes + CITATION_OVERHEAD + 20

    result = assemble([cheap, real], budget=budget)
    assert [c.locator for c in result.citations] == ["long.md#p0"]


def test_a_document_is_never_silenced_by_the_per_document_cap():
    """The cap stops a document dominating, not appearing.

    A cap that blocks a document's *first* citation excludes the best answer at
    small budgets for a reason the caller never asked for.
    """
    big = sp("a.md", 0, 300, 9.0)
    budget = 600  # per-doc cap is 300 here, and the citation is 380 with overhead
    assert big.nbytes + CITATION_OVERHEAD > budget * PER_DOC_FRACTION

    result = assemble([big], budget=budget)
    assert [c.locator for c in result.citations] == ["a.md#p0"]


def test_one_document_cannot_consume_the_whole_budget():
    """...but its second, third and fourth citations are capped."""
    scored = [sp("hog.md", i, 200, 9.0 - i * 0.1) for i in range(10)]
    scored.append(sp("other.md", 0, 200, 1.0))
    result = assemble(scored, budget=2000)

    hog_bytes = sum(c.nbytes for c in result.citations if c.doc_id == "file:hog.md")
    assert hog_bytes <= 2000 * PER_DOC_FRACTION + 200 + CITATION_OVERHEAD
    assert any(c.doc_id == "file:other.md" for c in result.citations)


def test_selection_skips_rather_than_stops():
    """A large passage that does not fit must not end the assembly — a smaller
    one further down may still fit, and stopping wastes the caller's window."""
    huge = sp("huge.md", 0, 5000, 9.0)
    small = sp("small.md", 0, 100, 8.0)
    result = assemble([huge, small], budget=1000)
    assert [c.locator for c in result.citations] == ["small.md#p0"]
    assert result.dropped == 1


def test_ties_break_deterministically_not_on_iteration_order():
    """Same corpus, same budget, same bytes — the whole promise."""
    scored = [sp(f"{c}.md", 0, 100, 5.0, sha=f"sha{c}") for c in "zyxwv"]
    baseline = [c.locator for c in assemble(scored, budget=10_000).citations]
    for rotation in range(1, len(scored)):
        rotated = scored[rotation:] + scored[:rotation]
        assert [c.locator for c in assemble(rotated, budget=10_000).citations] == baseline


def test_k_is_a_secondary_cap_not_the_primary_limit():
    scored = [sp(f"{i}.md", 0, 50, 10.0 - i) for i in range(10)]  # all > 0
    assert len(assemble(scored, budget=10_000).citations) == 10
    assert len(assemble(scored, budget=10_000, k=3).citations) == 3


def test_zero_scoring_passages_are_never_cited():
    """A passage that does not match the query is not an answer to it."""
    result = assemble([sp("a.md", 0, 100, 0.0)], budget=1000)
    assert result.citations == []


def test_citations_are_presented_best_first_even_though_selection_was_greedy():
    scored = [sp("a.md", 0, 400, 9.0), sp("b.md", 0, 50, 3.0)]
    result = assemble(scored, budget=10_000)
    assert [c.score for c in result.citations] == sorted(
        (c.score for c in result.citations), reverse=True
    )


def test_dropped_is_reported_so_truncation_is_never_silent():
    scored = [sp(f"{i}.md", 0, 900, 9.0) for i in range(5)]
    result = assemble(scored, budget=1000)
    assert result.dropped > 0


def test_a_nonpositive_budget_is_refused():
    with pytest.raises(ValueError):
        assemble([], budget=0)


# -- W-72: the per-document cap and the single-candidate shape -----------------


def test_one_document_may_use_the_whole_budget():
    """W-72, and the shape `fux answer` actually ships.

    `query/refer_answer.py` passes `refer()` exactly one candidate document, so
    the per-document cap was discarding up to half the caller's budget to stop a
    document dominating a field of one. Measured before the fix: the greedy
    assembler lost to plain top-k by up to 35.5% at 500-2000 byte budgets.

    Five 200-byte passages from one document, against a budget that fits four of
    them. Under the old cap only two could be seated (1000 * 0.5 = 500 bytes,
    minus the first-citation exemption); now the budget is the only bound.
    """
    scored = [sp("only.md", i, 200, 10.0 - i) for i in range(5)]
    budget = 4 * (200 + CITATION_OVERHEAD)
    result = assemble(scored, budget=budget)

    assert len(result.citations) == 4, (
        f"one document should be bounded by the budget alone, seated "
        f"{len(result.citations)} of a possible 4"
    )
    assert result.used <= budget
    assert {c.doc_id for c in result.citations} == {"file:only.md"}


def test_the_cap_still_binds_the_moment_a_second_document_competes():
    """The fix is scoped, not a removal.

    The same passages plus one from a second document: the cap is live again,
    because now there is something to protect. Without this assertion W-72's fix
    reads as "the cap was wrong" rather than "the cap did not apply".
    """
    scored = [sp("big.md", i, 200, 10.0 - i) for i in range(5)]
    scored.append(sp("other.md", 0, 200, 1.0))
    budget = 4 * (200 + CITATION_OVERHEAD)

    result = assemble(scored, budget=budget)
    from_big = sum(c.nbytes for c in result.citations if c.doc_id == "file:big.md")
    assert from_big <= int(budget * PER_DOC_FRACTION) + 200 + CITATION_OVERHEAD, (
        "with a competitor present the per-document cap must still bind "
        "(allowing the first-citation exemption)"
    )


def test_the_single_document_case_is_keyed_on_candidates_not_on_k():
    """A caller that asks for one document gets the un-capped behaviour whether
    or not it also passes `k` — the exemption is a property of the candidate
    set, so it cannot be switched on by an unrelated argument."""
    scored = [sp("only.md", i, 200, 10.0 - i) for i in range(4)]
    budget = 4 * (200 + CITATION_OVERHEAD)
    assert len(assemble(scored, budget=budget).citations) == 4
    assert len(assemble(scored, budget=budget, k=2).citations) == 2
