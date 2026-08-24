"""W-76 Phase 5 — line-range citations, and the property that makes them safe.

The citation format moved from `path#p3` to `path:L12-L40` because an agent
acts on a citation by **opening a file at a line**, and an ordinal forced a
second call to discover which lines those were.

**The gate is a round-trip, not a format check.** A citation that renders
beautifully and points at the wrong lines is worse than the ordinal it
replaced: the ordinal was at least honestly opaque. So the central test slices
the ORIGINAL document at the cited range and asserts it recovers the passage's
own text — for every passage, through every stage of the chunker (heading
split, runt merge, oversized split), including the fold-back path that has no
following section to merge into.
"""

from __future__ import annotations

import pytest

from fux.refer.chunk import MAX_PASSAGE_BYTES, MIN_PASSAGE_BYTES, chunk


def _assert_every_passage_round_trips(doc: str) -> list:
    lines = doc.splitlines()
    passages = chunk(doc)
    assert passages, "fixture produced no passages"
    for p in passages:
        assert p.line_start >= 1, f"line_start must be 1-based, got {p.line_start}"
        assert p.line_end >= p.line_start, f"inverted range L{p.line_start}-L{p.line_end}"
        assert p.line_end <= len(lines), f"L{p.line_end} is past the end of a {len(lines)}-line document"
        sliced = "\n".join(lines[p.line_start - 1 : p.line_end])
        assert p.text.strip() == sliced.strip(), (
            f"passage {p.ordinal} cites L{p.line_start}-L{p.line_end}, which is not its own text"
        )
    return passages


def test_plain_sections_round_trip():
    doc = "\n".join(
        f"## Section {i}\n\n" + ("word%d " % i) * 90 + "\n" for i in range(1, 6)
    )
    passages = _assert_every_passage_round_trips(doc)
    assert len(passages) == 5, "one passage per heading was expected here"


def test_a_preamble_before_the_first_heading_round_trips():
    """Text before the first heading is its own passage and must still cite."""
    doc = "Some preamble that is long enough to stand alone. " * 8 + "\n\n## After\n\n" + "body " * 90
    _assert_every_passage_round_trips(doc)


def test_merged_runts_span_from_the_first_fragment_to_the_last():
    """A merge is contiguous in the source, so its range is a real range.

    `_merge_runts` folds a too-short section FORWARD into the next one. The
    resulting passage must cite from the stub heading's line through the end
    of the section it merged into — not just the larger half.
    """
    doc = "## Stub\n\n## Real\n\n" + ("content " * 120)
    passages = _assert_every_passage_round_trips(doc)
    first = passages[0]
    assert first.line_start == 1, "the merged passage must start at the stub it folded from"


def test_the_fold_back_path_round_trips():
    """The branch with nothing left to fold forward INTO.

    A trailing runt is folded backward into the previous passage instead of
    being dropped. That path computes its end line differently from every
    other one, so it gets its own test.
    """
    doc = "## Real\n\n" + ("content " * 120) + "\n\n## Trailing stub\n"
    _assert_every_passage_round_trips(doc)


def test_oversized_sections_split_into_distinct_ranges():
    """The third stage. Pieces must not all claim the section's first line."""
    para = "paragraph text here " * 40
    doc = "## Big\n\n" + "\n\n".join([para] * 12)
    passages = _assert_every_passage_round_trips(doc)
    assert len(passages) > 1, "fixture did not actually oversize — nothing under test"
    starts = [p.line_start for p in passages]
    assert starts == sorted(starts), "ranges must advance through the document"
    assert len(set(starts)) == len(starts), "two pieces claimed the same starting line"


def test_identical_paragraphs_get_different_ranges():
    """The reason offsets are walked rather than searched for.

    Two identical paragraphs in one section would make a `str.find` return the
    first one for both, citing the wrong lines for the second.
    """
    para = "exactly the same words repeated " * 40
    doc = "## Same\n\n" + "\n\n".join([para] * 10)
    passages = _assert_every_passage_round_trips(doc)
    if len(passages) > 1:
        assert passages[0].line_start != passages[1].line_start


def test_the_locator_renders_a_line_range():
    from fux.refer.chunk import Passage
    from fux.refer.rescore import ScoredPassage

    p = Passage(heading="H", text="t", ordinal=3, line_start=12, line_end=40)
    s = ScoredPassage(doc_id="file:a.md", loc="docs/a.md", sha="abc", passage=p, score=1.0)
    assert s.locator == "docs/a.md:L12-L40"


def test_the_locator_falls_back_to_the_ordinal_without_a_range():
    """A wrong line number is worse than an honest ordinal.

    A passage built by something other than the chunker carries no range, and
    inventing one would produce a citation that looks actionable and is not.
    """
    from fux.refer.chunk import Passage
    from fux.refer.rescore import ScoredPassage

    p = Passage(heading="H", text="t", ordinal=3)
    s = ScoredPassage(doc_id="file:a.md", loc="docs/a.md", sha="abc", passage=p, score=1.0)
    assert s.locator == "docs/a.md#p3"


def test_the_ordinal_survives_alongside_the_range():
    """Kept deliberately: it is stable across a reflow that moves every line."""
    doc = "## A\n\n" + ("x " * 90) + "\n\n## B\n\n" + ("y " * 90)
    for i, p in enumerate(chunk(doc)):
        assert p.ordinal == i


@pytest.mark.parametrize("size", [MIN_PASSAGE_BYTES - 1, MIN_PASSAGE_BYTES + 1, MAX_PASSAGE_BYTES + 500])
def test_round_trips_at_the_chunker_boundaries(size):
    """The three sizes that select different code paths in the chunker."""
    doc = "## H\n\n" + ("z" * size)
    _assert_every_passage_round_trips(doc)
