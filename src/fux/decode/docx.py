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
# fux ships and the file you edit are byte-identical (SR-DECODE decision 11).
from fux.decode.ext import ooxml as _ooxml, table as _table, xml as _xml
from fux.decode.ext.zip import SafeZip, ZipTooBig
from fux.constants import fixed

#: **The reuse key's handle on this decoder** (W-166). Bump it by hand in the
#: same change as any edit that can change what `decode()` returns, and the next
#: `fux ingest` re-extracts the documents bound to THIS decoder and no others.
#: Leaving it alone is the claim that the edit cannot move a byte of output.
#: `tests/decode/test_decoder_versions.py` fails on a changed module that did
#: not bump it. [SR-DECODE](../../../records/0139_decode.md) decision 11a.
VERSION = fixed("decoders.docx", "version")  # 2 (W-287 A3): gridSpan/vMerge expanded, nested tables flattened once; not bumped by W-288 (imports moved to decode/ext, same output; USES now carries the extensions' VERSIONs)

EXTENSIONS = tuple(fixed("decoders.docx", "extensions"))
#: The decoder extensions this decoder calls, read by the reuse key (SR-DECODE decision 24).
USES = tuple(fixed("decoders.docx", "uses"))

#: The part ECMA-376 names -- `constants.toml [decoders.docx.format]` (R13).
_DOCUMENT = fixed("decoders.docx.format", "document")


def decode(raw: bytes, rel_path: str) -> str | None:
    try:
        with SafeZip(raw) as archive:
            if not archive.has(_DOCUMENT):
                return None  # a .docx that is not a Word document, or is corrupt
            root = _xml.parse(archive.read(_DOCUMENT))
    except (ZipTooBig, _xml.UnsafeXml):
        return None

    # A table nested in a cell is read as part of that cell's text (W-287 A3);
    # walking it again here emitted every nested table a second time.
    nested = {
        id(inner)
        for outer in root.iter()
        if _xml.local(outer.tag) == "tbl"
        for inner in outer.iter()
        if inner is not outer and _xml.local(inner.tag) == "tbl"
    }
    blocks: list[str] = []
    for element in root.iter():
        tag = _xml.local(element.tag)
        if tag == "tbl" and id(element) in nested:
            continue
        if tag == "tbl":
            table = _table_of(element)
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


def _table_of(element) -> str:
    """A `w:tbl` -> a Markdown table, every cell under its TRUE grid column.

    W-287 A3: the table becomes a `_table.Grid` and `_table.emit` writes it. A
    cell spanning columns (`w:gridSpan`) is a span across them, and a vertical
    merge (`w:vMerge`: `restart`, then cells that continue it) is ONE span down
    the column — Word stores the continuing cells empty, so reading them as
    written put a blank under a column whose value sits one row up.
    `w:gridBefore` shifts a row right. Rows and cells are this table's OWN: a
    nested table's rows are not this table's rows, and its text joins the cell
    it sits in. The first row is the header, as Word's tables are written.
    """
    grid = _table.Grid(header=(0,))
    open_merges: dict[int, tuple[int, int, int, int]] = {}  # start column -> (row0, col0, row1, col1)
    for r, row in enumerate(_own(element, "tr")):
        col = _val(row, "gridBefore", 0)
        continued: set[int] = set()
        for cell in _own(row, "tc"):
            span = max(1, _val(cell, "gridSpan", 1))
            merge = _vmerge(cell)
            if merge == "continue" and col in open_merges:
                row0, col0, _row1, col1 = open_merges[col]
                open_merges[col] = (row0, col0, r, col1)
                continued.add(col)
            else:
                if col in open_merges:  # a new cell where a merge was open ends it
                    grid.spans.append(open_merges.pop(col))
                text = " ".join(
                    _ooxml.paragraph_text(p) for p in cell.iter() if _xml.local(p.tag) == "p"
                ).strip()
                grid.cells[(r, col)] = _table.Cell(text, "text")
                if merge == "restart":
                    open_merges[col] = (r, col, r, col + span - 1)
                    continued.add(col)
                elif span > 1:
                    grid.spans.append((r, col, r, col + span - 1))
            col += span
        for start in [c for c in open_merges if c not in continued]:
            grid.spans.append(open_merges.pop(start))
    grid.spans.extend(open_merges.values())
    return _table.emit(grid, header_fill_percent=None, row_limit=None, max_cell_chars=None).markdown


def _own(element, tag: str):
    """`element`'s `tag` descendants that belong to it — through wrappers such as
    `w:sdt`, never into a nested `w:tbl`, and never into a match's own subtree."""
    for child in element:
        name = _xml.local(child.tag)
        if name == tag:
            yield child
        elif name != "tbl":
            yield from _own(child, tag)


def _props(element):
    """The `w:trPr` / `w:tcPr` child of a row or cell, or `None`."""
    for child in element:
        if _xml.local(child.tag) in ("trPr", "tcPr"):
            return child
    return None


def _val(element, name: str, default: int) -> int:
    """An integer `w:val` of the named property (`gridSpan`, `gridBefore`)."""
    props = _props(element)
    if props is None:
        return default
    for node in props:
        if _xml.local(node.tag) != name:
            continue
        for key, value in node.attrib.items():
            if _xml.local(key) == "val":
                try:
                    return int(value)
                except ValueError:
                    return default
    return default


def _vmerge(cell) -> str | None:
    """`"restart"`, `"continue"` or `None` — a cell's place in a vertical merge:
    `w:vMerge` with `w:val="restart"` starts one, and with its `w:val` absent or
    `continue` carries it on (ECMA-376 §17.4.85)."""
    props = _props(cell)
    if props is None:
        return None
    for node in props:
        if _xml.local(node.tag) != "vMerge":
            continue
        values = [v for k, v in node.attrib.items() if _xml.local(k) == "val"]
        return "restart" if values and values[0] == "restart" else "continue"
    return None


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
