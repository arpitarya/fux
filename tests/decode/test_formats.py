"""Every built-in decoder — W-86 P2-P5.

Fixtures are **built in the test rather than committed as binaries**. A
committed `.docx` is opaque in a diff: when its expected output changes nobody
can see why, and nobody can tell a fixture edit from a decoder regression.
Built here, the input is readable beside the assertion.

The assertions favour *the terms a searcher would type* over exact Markdown.
Byte-exactness would make every decoder improvement a fixture rewrite, which is
how a suite stops being run.
"""

from __future__ import annotations

import base64
import io
import zipfile
import zlib

import pytest

from fux.decode import decode

# -- fixture builders -------------------------------------------------------


def zf(parts: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        for name in sorted(parts):
            archive.writestr(name, parts[name])
    return buf.getvalue()


DOCX = zf(
    {
        "word/document.xml": """<?xml version="1.0"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
<w:p><w:pPr><w:pStyle w:val="Title"/></w:pPr><w:r><w:t>Broker Runbook</w:t></w:r></w:p>
<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Draining</w:t></w:r></w:p>
<w:p><w:r><w:t>Drain the </w:t></w:r><w:r><w:t>queue</w:t></w:r><w:r><w:t> first.</w:t></w:r></w:p>
<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/></w:numPr></w:pPr><w:r><w:t>stop consumers</w:t></w:r></w:p>
<w:tbl><w:tr><w:tc><w:p><w:r><w:t>step</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>owner</w:t></w:r></w:p></w:tc></w:tr>
<w:tr><w:tc><w:p><w:r><w:t>drain</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>sre</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
</w:body></w:document>"""
    }
)


def _slide(title: str, body: str) -> str:
    return f"""<?xml version="1.0"?><p:sld
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
 xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:cSld><p:spTree>
<p:sp><p:nvSpPr><p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr>
<p:txBody><a:p><a:r><a:t>{title}</a:t></a:r></a:p></p:txBody></p:sp>
<p:sp><p:txBody><a:p><a:r><a:t>{body}</a:t></a:r></a:p></p:txBody></p:sp>
</p:spTree></p:cSld></p:sld>"""


PPTX = zf(
    {
        "ppt/slides/slide2.xml": _slide("Second slide", "two body"),
        "ppt/slides/slide10.xml": _slide("Tenth slide", "ten body"),
        "ppt/notesSlides/notesSlide2.xml": (
            '<?xml version="1.0"?><p:notes xmlns:p="urn:p"'
            ' xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            "<a:p><a:r><a:t>speaker note here</a:t></a:r></a:p></p:notes>"
        ),
    }
)

_SS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
XLSX = zf(
    {
        "xl/sharedStrings.xml": f'<?xml version="1.0"?><sst xmlns="{_SS}">'
        "<si><t>step</t></si><si><t>owner</t></si>"
        "<si><t>drain the queue</t></si><si><t>sre</t></si></sst>",
        "xl/workbook.xml": f'<?xml version="1.0"?><workbook xmlns="{_SS}">'
        '<sheets><sheet name="Runbook"/></sheets></workbook>',
        "xl/worksheets/sheet1.xml": f'<?xml version="1.0"?><worksheet xmlns="{_SS}"><sheetData>'
        '<row><c t="s"><v>0</v></c><c t="s"><v>1</v></c></row>'
        '<row><c t="s"><v>2</v></c><c t="s"><v>3</v></c></row>'
        "</sheetData></worksheet>",
    }
)

ODT = zf(
    {
        "content.xml": """<?xml version="1.0"?><office:document-content
 xmlns:office="urn:o" xmlns:text="urn:t" xmlns:table="urn:tb"><office:body><office:text>
<text:h text:outline-level="1">Broker Runbook</text:h>
<text:p>Drain the queue first.</text:p>
<table:table><table:table-row>
<table:table-cell><text:p>step</text:p></table:table-cell>
<table:table-cell><text:p>owner</text:p></table:table-cell>
</table:table-row></table:table>
</office:text></office:body></office:document-content>"""
    }
)


def _drawio(model: str) -> bytes:
    obj = zlib.compressobj(9, zlib.DEFLATED, -15)
    payload = base64.b64encode(obj.compress(model.encode()) + obj.flush()).decode()
    return f'<mxfile><diagram name="Architecture">{payload}</diagram></mxfile>'.encode()


DRAWIO = _drawio(
    "<mxGraphModel><root>"
    '<mxCell id="1" value="Ingest plane"/>'
    '<mxCell id="2" value="&lt;b&gt;Refer&lt;/b&gt; plane"/>'
    "</root></mxGraphModel>"
)


def _pdf(content: bytes, *, compress: bool = True) -> bytes:
    body = zlib.compress(content) if compress else content
    out = b"%PDF-1.4\n"
    out += b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    out += b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    out += b"3 0 obj\n<< /Type /Page /Contents 4 0 R >>\nendobj\n"
    out += b"4 0 obj\n<< /Length %d >>\nstream\n" % len(body) + body + b"\nendstream\nendobj\n"
    return out + b"trailer\n<< /Root 1 0 R >>\n%%EOF\n"


PDF = _pdf(
    b"""BT /F1 12 Tf 72 720 Td (Broker Runbook) Tj
0 -20 Td (Drain the queue first, then restart the bro-) Tj
0 -20 Td (ker service.) Tj
0 -20 Td [(Owner) -250 (: SRE team)] TJ ET"""
)


# -- OOXML ------------------------------------------------------------------


def test_docx_headings_lists_and_tables():
    out = decode(DOCX, "runbook.docx")
    assert out is not None
    assert "# Broker Runbook" in out, "Title style must map to H1, above Heading 1"
    assert "## Draining" in out
    assert "- stop consumers" in out
    assert "| step | owner |" in out


def test_docx_joins_runs_without_inserting_spaces():
    """Word splits a word across runs whenever formatting or a spell-check
    touches it. A space between runs turns "queue" into "que ue" and the term
    stops matching what anyone types.
    """
    out = decode(DOCX, "runbook.docx")
    assert "Drain the queue first." in out


def test_docx_table_cells_are_not_emitted_twice():
    """Cells are paragraphs too. Without the in-table check they appear in the
    table AND as loose paragraphs, doubling their `tf`.
    """
    out = decode(DOCX, "runbook.docx")
    assert out.count("drain") == 1


def test_pptx_orders_slides_numerically_not_lexically():
    """slide10 sorts before slide2 lexically. A deck read that way is
    deterministic and wrong, which is worse than noisy — nothing looks broken.
    """
    out = decode(PPTX, "deck.pptx")
    assert out.index("Second slide") < out.index("Tenth slide")


def test_pptx_keeps_speaker_notes():
    assert "speaker note here" in decode(PPTX, "deck.pptx")


def test_pptx_untitled_slide_still_gets_a_heading():
    deck = zf({"ppt/slides/slide1.xml": _slide("", "orphan bullet")})
    out = decode(deck, "deck.pptx")
    assert "## Slide 1" in out


def test_xlsx_resolves_the_shared_string_table():
    """Most cell text is not in the sheet — it is an index into
    `sharedStrings.xml`. A decoder that misses that finds only numbers.
    """
    out = decode(XLSX, "book.xlsx")
    assert "drain the queue" in out
    assert "## Runbook" in out, "the sheet name is its heading"


def test_odf_text_is_not_read_through_the_ooxml_walker():
    """ODF puts text directly on `text:p`; OOXML nests it in run elements.
    Reusing the OOXML walker returned empty for every plain paragraph — a whole
    format decoding to nothing, with no error anywhere.
    """
    out = decode(ODT, "doc.odt")
    assert out is not None
    assert "# Broker Runbook" in out
    assert "Drain the queue first." in out


@pytest.mark.parametrize("ext", [".odt", ".ods", ".odp"])
def test_one_module_serves_all_three_opendocument_types(ext):
    assert decode(ODT, "doc" + ext) is not None


# -- the smaller formats ----------------------------------------------------


def test_drawio_inflates_the_compressed_model_and_converts_html_labels():
    out = decode(DRAWIO, "arch.drawio")
    assert out is not None
    assert "Ingest plane" in out
    assert "Refer" in out and "&lt;" not in out


def test_rtf_drops_font_tables_and_keeps_prose():
    raw = rb"{\rtf1\ansi{\fonttbl{\f0 Times New Roman;}}\b Broker\b0  runbook\par drain the queue\par}"
    out = decode(raw, "a.rtf")
    assert "Broker runbook" in out
    assert "Times New Roman" not in out, "the font table is metadata, not prose"


def test_rtf_decodes_codepage_escapes():
    raw = rb"{\rtf1\ansi\ansicpg1252 caf\'e5 na\'efve\par}"
    out = decode(raw, "a.rtf")
    assert "\\'" not in out


def test_eml_subject_leads_and_attachments_are_not_opened():
    raw = (
        b"Subject: Broker restart\r\nFrom: sre@example.com\r\n"
        b'Content-Type: multipart/mixed; boundary="B"\r\n\r\n'
        b"--B\r\nContent-Type: text/plain\r\n\r\nDrain the queue first.\r\n"
        b'--B\r\nContent-Type: application/pdf\r\nContent-Disposition: attachment; filename="x.pdf"\r\n\r\n'
        b"%PDF-1.4 attachment body\r\n--B--\r\n"
    )
    out = decode(raw, "mail.eml")
    assert out.startswith("# Broker restart")
    assert "Drain the queue first." in out
    assert "attachment body" not in out


def test_eml_falls_back_to_html_through_the_shared_converter():
    raw = b"Subject: S\r\nContent-Type: text/html\r\n\r\n<h1>Heading</h1><p>body text</p>\r\n"
    out = decode(raw, "mail.eml")
    assert "# Heading" in out and "body text" in out


# -- PDF --------------------------------------------------------------------


def test_pdf_extracts_the_text_layer_and_rejoins_hyphenated_breaks():
    out = decode(PDF, "doc.pdf")
    assert out is not None
    assert "Broker Runbook" in out
    assert "broker service" in out, "a line-break hyphen must not survive as a term"
    assert "SRE team" in out, "TJ arrays carry text too, not just Tj"


def test_pdf_without_a_text_layer_is_none_not_an_error():
    """The distinction the enrichment queue is built on: a scan is a real
    document that needs a model, not a failure.
    """
    scanned = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< >>\n%%EOF\n"
    assert decode(scanned, "scan.pdf") is None


def test_pdf_reads_an_uncompressed_content_stream():
    assert "Broker Runbook" in decode(_pdf(PDF and b"BT (Broker Runbook) Tj ET", compress=False), "d.pdf")


def test_a_file_that_is_not_a_pdf_is_not_guessed_at():
    assert decode(b"just text", "notreally.pdf") is None


# -- safety: bombs and entities ---------------------------------------------


def test_a_zip_bomb_is_refused_rather_than_inflated():
    bomb = zf({"word/document.xml": "A" * (80 * 1024 * 1024)})
    assert decode(bomb, "bomb.docx") is None


def test_a_doctype_is_refused_everywhere_xml_is_parsed():
    """One rule closes both billion-laughs and XXE. OOXML and ODF never declare
    a DOCTYPE, so the cost is a DTD-validated config file being skipped.
    """
    laughs = (
        b'<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY lol "lol">'
        b'<!ENTITY lol2 "&lol;&lol;&lol;">]><doc>&lol2;</doc>'
    )
    assert decode(laughs, "bomb.xml") is None
    assert decode(zf({"content.xml": laughs.decode()}), "bomb.odt") is None


def test_every_registered_extension_survives_garbage_without_raising():
    """A corrupt file among ten thousand must not end the run. Some decoders
    return None and some raise DecodeFailed; neither may be an uncaught error.
    """
    from fux.decode import DecodeFailed, registry

    for ext in sorted(registry()):
        try:
            decode(b"\x00\x01garbage\xff\xfe", "junk" + ext)
        except DecodeFailed:
            pass  # recorded as a skip by the caller


# -- determinism ------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,name",
    [
        (DOCX, "a.docx"),
        (PPTX, "a.pptx"),
        (XLSX, "a.xlsx"),
        (ODT, "a.odt"),
        (PDF, "a.pdf"),
        (DRAWIO, "a.drawio"),
        (b'{"b":"beta text here","a":"alpha text here"}', "a.json"),
        (b"one: first value\ntwo: second value\n", "a.yaml"),
    ],
)
def test_decoding_the_same_bytes_twice_gives_the_same_string(raw, name):
    assert decode(raw, name) == decode(raw, name)


