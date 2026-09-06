"""`.xlsx` -> Markdown, one table per sheet.

The awkward part of the format: **most cell text is not in the sheet.** Strings
live once in `xl/sharedStrings.xml` and each cell holds an index into it, so a
decoder that reads only the sheet parts finds numbers and nothing else. That
indirection is the single thing worth knowing about this file.

⚠ **Formulas are ignored; cached values are indexed.** A formula is not what a
human reads, and `=VLOOKUP(...)` as a term matches nothing anyone types.

⚠ **A spreadsheet is the format most likely to be pure numbers**, which is the
shape [ADR-TYPES](../../../docs/adr/0031_types-list.md) verdict G punished. A
consumer opting `.xlsx` in should know their sheets are mostly words.
"""

from __future__ import annotations

# Imports are ABSOLUTE, not relative, and that is what makes this file work in
# both places it runs: as a package module, and as a consumer copy in
# `.fux/decoders/` loaded by path. A path-loaded file has no parent package, so
# `from . import _xml` raises `attempted relative import with no known parent
# package` — the copy would be dead on arrival. Absolute imports mean the file
# fux ships and the file you edit are byte-identical (ADR-DECODE decision 11).
from fux.decode import _ooxml, _xml
from fux.decode._zip import SafeZip, ZipTooBig, numeric_key

EXTENSIONS = (".xlsx", ".xlsm")

_SHARED = "xl/sharedStrings.xml"
_SHEETS = "xl/worksheets/sheet"
_WORKBOOK = "xl/workbook.xml"

MAX_ROWS_PER_SHEET = 500
MAX_COLS = 40


def decode(raw: bytes, rel_path: str) -> str | None:
    try:
        with SafeZip(raw) as archive:
            shared = _shared_strings(archive)
            names = _sheet_names(archive)
            parts = sorted(archive.matching(_SHEETS, ".xml"), key=numeric_key)
            if not parts:
                return None
            blocks: list[str] = []
            for index, part in enumerate(parts):
                try:
                    root = _xml.parse(archive.read(part))
                except _xml.UnsafeXml:
                    continue
                rows = _rows(root, shared)
                table = _ooxml.table_markdown(rows)
                if not table:
                    continue
                title = names[index] if index < len(names) else f"Sheet {index + 1}"
                blocks.append(f"## {title}")
                blocks.append(table)
    except ZipTooBig:
        return None

    body = "\n\n".join(blocks)
    return body if body.strip() else None


def _shared_strings(archive: SafeZip) -> list[str]:
    if not archive.has(_SHARED):
        return []
    try:
        root = _xml.parse(archive.read(_SHARED))
    except _xml.UnsafeXml:
        return []
    # `si` elements are positional — index order IS the contract, so this is the
    # one list in the plane that must NOT be sorted.
    return [
        _xml.text_of(si) for si in root if _xml.local(si.tag) == "si"
    ]


def _sheet_names(archive: SafeZip) -> list[str]:
    if not archive.has(_WORKBOOK):
        return []
    try:
        root = _xml.parse(archive.read(_WORKBOOK))
    except _xml.UnsafeXml:
        return []
    names: list[str] = []
    for node in root.iter():
        if _xml.local(node.tag) != "sheet":
            continue
        for key, value in node.attrib.items():
            if _xml.local(key) == "name":
                names.append(value)
    return names


def _rows(root, shared: list[str]) -> list[list[str]]:
    out: list[list[str]] = []
    for row in root.iter():
        if _xml.local(row.tag) != "row":
            continue
        cells: list[str] = []
        for cell in row:
            if _xml.local(cell.tag) != "c":
                continue
            cells.append(_cell(cell, shared))
            if len(cells) >= MAX_COLS:
                break
        out.append(cells)
        if len(out) >= MAX_ROWS_PER_SHEET:
            break
    return out


def _cell(cell, shared: list[str]) -> str:
    kind = None
    for key, value in cell.attrib.items():
        if _xml.local(key) == "t":
            kind = value
    value_node = None
    inline = None
    for child in cell:
        tag = _xml.local(child.tag)
        if tag == "v":
            value_node = child
        elif tag == "is":  # an inline string, used when sharing is disabled
            inline = child
    if inline is not None:
        return _xml.text_of(inline)
    if value_node is None or value_node.text is None:
        return ""
    text = value_node.text.strip()
    if kind == "s":  # an index into sharedStrings
        try:
            return shared[int(text)]
        except (ValueError, IndexError):
            return ""
    if kind == "str":  # a formula's cached string result
        return text
    return text
