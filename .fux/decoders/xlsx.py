"""`.xlsx` -> Markdown, one table per sheet.

The awkward part of the format: **most cell text is not in the sheet.** Strings
live once in `xl/sharedStrings.xml` and each cell holds an index into it, so a
decoder that reads only the sheet parts finds numbers and nothing else. That
indirection is the single thing worth knowing about this file.

⚠ **Formulas are ignored; cached values are indexed.** A formula is not what a
human reads, and `=VLOOKUP(...)` as a term matches nothing anyone types.

⚠ **A spreadsheet is the format most likely to be pure numbers**, which is the
shape [SR-TYPES](../../../records/0128_types-list.md) verdict G punished. A
consumer opting `.xlsx` in should know their sheets are mostly words.
"""

from __future__ import annotations

# Imports are ABSOLUTE, not relative, and that is what makes this file work in
# both places it runs: as a package module, and as a consumer copy in
# `.fux/decoders/` loaded by path. A path-loaded file has no parent package, so
# `from . import _xml` raises `attempted relative import with no known parent
# package` — the copy would be dead on arrival. Absolute imports mean the file
# fux ships and the file you edit are byte-identical (SR-DECODE decision 11).
from fux.decode import _ooxml, _xml
from fux.decode._zip import SafeZip, ZipTooBig, numeric_key

EXTENSIONS = (".xlsx", ".xlsm")

_SHARED = "xl/sharedStrings.xml"
_SHEETS = "xl/worksheets/sheet"
_WORKBOOK = "xl/workbook.xml"

#: Per SHEET, not per workbook — a five-sheet workbook admits the limit five
#: times, because a sheet is the document's own division and truncating the
#: fifth because the first four were long would be arbitrary.
#: Was a hard-coded 500; now `.fux/tune.toml [index] max_table_rows` (see `csv.py` for the
#: data-loss this hid).
from fux.decode._limits import max_table_rows

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
                limit = max_table_rows()
                rows, truncated, dropped_cols = _rows(root, shared, limit + 1)
                table = _ooxml.table_markdown(rows)
                if not table:
                    continue
                title = names[index] if index < len(names) else f"Sheet {index + 1}"
                blocks.append(f"## {title}")
                blocks.append(table)
                # ⚠ **Said in the document, exactly as `csv.py` says it.** Both
                # files are SR-TABULAR's, the record exists to close silent
                # tabular data loss, and until now only one of them did it: an
                # `.xlsx` truncated at `max_table_rows` or at `MAX_COLS` left
                # NO trace at all, in the index or on the page.
                notices = []
                if truncated:
                    notices.append("table truncated")
                if dropped_cols:
                    # A count here, unlike the row case, because a sheet's width
                    # is a property of the sheet rather than of how much of it
                    # was read -- it does not move as the file grows.
                    notices.append(f"columns past {MAX_COLS} dropped")
                if notices:
                    blocks.append("*(" + "; ".join(notices) + ")*")
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


def _rows(root, shared: list[str], limit: int) -> tuple[list[list[str]], bool, bool]:
    """`(rows, truncated, dropped_cols)`.

    `limit` counts the header too — the caller adds one, so the number a
    consumer writes in `.fux/tune.toml` is the number of DATA rows they get.

    ⚠ **A BLANK ROW DOES NOT SPEND THE BUDGET, and it used to.** Every `<row>`
    element was appended and counted, blank ones included — and a sheet carries
    a phantom blank row for any row that was ever styled, which is most of them
    on a maintained tracker. So a sheet with interleaved phantom rows stopped
    at `max_table_rows` **elements** and delivered roughly HALF that many
    records, while the docstring above promised records. `table_markdown` then
    dropped the blanks, leaving no evidence that anything had been skipped.

    `csv.py` never had this: it filters empty rows *before* applying the limit
    (`rows = [r for r in rows if any(cell.strip() …)]`). Two files, one record,
    one of them right — the divergence is the defect, not a difference of
    opinion.
    """
    out: list[list[str]] = []
    truncated = False
    dropped_cols = False
    for row in root.iter():
        if _xml.local(row.tag) != "row":
            continue
        cells: list[str] = []
        for cell in row:
            if _xml.local(cell.tag) != "c":
                continue
            if len(cells) >= MAX_COLS:
                dropped_cols = True
                break
            cells.append(_cell(cell, shared))
        if not any(cell.strip() for cell in cells):
            continue  # a phantom row: no content, so it buys no budget
        out.append(cells)
        # ⚠ **One row PAST the budget is what proves a tail exists.** Stopping
        # AT the budget cannot tell "exactly filled" from "more remained", and
        # a sheet that exactly fits then claimed a truncation that never
        # happened. `csv.py` never had to solve this — it reads every row and
        # compares (`len(rows) > limit + 1`); streaming one further and
        # discarding it buys the same answer for one row of work.
        if len(out) > limit:
            truncated = True
            out.pop()
            break
    return out, truncated, dropped_cols


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
