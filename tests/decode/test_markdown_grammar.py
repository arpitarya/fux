"""The one Markdown heading grammar — `decode/_markdown.py`.

Both `ingest/extract.py` and `refer/_chunk.py` read this module, so a defect
here is a ranking defect and a citation defect at the same time. The case that
created it is the first test: a `#` comment inside a fenced code block, which
both planes used to count as a heading.
"""

from __future__ import annotations

from fux.decode._markdown import headings, strip_headings

FENCED = """# Real Heading

Prose about setup.

```bash
# Install dependencies
uv sync --extra dev
```

## Second Real Heading

More prose.
"""


def test_a_hash_comment_inside_a_fence_is_not_a_heading():
    """The defect this module exists for. Every ADR in this repository opens a
    ```bash block containing a `# comment` line; each one used to be mined as a
    heading, weighted as a heading, and published in `phrases`."""
    assert [h.text for h in headings(FENCED)] == ["Real Heading", "Second Real Heading"]


def test_a_fenced_comment_stays_in_the_body():
    """It is body text and always was. Stripping it removed words a reader can
    see from the field the index searches."""
    body = strip_headings(FENCED)
    assert "# Install dependencies" in body
    assert "uv sync --extra dev" in body


def test_real_headings_are_removed_from_the_body():
    """Without this a heading's words count twice — once as heading tf, once as
    body tf — and "heading match outranks body match" stops meaning anything."""
    body = strip_headings(FENCED)
    assert "# Real Heading" not in body
    assert "## Second Real Heading" not in body


def test_line_numbers_are_one_based():
    found = headings(FENCED)
    assert found[0].lineno == 1
    assert FENCED.split("\n")[found[1].lineno - 1] == "## Second Real Heading"


def test_levels_come_from_the_hash_run():
    assert [h.level for h in headings("# a\n\n### c\n\n###### f\n")] == [1, 3, 6]
    assert headings("####### seven\n") == []  # seven hashes is not a heading


def test_a_closing_atx_sequence_is_not_part_of_the_title():
    """`_chunk` stripped it and `extract` kept it, so the same document's
    heading was `Rollbacks` to one plane and `Rollbacks ###` to the other."""
    assert [h.text for h in headings("## Rollbacks ##\n")] == ["Rollbacks"]


def test_tilde_fences_are_fences_too():
    assert headings("~~~\n# not a heading\n~~~\n") == []


def test_a_backtick_run_does_not_close_a_tilde_block():
    doc = "~~~\n```\n# still inside the tilde block\n```\n~~~\n\n# after\n"
    assert [h.text for h in headings(doc)] == ["after"]


def test_a_shorter_fence_does_not_close_a_longer_one():
    doc = "````\n```\n# still code\n```\n````\n\n# after\n"
    assert [h.text for h in headings(doc)] == ["after"]


def test_a_fence_with_an_info_string_does_not_close_a_block():
    """```python inside a ``` block opens nothing and closes nothing."""
    doc = "```\n```python\n# still code\n```\n\n# after\n"
    assert [h.text for h in headings(doc)] == ["after"]


def test_an_unclosed_fence_runs_to_the_end_of_the_document():
    """CommonMark's rule, and the forgiving one: treating the remainder as
    prose would resurrect exactly the miscount this module prevents."""
    assert headings("```\n# never closed\n\n# nor this\n") == []


def test_an_indented_hash_was_never_a_heading_and_still_is_not():
    assert headings("    # four-space indented\n") == []


def test_setext_headings_are_deliberately_not_recognised():
    """Recognising them would change what counts as a heading in every
    hand-written `.md` in every corpus, with no defect behind it."""
    assert headings("Title\n=====\n") == []


def test_the_scan_is_deterministic():
    assert headings(FENCED) == headings(FENCED)


def test_a_document_with_no_headings_is_returned_unchanged():
    plain = "just prose\n\nand more prose\n"
    assert headings(plain) == []
    assert strip_headings(plain) == plain
