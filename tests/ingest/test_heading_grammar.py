"""W-86 P0 — the three allowed types whose headings reached nothing.

`DEFAULT_TYPES` has admitted `.rst`, `.adoc` and `.org` since the allowlist
shipped, and `extract.py` knew only `#`. **Every heading in those three formats
landed in the body field** and their `phrases` list was empty — three of six
allowed types, silently, for as long as the filter existed.

These tests are written against the *consequence* (the heading reaches the
heading field, the body no longer contains it) rather than against the regex,
because the regex is the implementation and the field placement is the promise.
"""

from __future__ import annotations

import pytest

from fux.ingest.extract import extract_fields
from fux.ingest.parse import ParsedDoc

RST = "Broker Runbook\n==============\n\nDrain the queue.\n\nDraining\n--------\n\nStop consumers.\n"
ADOC = "= Broker Runbook\n\nDrain the queue.\n\n== Draining\n\nStop consumers.\n"
ORG = "* Broker Runbook\n\nDrain the queue.\n\n** Draining\n\nStop consumers.\n"
MD = "# Broker Runbook\n\nDrain the queue.\n\n## Draining\n\nStop consumers.\n"


@pytest.mark.parametrize(
    "name,body", [("a.rst", RST), ("a.adoc", ADOC), ("a.org", ORG), ("a.md", MD)]
)
def test_headings_reach_the_heading_field(name, body):
    out = extract_fields(name, ParsedDoc(meta={}, body=body))
    assert out.phrases == ["Broker Runbook", "Draining"], name
    assert out.title == "Broker Runbook", name


@pytest.mark.parametrize(
    "name,body", [("a.rst", RST), ("a.adoc", ADOC), ("a.org", ORG), ("a.md", MD)]
)
def test_a_heading_is_not_counted_twice(name, body):
    """A heading's words must leave the body, or they count once as heading tf
    and once as body tf — which dilutes exactly the signal the field exists for.
    """
    out = extract_fields(name, ParsedDoc(meta={}, body=body))
    body_tf, heading_tf = out.terms["runbook"][0], out.terms["runbook"][1]
    assert heading_tf == 1, name
    assert body_tf == 0, name


def test_org_emphasis_is_not_a_heading():
    """`*emphasis*` and `**bold**` start a line with asterisks and are prose.
    The required space after the run is the whole guard.
    """
    out = extract_fields("a.org", ParsedDoc(meta={}, body="* Real\n\n*emphasis* here\n"))
    assert out.phrases == ["Real"]


def test_rst_needs_a_full_width_rule():
    """A short underline is not a heading — and a row of dashes inside a table
    is not one either. reStructuredText requires the rule to run the width of
    the text, and honouring that is what keeps tables out of the heading field.
    """
    out = extract_fields("a.rst", ParsedDoc(meta={}, body="Title\n=====\n\nnot\n-\n"))
    assert out.phrases == ["Title"]


def test_adoc_level_one_is_the_document_title():
    out = extract_fields("a.adoc", ParsedDoc(meta={}, body="= Doc\n\n== Section\n"))
    assert out.phrases == ["Doc", "Section"]


def test_a_decoded_document_always_uses_the_markdown_grammar():
    """Decoders emit Markdown (ADR-DECODE decision 2), so a `.docx` or `.pdf`
    must NOT be read with an Office-shaped grammar — there is no such thing.
    Only already-prose files take a different pattern.
    """
    out = extract_fields("a.docx", ParsedDoc(meta={}, body="# From a decoder\n\nbody\n"))
    assert out.phrases == ["From a decoder"]


def test_an_unknown_extension_falls_back_to_markdown():
    out = extract_fields("a.weird", ParsedDoc(meta={}, body="# Still a heading\n"))
    assert out.phrases == ["Still a heading"]
