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


# -- the shared grammar, and what it stopped cutting in half -----------------


def test_a_fenced_hash_comment_does_not_open_a_passage():
    """`refer/_chunk.py` used to split here, cutting a code example in two and
    titling the second half with a shell comment."""
    doc = f"# A\n\n{_body('alpha')}\n\n```bash\n# Install dependencies\nuv sync\n```\n"
    passages = chunk(doc)
    assert [p.heading for p in passages] == ["A"]
    assert "# Install dependencies" in passages[0].text


# -- oversized tables, which no blank line could ever split ------------------


def _table(rows: int) -> str:
    body = "\n".join(f"| row{i} | {'data ' * 8}| more |" for i in range(rows))
    return f"## Sheet1\n\n| name | value | note |\n|---|---|---|\n{body}\n"


def test_an_oversized_table_is_banded_rather_than_returned_whole():
    """A table contains no blank line, so before banding a 40 KB sheet came
    back as one passage the assembler then refused to seat — a document that
    ranks and cannot be quoted."""
    passages = chunk(_table(200))
    assert len(passages) > 1
    for p in passages:
        assert p.nbytes <= MAX_PASSAGE_BYTES


def test_every_row_of_a_banded_table_survives():
    passages = chunk(_table(200))
    joined = "\n".join(p.text for p in passages)
    assert [i for i in range(200) if f"row{i} " not in joined] == []


def test_each_band_repeats_the_header_row():
    """The one documented exception to totality: a band whose columns have no
    names is a citation nobody can read."""
    passages = chunk(_table(200))
    for p in passages:
        assert "| name | value | note |" in p.text


def test_a_banded_table_keeps_its_section_heading_out_of_a_runt():
    """The heading joins the first band. Emitted beside it, `## Sheet1` was a
    9-byte passage the merge pass never sees — merging happens before
    splitting."""
    passages = chunk(_table(200))
    assert passages[0].text.startswith("## Sheet1")
    assert all(p.heading == "Sheet1" for p in passages)


def test_band_line_ranges_are_contiguous_and_do_not_overlap():
    """The repeated header means a band holds more lines than it covers, which
    is why the splitter reports source lines rather than its own."""
    passages = chunk(_table(200))
    for earlier, later in zip(passages, passages[1:]):
        assert later.line_start == earlier.line_end + 1


def test_a_small_table_is_split_too_not_only_an_oversized_one():
    """`_pieces` used to return early whenever a section fitted the ceiling, so
    a ten-row table — the common case — never reached the row split at all."""
    passages = chunk(_table(3))
    assert len(passages) == 3


def test_every_row_still_carries_the_header():
    """A row whose columns have no names is a citation nobody can read. This is
    the one documented exception to totality."""
    for p in chunk(_table(20)):
        assert "| name | value | note |" in p.text


# -- generated text has no line numbers to cite ------------------------------


def test_line_numbers_can_be_suppressed_for_generated_text():
    """A decoded `.docx` is Markdown that exists nowhere on disk, so
    `path:L12-L40` would point at nothing. `_rescore.locator` falls back to
    `path#p3`."""
    doc = f"# A\n\n{_body('alpha')}\n\n## B\n\n{_body('beta')}"
    passages = chunk(doc, line_numbers=False)
    assert len(passages) == 2
    assert all(p.line_start == 0 and p.line_end == 0 for p in passages)
    assert [p.heading for p in passages] == ["A", "B"]


# -- a table band is a neighbourhood, not a chapter and not a row ------------


def test_a_table_is_split_one_row_per_passage():
    """Ruled by Arpit 2026-09-06 on the measurement in
    `work/regression/2026-09-06-csv-chunk-granularity/`: on ambiguous queries
    `hit@1` went 0.208 (58-row bands) -> 0.229 (11-row) -> 0.875 (per row)."""
    from fux.refer._chunk import TABLE_ROWS_PER_PASSAGE

    assert TABLE_ROWS_PER_PASSAGE == 1
    passages = chunk(_table(200))
    assert len(passages) == 200
    for p in passages:
        assert p.text.count("\n| row") == 1