def test_json_keys_are_emitted_sorted_not_in_document_order():
    """Two exports of the same data with keys in a different order must decode
    identically, or the index records which exporter ran (L3).
    """
    first = decode(b'{"alpha":"one text","beta":"two text"}', "a.json")
    second = decode(b'{"beta":"two text","alpha":"one text"}', "a.json")
    assert first == second


def test_zip_member_order_does_not_reach_the_output():
    forward = zf({"content.xml": ODT_CONTENT, "meta.xml": "<meta/>"})
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:  # reversed write order
        archive.writestr("meta.xml", "<meta/>")
        archive.writestr("content.xml", ODT_CONTENT)
    assert decode(forward, "a.odt") == decode(buf.getvalue(), "a.odt")


ODT_CONTENT = """<?xml version="1.0"?><office:document-content xmlns:office="urn:o"
 xmlns:text="urn:t"><office:body><office:text>
<text:p>Drain the queue first.</text:p></office:text></office:body></office:document-content>"""


# -- the noise rules that verdict G is about --------------------------------


def test_json_drops_ids_numbers_and_blobs_but_keeps_prose():
    raw = (
        b'{"description":"the broker runbook","count":42,'
        b'"id":"550e8400-e29b-41d4-a716-446655440000",'
        b'"hash":"deadbeefcafe","when":"2026-08-26T10:00:00Z"}'
    )
    out = decode(raw, "a.json")
    assert "the broker runbook" in out
    for noise in ("550e8400", "deadbeef", "2026-08-26", "42"):
        assert noise not in out


