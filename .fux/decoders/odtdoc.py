"""OpenDocument text, spreadsheet and presentation -> Markdown.

**One module for all three, and that is the exception to one-module-per-format.**
ODF puts every kind of document in the same `content.xml` with the same
`text:h` / `text:p` / `table:table` elements — a `.odt` and a `.ods` differ in
which of those appear, not in how they are read. Splitting them would give a
consumer three files to override to change one behaviour, which is the opposite
of what the override seam is for.

OOXML needed three modules because Word, PowerPoint and Excel genuinely store
text three different ways: styles, slide parts, and a shared-string table.
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

EXTENSIONS = (".odt", ".ods", ".odp", ".fodt")

_CONTENT = "content.xml"


def _text(element) -> str:
    """One ODF paragraph's text.

    ⚠ **Not `_ooxml.paragraph_text`.** OOXML nests every fragment in a `<w:t>`
    or `<a:t>` run element; ODF puts the text directly on `text:p` and only
    wraps it when a span carries formatting. Reusing the OOXML walker here
    returned the empty string for every plain paragraph — a whole format
    decoding to nothing, with no error anywhere.
    """
    return _xml.text_of(element)


def decode(raw: bytes, rel_path: str) -> str | None:
    try:
        with SafeZip(raw) as archive:
            if not archive.has(_CONTENT):
                return None
            root = _xml.parse(archive.read(_CONTENT))
    except (ZipTooBig, _xml.UnsafeXml):
        return None

    blocks: list[str] = []
    seen: set[int] = set()
    for element in root.iter():
        tag = _xml.local(element.tag)
        if tag == "table":
            table = _table(element, seen)
            if table:
                blocks.append(table)
        elif tag == "h" and id(element) not in seen:
            text = _text(element)
            if text:
                blocks.append("#" * _level(element) + " " + text)
        elif tag == "p" and id(element) not in seen:
            text = _text(element)
            if text:
                blocks.append(text)
    body = "\n\n".join(blocks)
    return body if body.strip() else None


def _level(element) -> int:
    """`text:outline-level` -> a heading level.

    ODF states the level as an attribute rather than through a named style, so
    unlike OOXML there is no styles part to consult and no name to pattern-match
    — the document says what it means.
    """
    for key, value in element.attrib.items():
        if _xml.local(key) == "outline-level":
            try:
                return max(1, min(int(value), 6))
            except ValueError:
                return 2
    return 2


def _table(element, seen: set[int]) -> str:
    """A table, marking its paragraphs so the main walk does not repeat them.

    Same defect `docxdoc` guards against: without this, every cell's text is
    emitted twice and its `tf` doubles.
    """
    rows: list[list[str]] = []
    for row in element.iter():
        if _xml.local(row.tag) != "table-row":
            continue
        cells: list[str] = []
        for cell in row.iter():
            if _xml.local(cell.tag) != "table-cell":
                continue
            texts: list[str] = []
            for node in cell.iter():
                if _xml.local(node.tag) in ("p", "h"):
                    seen.add(id(node))
                    text = _text(node)
                    if text:
                        texts.append(text)
            cells.append(" ".join(texts))
        rows.append(cells)
    return _ooxml.table_markdown(rows)
