"""Unit suite for the heading-based chunker."""

from __future__ import annotations

from fux.ingest.chunk import chunk_markdown


def words(n: int, base: str = "w") -> str:
    return " ".join(f"{base}{i}" for i in range(n))


def test_empty_body():
    assert chunk_markdown("") == []
    assert chunk_markdown("\n\n  \n") == []


def test_heading_paths_nest():
    body = (
        "# Guide\n\n"
        + words(300)
        + "\n\n## Install\n\n"
        + words(300)
        + "\n\n## Use\n\n"
        + words(300)
        + "\n\n# Other\n\n"
        + words(300)
    )
    chunks = chunk_markdown(body)
    paths = [c.heading_path for c in chunks]
    assert "Guide" in paths
    assert "Guide > Install" in paths
    assert "Guide > Use" in paths
    assert "Other" in paths


def test_small_sections_merge():
    body = "# A\n\nshort a\n\n# B\n\nshort b\n\n# C\n\nshort c"
    chunks = chunk_markdown(body)
    assert len(chunks) == 1  # far under target_min: everything merges
    assert chunks[0].heading_path == "A"


def test_sizes_within_target():
    body = "\n\n".join(f"## S{i}\n\n{words(120, f's{i}_')}" for i in range(10))
    chunks = chunk_markdown(body)
    for c in chunks[:-1]:
        assert c.words <= 512
    assert sum(c.words for c in chunks) >= 1200


def test_code_fence_atomic():
    fence = "```python\n" + "\n".join(f"line_{i} = {i}" for i in range(700)) + "\n```"
    body = f"# H\n\nintro text here\n\n{fence}\n\nafter text"
    chunks = chunk_markdown(body)
    fenced = [c for c in chunks if "```python" in c.text]
    assert len(fenced) == 1
    assert fenced[0].text.count("```") == 2  # opener + closer stayed together


def test_table_atomic():
    table = "\n".join(f"| a{i} | b{i} |" for i in range(50))
    body = f"# H\n\n{words(500)}\n\n{table}\n\nafter"
    chunks = chunk_markdown(body)
    tabled = [c for c in chunks if "| a0 |" in c.text]
    assert len(tabled) == 1
    assert "| a49 |" in tabled[0].text  # the whole table in one chunk


def test_oversize_paragraph_splits_with_overlap():
    body = words(1200)
    chunks = chunk_markdown(body)
    assert len(chunks) >= 3
    first = chunks[0].text.split()
    second = chunks[1].text.split()
    assert len(first) == 512
    overlap = int(512 * 0.12)
    assert first[-overlap:] == second[:overlap]


def test_no_headings_fallback():
    body = "para one alpha beta gamma delta.\n\npara two epsilon zeta eta theta."
    chunks = chunk_markdown(body)
    assert len(chunks) == 1
    assert chunks[0].heading_path == ""
    assert chunks[0].start_line == 1


def test_line_spans_match_body():
    body = "# Title\n\nfirst para line one\nline two\n\nsecond para"
    chunks = chunk_markdown(body)
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 6  # "second para" is body line 6... adjusted below
    lines = body.split("\n")
    assert lines[chunks[0].start_line - 1] == "# Title"


def test_unclosed_fence_does_not_hang():
    body = "# H\n\n```py\nno closer"
    chunks = chunk_markdown(body)
    assert len(chunks) == 1