def test_yaml_does_not_expand_aliases():
    """A conformant parser expands `*a` everywhere, duplicating the anchored
    text and inflating `tf`. That is the one place full YAML is actively wrong
    for a ranking index.
    """
    raw = b"first: &a shared phrase here\nsecond: *a\nthird: *a\n"
    out = decode(raw, "a.yaml")
    assert out.count("shared phrase here") == 1


def test_yaml_block_scalars_are_dedented_by_their_own_indent():
    out = decode(b"notes: |\n    restart after draining\n    then verify\n", "a.yaml")
    assert "restart after draining\nthen verify" in out


def test_notebook_outputs_are_dropped_but_code_is_kept():
    """Outputs are re-execution artifacts: the same notebook run twice produces
    different ones, so indexing them makes the index depend on who hit Run.
    """
    raw = (
        b'{"cells":[{"cell_type":"markdown","source":["# Runbook\\n"]},'
        b'{"cell_type":"code","source":["drain_queue()"],'
        b'"outputs":[{"text":["EPHEMERAL OUTPUT"]}]}],'
        b'"metadata":{"language_info":{"name":"python"}}}'
    )
    out = decode(raw, "a.ipynb")
    assert "# Runbook" in out
    assert "drain_queue()" in out
    assert "EPHEMERAL" not in out


def test_csv_truncates_rather_than_indexing_a_dataset():
    rows = b"col\n" + b"".join(b"value %d\n" % i for i in range(900))
    out = decode(rows, "a.csv")
    assert "table truncated" in out


def test_properties_files_have_no_section_header_and_still_parse():
    out = decode(b"db.host=the primary database\ndb.port=5432\n", "app.properties")
    assert "the primary database" in out
