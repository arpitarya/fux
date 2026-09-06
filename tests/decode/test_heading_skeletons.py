"""Structural headings, per format — W-115.

**A decoder's headings ARE its chunking.** `refer/_chunk.py` splits a document
into citable passages at `^#{1,6}` and nowhere else, and `ingest/extract.py`
mines the same lines into the `heading` field and the record's `phrases`. So a
decoder that emits no heading is not merely untidy: its format gets no `§`
lines in `fux ask`, and its documents are cut into blind fixed-size slabs.

Four formats emitted none at all, and two emitted the wrong ones. These tests
pin what each one now emits, and — as importantly — pin the two things that
must NOT change: an `.eml`'s shape, and every format's title.
"""

from __future__ import annotations

import json
import zlib

from fux.decode import decode

# -- PDF: `# <filename>` then `## Page N` ------------------------------------


def _pdf(*pages: bytes) -> bytes:
    """A PDF with one content stream per page. Built here rather than committed
    as a binary, so the input is readable beside the assertion."""
    out = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
    for index, content in enumerate(pages):
        body = zlib.compress(content)
        out += b"%d 0 obj\n<< /Length %d >>\nstream\n" % (index + 4, len(body))
        out += body + b"\nendstream\nendobj\n"
    return out + b"trailer\n<< /Root 1 0 R >>\n%%EOF\n"


TWO_PAGE = _pdf(
    b"BT /F1 12 Tf (Retention Policy) Tj 0 -20 Td (Records are kept seven years.) Tj ET",
    b"BT /F1 12 Tf (Litigation holds override the schedule.) Tj ET",
)


def test_a_pdf_emits_a_heading_per_page():
    """Before this, every PDF in every corpus decoded to one undivided blob and
    contributed no phrases at all."""
    out = decode(TWO_PAGE, "policy.pdf")
    assert "## Page 1" in out
    assert "## Page 2" in out


def test_a_pdf_title_is_still_the_filename():
    """`extract._title` takes the first heading. Without the H1 the title of
    every PDF would become the string `Page 1`."""
    from fux.ingest.extract import extract_fields
    from fux.ingest.parse import parse_document

    doc = parse_document(TWO_PAGE, "policy.pdf")
    assert extract_fields("policy.pdf", doc).title == "policy.pdf"


def test_a_pdf_page_heading_carries_that_page_s_text():
    out = decode(TWO_PAGE, "policy.pdf")
    first, second = out.split("## Page 2")
    assert "seven years" in first
    assert "Litigation holds" in second


def test_a_pdf_with_no_text_layer_is_still_none():
    """The enrichment-queue signal, unchanged: a page heading must never be
    manufactured for a document that has no text."""
    assert decode(b"%PDF-1.4\n1 0 obj\n<< >>\nendobj\ntrailer\n<< >>\n%%EOF\n", "s.pdf") is None


# -- RTF: `\outlinelevel` ----------------------------------------------------

RTF = rb"""{\rtf1\ansi\ansicpg1252
{\fonttbl{\f0 Times New Roman;}}
\pard\outlinelevel0\b Retention Policy\b0\par
\pard Records are kept for seven years.\par
\pard\outlinelevel1 Exceptions\par
\pard Litigation holds override the schedule.\par
}"""


def test_rtf_outline_levels_become_headings():
    out = decode(RTF, "policy.rtf")
    assert "# Retention Policy" in out
    assert "## Exceptions" in out


def test_rtf_body_paragraphs_are_not_headings():
    out = decode(RTF, "policy.rtf")
    assert "# Records are kept" not in out
    assert "Records are kept for seven years." in out


def test_rtf_still_never_leaks_the_font_table():
    """`\\outlinelevel` was chosen over style names precisely so the stylesheet
    stays a skipped destination group."""
    assert "Times New Roman" not in decode(RTF, "policy.rtf")


# -- CSV: the filename as H1 -------------------------------------------------


def test_a_csv_gets_a_heading_so_its_table_has_a_section():
    out = decode(b"owner,system\nSRE,queue\n", "owners.csv")
    assert out.startswith("# owners.csv")
    assert "| owner | system |" in out


# -- JSONL: one section per record -------------------------------------------


def test_each_jsonl_record_opens_its_own_section():
    """The record boundary used to be invisible, so a citation could span six
    unrelated log lines and read as one statement."""
    raw = b"\n".join(
        json.dumps({"summary": f"incident number {i} in the broker"}).encode() for i in range(3)
    )
    out = decode(raw, "incidents.jsonl")
    assert out.count("## Record ") == 3
    assert "## Record 1" in out and "## Record 3" in out


def test_a_malformed_jsonl_line_still_only_drops_itself():
    raw = b'{"summary": "the first one"}\nnot json at all\n{"summary": "the third one"}\n'
    out = decode(raw, "x.jsonl")
    assert out.count("## Record ") == 2
    assert "the first one" in out and "the third one" in out


# -- mbox: one section per message -------------------------------------------

MBOX = (
    b"From alice@x.com Mon Sep  1 10:00:00 2026\r\n"
    b"Subject: First thread\r\nFrom: alice@x.com\r\n\r\nBody one.\r\n"
    b"From bob@x.com Mon Sep  2 11:00:00 2026\r\n"
    b"Subject: Second thread\r\nFrom: bob@x.com\r\n\r\nBody two.\r\n"
)


def test_every_message_in_an_mbox_is_read():
    """`BytesParser` reads one message. Pointed at an archive it returned the
    first and silently discarded the rest."""
    out = decode(MBOX, "archive.mbox")
    assert "## First thread" in out
    assert "## Second thread" in out
    assert "Body one." in out and "Body two." in out


def test_an_mbox_is_titled_by_the_file_not_its_oldest_thread():
    out = decode(MBOX, "archive.mbox")
    assert out.startswith("# archive.mbox")