def test_prose_still_bands_at_the_prose_ceiling():
    """The table ceiling must not reach ordinary text."""
    paragraphs = "\n\n".join(_body("word", 60) for _ in range(20))
    passages = chunk(f"# Big\n\n{paragraphs}")
    assert max(p.nbytes for p in passages) > 2000


# -- the runt floor no longer eats structural boundaries ---------------------


def test_a_run_of_short_headed_sections_is_not_folded_together():
    """Three instances of one defect: a `.pptx` slide with two bullets merged
    into the next slide, six small `.jsonl` records came back as one passage,
    and any short band of a small table would have gone the same way. A record
    in a run is a complete unit, not a stub."""
    doc = "\n\n".join(f"## Record {i}\n\n**msg:** event {i}" for i in range(1, 7))
    passages = chunk(doc)
    assert [p.heading for p in passages] == [f"Record {i}" for i in range(1, 7)]


def test_a_stub_heading_folds_into_its_own_SUBSECTION():
    """The rule the floor was written for, kept: `## Notes` with one line under
    it is not a citation on its own — but it may only be absorbed by something
    NESTED INSIDE it."""
    doc = f"## Notes\n\nsee below.\n\n### Detail\n\n{_body('beta')}"
    passages = chunk(doc)
    assert len(passages) == 1
    assert "see below." in passages[0].text and "beta" in passages[0].text
    assert passages[0].heading == "Notes", "the enclosing section names the fold"


def test_two_SIBLING_stubs_never_fold_into_each_other():
    """🔴 The defect the strategy knob used to work around. Under the old rule
    a short section folded forward into whatever came next, sibling or not, so
    a short slide, record or page was absorbed by the next one and cited under
    its name. Depth is the whole fix: siblings are not nested."""
    doc = "## Record 1\n\nbroker timeout\n\n## Record 2\n\nqueue drained\n"
    assert [p.heading for p in chunk(doc)] == ["Record 1", "Record 2"]
    assert "queue drained" not in chunk(doc)[0].text


def test_a_short_preamble_folds_into_the_first_section():
    """A preamble is level 0, so every heading is nested inside it. It carries
    its text forward and the first real heading names the passage."""
    doc = f"tiny.\n\n# A\n\n{_body('alpha')}"
    passages = chunk(doc)
    assert [p.heading for p in passages] == ["A"]
    assert "tiny." in passages[0].text


def test_a_document_with_no_heading_at_all_is_one_passage():
    """Totality: nothing to fold into, so the floor cannot strand it."""
    passages = chunk("just prose, no heading anywhere\n")
    assert len(passages) == 1 and passages[0].heading == ""


# -- the unit: a slide, a message, a page, a record ---------------------------


def _deck(short_slide: int = 2) -> str:
    long = "- a bullet with some real length\n" * 20
    parts = ["# deck.pptx\n"]
    for i in (1, 2, 3):
        body = "- two words\n" if i == short_slide else long
        parts.append(f"## Slide {i}\n\n{body}")
    return "\n".join(parts)


def test_a_unit_is_never_absorbed_by_a_neighbour():
    """🔴 Measured 2026-09-06: this deck cited Slide 1's content as `deck.pptx`
    and Slide 3's as `Slide 2` — confidently the WRONG attribution, which is
    worse than a coarse citation. Nothing is declared to fix it; the slides are
    siblings, and siblings do not fold."""
    for short in (1, 2, 3):
        assert [p.heading for p in chunk(_deck(short))] == ["Slide 1", "Slide 2", "Slide 3"], short


def test_each_unit_carries_only_its_own_content():
    pages = {p.heading: p.text for p in chunk(_deck())}
    assert "two words" in pages["Slide 2"]
    assert "two words" not in pages["Slide 3"]
    assert "two words" not in pages["Slide 1"]


def test_the_document_title_never_names_a_unit():
    """`# deck.pptx` is short and every slide is nested inside it, so it folds.
    If it also supplied the heading, slide 1's content would be cited as
    `deck.pptx` — the original defect arriving by a different route."""
    first = chunk(_deck(short_slide=1))[0]
    assert first.heading == "Slide 1"
    assert "# deck.pptx" in first.text, "the title is context, not a lost byte"


