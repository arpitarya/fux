"""Heading-aware chunking — total, deterministic, and never written down."""

from __future__ import annotations

from fux.refer._chunk import MAX_PASSAGE_BYTES, MIN_PASSAGE_BYTES, chunk


def _body(word: str, n: int = 40) -> str:
    return (word + " ") * n


def test_sections_split_on_headings():
    doc = f"# A\n\n{_body('alpha')}\n\n## B\n\n{_body('beta')}"
    passages = chunk(doc)
    assert [p.heading for p in passages] == ["A", "B"]


def test_ordinals_are_document_order_from_zero():
    doc = f"# A\n\n{_body('alpha')}\n\n## B\n\n{_body('beta')}\n\n## C\n\n{_body('gamma')}"
    assert [p.ordinal for p in chunk(doc)] == [0, 1, 2]


def test_a_preamble_before_the_first_heading_is_not_dropped():
    """Content above the first heading is content. Dropping it silently is how
    the one sentence that answers the question disappears."""
    doc = f"{_body('preamble')}\n\n# A\n\n{_body('alpha')}"
    passages = chunk(doc)
    assert any("preamble" in p.text for p in passages)


def test_every_byte_of_input_lands_in_some_passage():
    doc = f"# A\n\n{_body('alpha')}\n\n## B\n\n{_body('beta')}"
    joined = "".join(p.text for p in chunk(doc))
    for word in ("alpha", "beta"):
        assert joined.count(word) == doc.count(word)


def test_a_runt_section_is_folded_rather_than_cited_alone():
    """A two-line passage is a citation nobody can read in isolation."""
    doc = f"# A\n\nshort.\n\n## B\n\n{_body('beta')}"
    passages = chunk(doc)
    assert len(passages) == 1
    assert "short." in passages[0].text and "beta" in passages[0].text


def test_an_oversized_section_splits_on_paragraph_boundaries():
    paragraphs = "\n\n".join(_body("word", 60) for _ in range(20))
    passages = chunk(f"# Big\n\n{paragraphs}")
    assert len(passages) > 1
    for p in passages:
        assert p.nbytes <= MAX_PASSAGE_BYTES * 1.5  # a whole paragraph is never split


def test_chunking_is_deterministic():
    doc = f"# A\n\n{_body('alpha')}\n\n## B\n\n{_body('beta')}"
    assert [(p.heading, p.text, p.ordinal) for p in chunk(doc)] == [
        (p.heading, p.text, p.ordinal) for p in chunk(doc)
    ]


def test_an_empty_document_yields_no_passages():
    assert chunk("") == []
    assert chunk("\n\n   \n") == []


def test_the_thresholds_are_ordered_sensibly():
    assert 0 < MIN_PASSAGE_BYTES < MAX_PASSAGE_BYTES
