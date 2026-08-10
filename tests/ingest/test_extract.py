from __future__ import annotations

from fux.ingest.extract import extract_fields
from fux.ingest.parse import parse


def test_title_from_frontmatter():
    doc = parse(b"---\ntitle: Explicit Title\n---\n# Heading\nbody\n")
    assert extract_fields("a.md", doc).title == "Explicit Title"


def test_title_falls_back_to_first_heading():
    doc = parse(b"# The Heading\n\nbody text\n")
    assert extract_fields("a.md", doc).title == "The Heading"


def test_title_falls_back_to_filename():
    doc = parse(b"no heading here, just prose\n")
    assert extract_fields("docs/notes.md", doc).title == "notes.md"


def test_phrases_are_headings_only_capped_at_12():
    body = "\n".join(f"## Heading {i}" for i in range(20))
    doc = parse(body.encode("utf-8"))
    fields = extract_fields("a.md", doc)
    assert fields.phrases == [f"Heading {i}" for i in range(12)]


def test_terms_split_heading_and_body_tf():
    doc = parse(b"# install guide\n\ninstall the thing, then install again\n")
    fields = extract_fields("a.md", doc)
    # title falls back to the one heading, so it isn't double-counted: tf_heading=1
    assert fields.terms["install"] == (1, 2)


def test_frontmatter_title_distinct_from_heading_is_counted_too():
    doc = parse(b"---\ntitle: install now\n---\n# setup guide\n\nsome body text\n")
    fields = extract_fields("a.md", doc)
    # "install" appears only in the (distinct) frontmatter title -> heading tf=1
    assert fields.terms["install"] == (1, 0)


def test_wlen_is_integer_and_weighted():
    doc = parse(b"# x b\n\nc d e\n")
    fields = extract_fields("x.md", doc)
    # title falls back to the heading "x b" — not double-counted: heading tokens = 2
    # body tokens: "c","d","e" = 3
    assert isinstance(fields.wlen, int)
    assert fields.wlen == 3 * 2 + 1 * 3


def test_code_field_present_when_embeddable():
    doc = parse(b"# Rollback procedure\n\nRollbacks complete within two minutes.\n")
    fields = extract_fields("a.md", doc)
    assert fields.code is not None
    import base64

    # must decode cleanly as unpadded base64url
    padded = fields.code + "=" * (-len(fields.code) % 4)
    assert len(base64.urlsafe_b64decode(padded)) == 32


def test_code_field_absent_for_unembeddable_text():
    # title falls back to filename otherwise, and "a.md" alone is embeddable —
    # pin an all-emoji frontmatter title too so the whole embed input is OOV.
    doc = parse('---\ntitle: "🎯🎯🎯"\n---\n\n🎯 🎯 🎯\n'.encode("utf-8"))
    fields = extract_fields("a.md", doc)
    assert fields.code is None


def test_extraction_is_deterministic():
    doc = parse(b"# Title\n\nsome repeated repeated words\n")
    a = extract_fields("a.md", doc)
    b = extract_fields("a.md", doc)
    assert a == b