def test_a_heading_INSIDE_a_unit_does_not_rename_it():
    """An mbox message whose body is HTML carries that body's headings. They
    are nested, so they fold back in — and the MESSAGE names the passage, not
    the deepest thing in its body."""
    doc = (
        "# archive.mbox\n\n## Subject one\n\n### Body head\n\ntext here\n\n"
        "#### Deeper\n\nmore\n\n## Subject two\n\nlast\n"
    )
    passages = chunk(doc)
    assert [p.heading for p in passages] == ["Subject one", "Subject two"]
    assert "Deeper" in passages[0].text


def test_unit_line_ranges_stay_contiguous():
    passages = chunk(_deck())
    for earlier, later in zip(passages, passages[1:]):
        assert later.line_start > earlier.line_end


def test_prose_still_chunks_at_its_headings():
    doc = f"# A\n\n{_body('alpha')}\n\n## B\n\n{_body('beta')}"
    assert [p.heading for p in chunk(doc)] == ["A", "B"]


def test_there_is_no_strategy_parameter():
    """The knob is gone, and its absence is pinned. What a passage is derives
    from the document's own heading depth, so there is nothing for a caller or
    a decoder to set — and nothing for either to set WRONG."""
    import inspect

    assert "strategy" not in inspect.signature(chunk).parameters


# -- the fallback ladder: paragraph -> line -> word --------------------------


def test_a_wall_of_text_can_be_quoted_at_all():
    """🔴 A 12 KB document with no blank line came back as ONE 10 889-byte
    passage — over the ceiling and over the whole budget — so the assembler
    seated ZERO citations. The document ranked and could not be quoted."""
    from fux.refer._assemble import DEFAULT_BUDGET, assemble
    from fux.refer._rescore import rescore

    wall = "# Notes\n\n" + " ".join(
        f"sentence number {i} about the broker retention policy." for i in range(200)
    )
    passages = chunk(wall)
    assert len(passages) > 1
    assert max(p.nbytes for p in passages) <= MAX_PASSAGE_BYTES
    seated = assemble(
        rescore("broker retention policy", [("d", "n.md", "s", passages)]),
        budget=DEFAULT_BUDGET, k=5, source="fetched",
    )
    assert seated.citations, "a document that ranks must be quotable"


def test_the_line_rung_is_preferred_over_the_word_rung():
    """A word cut is the floor, not the first resort. Nearly all real prose has
    newlines and never gets past the line rung."""
    doc = "# Log\n\n" + "\n".join(
        f"2026-09-06 event {i} in the broker pipeline with detail" for i in range(400)
    )
    rungs = {p.cut for p in chunk(doc)}
    assert "line" in rungs
    assert "word" not in rungs


def test_a_passage_records_which_rung_cut_it():
    """A span cut between two words is a real citation and must not pretend to
    be a paragraph."""
    wall = "# Notes\n\n" + " ".join(f"word{i}" for i in range(4000))
    assert {p.cut for p in chunk(wall)} == {"", "word"}


def test_an_author_boundary_is_recorded_as_no_cut():
    doc = f"# A\n\n{_body('alpha')}\n\n## B\n\n{_body('beta')}"
    assert all(p.cut == "" for p in chunk(doc))


def test_no_word_is_ever_split():
    wall = "# N\n\n" + " ".join(f"token{i:05d}" for i in range(3000))
    joined = " ".join(p.text for p in chunk(wall) if p.cut == "word")
    for i in range(3000):
        assert f"token{i:05d}" in joined


def test_a_single_unbreakable_token_comes_back_whole():
    """No rung can cut it, and inventing one would corrupt the content. The
    assembler refuses it downstream — which is correct, and now it is the ONLY
    case that reaches that."""
    blob = "# N\n\n" + "x" * 9000
    passages = chunk(blob)
    assert any(p.nbytes > MAX_PASSAGE_BYTES for p in passages)