def test_a_single_eml_is_unchanged():
    """`.eml` keeps its H1 subject and its header block exactly as before —
    the mbox split must not reach it."""
    eml = b"Subject: Retention policy\r\nFrom: a@x.com\r\nTo: b@x.com\r\n\r\nSeven years.\r\n"
    out = decode(eml, "a.eml")
    assert out.startswith("# Retention policy")
    assert "**From:** a@x.com" in out
    assert "## " not in out


# -- the heading-depth cap ---------------------------------------------------


def test_deep_json_keys_stop_claiming_sections():
    """A heading is a section boundary and a `phrases` slot. One per key at
    every level filled all twelve slots with fifth-level keys while the
    top-level structure that names the document never made it in."""
    payload = {"service": {"broker": {"retention": {"policy": {"summary": "seven years"}}}}}
    out = decode(json.dumps(payload).encode(), "config.json")
    # A document's top-level keys ARE its outline; everything under them is
    # detail. `service` is reached at depth 2 — the root itself carries no
    # label — so the cap admits exactly that level and no more.
    assert "## service" in out
    assert "### broker" not in out


def test_a_deep_key_is_still_indexed_as_body_text():
    """Capped, not dropped — the term stays searchable, it just stops being a
    section."""
    payload = {"service": {"broker": {"retention": {"policy": {"summary": "seven years"}}}}}
    out = decode(json.dumps(payload).encode(), "config.json")
    assert "**retention**" in out
    assert "seven years" in out


def test_the_cap_applies_to_yaml_and_xml_too():
    yaml_out = decode(b"service:\n  broker:\n    retention:\n      policy:\n        note: keep\n", "a.yaml")
    assert "### retention" not in yaml_out
    xml_out = decode(b"<a><b><c><d><e>text here</e></d></c></b></a>", "a.xml")
    assert "#### d" not in xml_out


# -- a top-level JSON array is a list of records ------------------------------


def test_a_top_level_json_array_opens_a_section_per_item():
    """It emitted NO heading at all until 2026-09-06, so an export of six
    records decoded to one undivided block and was cited as one statement —
    the same defect `jsonl` fixed for the line-delimited spelling of exactly
    the same shape."""
    payload = [{"incident": f"INC-{i}", "summary": f"broker {i} dropped its queue"} for i in range(6)]
    out = decode(json.dumps(payload).encode(), "incidents.json")
    assert out.count("## Item ") == 6
    assert "## Item 1" in out and "## Item 6" in out


def test_an_array_of_scalars_is_not_a_record_array():
    """`["draft", "review", "done"]` are one document's values. A heading per
    string would be a heading per word."""
    out = decode(json.dumps({"states": ["draft", "review", "done"]}).encode(), "a.json")
    assert "## Item" not in out
    assert "draft" in out and "done" in out


def test_a_json_object_is_unaffected():
    out = decode(json.dumps({"service": {"note": "seven years of retention"}}).encode(), "c.json")
    assert "## Item" not in out
    assert "## service" in out


def test_a_very_long_array_is_truncated_and_says_so():
    payload = [{"n": f"record number {i}"} for i in range(600)]
    out = decode(json.dumps(payload).encode(), "big.json")
    assert out.count("## Item ") == 500
    assert "*(array truncated)*" in out


# -- the page strategy, declared by the decoders that need it ----------------


def test_the_three_page_decoders_declare_it():
    """`CHUNK` is opt-in on the `WANTS_PATH` precedent, so a decoder that says
    nothing still means `heading`."""
    from fux.decode import registry

    r = registry()
    assert r[".pptx"].chunk == "page"
    assert r[".mbox"].chunk == "page" and r[".eml"].chunk == "page"
    assert r[".drawio"].chunk == "page"
    assert r[".csv"].chunk == "heading"
    assert r[".md"] if ".md" in r else True


def test_an_unknown_chunk_strategy_is_a_hard_error(tmp_path):
    """A typo that silently fell back to `heading` would be a citation defect
    with no signal — the shape decision 7 refuses for a missing dependency."""
    import pytest

    from fux.decode import _chunk_strategy
    from fux.errors import FuxError

    class Bad:
        CHUNK = "pages"

    with pytest.raises(FuxError, match="pages"):
        _chunk_strategy(Bad, "baddoc")


def test_an_html_email_body_cannot_outrank_its_own_subject():
    """🔴 `htmldoc` maps `<h1>` to `#`, so a message body emitted a LEVEL-1
    heading under its own `## Subject`. One email became four passages, two
    cited as top-level units of the archive."""
    mbox = (
        b"From a@x.com Mon Sep  1 10:00:00 2026\r\n"
        b"Subject: Retention decision\r\nContent-Type: text/html\r\n\r\n"
        b"<h1>Background</h1><p>three years</p><h2>Decision</h2><p>seven years</p>\r\n"
    )
    out = decode(mbox, "a.mbox")
    levels = [len(l) - len(l.lstrip("#")) for l in out.split("\n") if l.startswith("#")]
    subject = out.split("\n").index("## Retention decision")
    body = [i for i, l in enumerate(out.split("\n")) if l.startswith("#") and i > subject]
    assert all(out.split("\n")[i].startswith("###") for i in body)
    assert max(levels) <= 6


def test_a_fenced_hash_in_an_email_body_is_not_demoted():
    """`_demote` reads the one fence-aware grammar, so a shell comment in an
    email stays a shell comment."""
    eml = (
        b"Subject: Runbook\r\nContent-Type: text/html\r\n\r\n"
        b"<pre># Install dependencies\nuv sync</pre>\r\n"
    )
    out = decode(eml, "a.eml")
    assert "# Install dependencies" in out
    assert "### Install dependencies" not in out
