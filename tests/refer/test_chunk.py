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


def test_a_lone_stub_heading_still_folds_forward():
    """The rule the floor was written for, unchanged: `## Notes` followed by
    something substantial is not a citation on its own."""
    doc = f"## Notes\n\nsee below.\n\n## Detail\n\n{_body('beta')}"
    passages = chunk(doc)
    assert len(passages) == 1
    assert "see below." in passages[0].text and "beta" in passages[0].text


def test_a_short_preamble_is_still_governed_by_the_old_rule():
    """A preamble has no heading, so `_sibling_run` returns early and the
    original rule decides — and that rule never folded a headless preamble
    (`heading or carry` is false for the first section). Unchanged, and pinned
    here because the new exception must not reach it."""
    doc = f"tiny.\n\n# A\n\n{_body('alpha')}"
    passages = chunk(doc)
    assert [p.heading for p in passages] == ["", "A"]
    assert passages[0].text == "tiny."
