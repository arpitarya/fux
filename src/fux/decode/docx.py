"""`.docx` -> Markdown.

A Word document is `word/document.xml` inside a zip: paragraphs (`w:p`) carrying
runs (`w:r` / `w:t`), with the paragraph's style name in `w:pStyle`. Headings
are style names, not markup, which is why `_ooxml.heading_level` exists — and
why getting them out matters more here than anywhere else: a specification or a
runbook is *mostly* headings, and `extract.py` weights that field above body.
"""

from __future__ import annotations

# Imports are ABSOLUTE, not relative, and that is what makes this file work in
# both places it runs: as a package module, and as a consumer copy in
# `.fux/decoders/` loaded by path. A path-loaded file has no parent package, so
# `from . import _xml` raises `attempted relative import with no known parent
# package` — the copy would be dead on arrival. Absolute imports mean the file
# fux ships and the file you edit are byte-identical (ADR-DECODE decision 11).
from fux.decode import _ooxml, _xml
from fux.decode._zip import SafeZip, ZipTooBig

EXTENSIONS = (".docx", ".docm")

_DOCUMENT = "word/document.xml"


def decode(raw: bytes, rel_path: str) -> str | None:
    try:
        with SafeZip(raw) as archive:
            if not archive.has(_DOCUMENT):
                return None  # a .docx that is not a Word document, or is corrupt
            root = _xml.parse(archive.read(_DOCUMENT))
    except (ZipTooBig, _xml.UnsafeXml):
        return None

    blocks: list[str] = []
    for element in root.iter():
        tag = _xml.local(element.tag)
        if tag == "tbl":
            table = _table(element)
            if table:
                blocks.append(table)
        elif tag == "p" and not _inside_table(root, element):
            block = _paragraph(element)
            if block:
                blocks.append(block)
    body = "\n\n".join(blocks)
    return body if body.strip() else None


def _paragraph(element) -> str:
    text = _ooxml.paragraph_text(element)
    if not text:
        return ""
    level = _ooxml.heading_level(_style(element))
    if level:
        return "#" * level + " " + text
    if _is_list_item(element):
        return "- " + text
    return text


def _style(element) -> str | None:
    for node in element.iter():
        if _xml.local(node.tag) == "pStyle":
            for key, value in node.attrib.items():
                if _xml.local(key) == "val":
                    return value
    return None


def _is_list_item(element) -> bool:
    # `numPr` is Word's numbering-properties marker. The actual bullet glyph
    # and numbering live in `numbering.xml`; following that indirection would
    # buy a correct "1." instead of "-" and cost a second part read per
    # paragraph, which is not worth it for a ranking index.
    return any(_xml.local(node.tag) == "numPr" for node in element.iter())


def _table(element) -> str:
    rows: list[list[str]] = []
    for row in element.iter():
        if _xml.local(row.tag) != "tr":
            continue
        cells: list[str] = []
        for cell in row.iter():
            if _xml.local(cell.tag) != "tc":
                continue
            cells.append(
                " ".join(
                    _ooxml.paragraph_text(p)
                    for p in cell.iter()
                    if _xml.local(p.tag) == "p"
                ).strip()
            )
        rows.append(cells)
    return _ooxml.table_markdown(rows)


def _inside_table(root, target) -> bool:
    """Whether this paragraph is already covered by a table.

    Without this every cell's text appears twice — once in the table and once
    as a loose paragraph — which doubles those terms' `tf` and makes a
    table-heavy document rank as if it repeated itself.
    """
    for table in root.iter():
        if _xml.local(table.tag) != "tbl":
            continue
        for node in table.iter():
            if node is target:
                return True
    return False
