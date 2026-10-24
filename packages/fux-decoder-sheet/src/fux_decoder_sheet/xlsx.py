"""`.xlsx` -> Markdown, one table per sheet.

The awkward part of the format: **most cell text is not in the sheet.** Strings
live once in `xl/sharedStrings.xml` and each cell holds an index into it, so a
decoder that reads only the sheet parts finds numbers and nothing else. That
indirection is the single thing worth knowing about this file.

⚠ **Formulas are ignored; cached values are indexed.** A formula is not what a
human reads, and `=VLOOKUP(...)` as a term matches nothing anyone types.

⚠ **A cell's position is its ADDRESS, never its place in the XML** (W-287 A1).
Excel omits an empty cell entirely, so a row whose second cell is blank stores
two `<c>` elements, and appending them in order put the third column's value
under the second column's name. Each cell carries `r="C7"`; that is where it
goes. A date is a number with a date FORMAT (`styles.xml`), so reading the
number alone indexed `46214` where a human reads `2026-07-11`.

⚠ **A spreadsheet is the format most likely to be pure numbers**, which is the
shape [SR-TYPES](../../../../records/0128_types-list.md) verdict G punished. A
consumer opting `.xlsx` in should know their sheets are mostly words.
"""

from __future__ import annotations

# Imports are ABSOLUTE, not relative, and that is what makes this file work in
# both places it runs: as a package module, and as a consumer copy in
# `.fux/decoders/` loaded by path. A path-loaded file has no parent package, so
# `from . import _xml` raises `attempted relative import with no known parent
# package` — the copy would be dead on arrival. Absolute imports mean the file
# fux ships and the file you edit are byte-identical (SR-DECODE decision 11).
import re

from fux.decode.ext import xml as _xml
from fux_extension_table import table as _table
from fux.decode.ext.zip import SafeZip, ZipTooBig, numeric_key
from fux.constants import fixed

#: **The reuse key's handle on this decoder** (W-166). Bump it by hand in the
#: same change as any edit that can change what `decode()` returns, and the next
#: `fux ingest` re-extracts the documents bound to THIS decoder and no others.
#: Leaving it alone is the claim that the edit cannot move a byte of output.
#: `tests/decode/test_decoder_versions.py` fails on a changed module that did
#: not bump it. [SR-DECODE](../../../../records/0139_decode.md) decision 11a.
VERSION = fixed("decoders.xlsx", "version")  # 3 (W-287 A1/A4): cells by address, number formats, merges, header detection; not bumped by W-288 (imports moved to decode/ext, same output; USES now carries the extensions' VERSIONs)

EXTENSIONS = tuple(fixed("decoders.xlsx", "extensions"))
#: The decoder extensions this decoder calls, read by the reuse key (SR-DECODE decision 24).
USES = tuple(fixed("decoders.xlsx", "uses"))

#: The parts ECMA-376 names -- `constants.toml [decoders.xlsx.format]` (R13).
_SHARED = fixed("decoders.xlsx.format", "shared")
_SHEETS = fixed("decoders.xlsx.format", "sheets")
_WORKBOOK = fixed("decoders.xlsx.format", "workbook")
_STYLES = fixed("decoders.xlsx.format", "styles")

#: W-287 A1 — the built-in number formats ECMA-376 defines as dates and times
#: (`constants.toml [decoders.xlsx.format]`); `_table` writes the dates.
_DATE_IDS = frozenset(fixed("decoders.xlsx.format", "date_formats"))
_TIME_IDS = frozenset(fixed("decoders.xlsx.format", "time_formats"))
_DATETIME_IDS = frozenset(fixed("decoders.xlsx.format", "datetime_formats"))

#: A cell reference's two halves: `AB12` -> `AB`, `12`.
_REF_RE = re.compile(r"^\$?([A-Za-z]+)\$?([0-9]+)$")
#: What a custom format code shows, once its literals are gone: a quoted string,
#: a backslash-escaped character, and a `[...]` section (a colour, a locale, a
#: condition) are text, never a date token.
_FORMAT_LITERAL_RE = re.compile(r'"[^"]*"|\\.|\[[^\]]*\]')

#: Per SHEET, not per workbook — a five-sheet workbook admits the limit five
#: times, because a sheet is the document's own division and truncating the
#: fifth because the first four were long would be arbitrary.
#: Was a hard-coded 500; now `.fux/config/tune.toml [index] max_table_rows` (see `csv.py` for the
#: data-loss this hid).
from fux.decode.ext.limits import limit, max_table_rows

#: ⚠ **`MAX_COLS` is `[limits.xlsx] max_cols` in .fux/config/formats.toml** since W-225 stage 4a
#: (SR-LAW-12 decision 9b): read per call through `limit()`, in the extract-config digest.


def decode(raw: bytes, rel_path: str) -> str | None:
    try:
        with SafeZip(raw) as archive:
            shared = _shared_strings(archive)
            names = _sheet_names(archive)
            date1904 = _date1904(archive)
            formats = _cell_formats(archive)
            parts = sorted(archive.matching(_SHEETS, ".xml"), key=numeric_key)
            if not parts:
                return None
            blocks: list[str] = []
            for index, part in enumerate(parts):
                try:
                    root = _xml.parse(archive.read(part))
                except _xml.UnsafeXml:
                    continue
                grid, dropped_cols = _grid(root, shared, formats, date1904)
                table = _table.emit(
                    grid,
                    header_fill_percent=limit("xlsx", "header_fill_percent"),
                    row_limit=max_table_rows(),
                    max_cell_chars=None,
                )
                if not table.markdown:
                    continue
                truncated = table.truncated
                title = names[index] if index < len(names) else f"Sheet {index + 1}"
                blocks.append(f"## {title}")
                if table.prose:
                    # W-287 A4: a title banner above the header is the sheet's
                    # prose, not a row — its words are not anyone's column name.
                    blocks.append("\n".join(table.prose))
                blocks.append(table.markdown)
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
                    notices.append(f"columns past {limit('xlsx', 'max_cols')} dropped")
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


def _date1904(archive: SafeZip) -> bool:
    """Whether the workbook counts dates from 1904 (`workbookPr date1904`)."""
    if not archive.has(_WORKBOOK):
        return False
    try:
        root = _xml.parse(archive.read(_WORKBOOK))
    except _xml.UnsafeXml:
        return False
    for node in root.iter():
        if _xml.local(node.tag) == "workbookPr":
            for key, value in node.attrib.items():
                if _xml.local(key) == "date1904":
                    return value.strip().lower() in ("1", "true")
    return False


def _cell_formats(archive: SafeZip) -> list[str]:
    """`cellXfs` index -> `"date"`, `"time"`, `"datetime"` or `""` (W-287 A1).

    A cell's `s="3"` is an index into `cellXfs`, whose `numFmtId` is either a
    built-in id or one of the workbook's own `numFmt` codes. ⚠ `cellStyleXfs`
    holds `xf` elements too, and they are NOT what `s` indexes — only the
    children of `cellXfs` are read.
    """
    if not archive.has(_STYLES):
        return []
    try:
        root = _xml.parse(archive.read(_STYLES))
    except _xml.UnsafeXml:
        return []
    codes: dict[int, str] = {}
    out: list[str] = []
    for node in root:
        tag = _xml.local(node.tag)
        if tag == "numFmts":
            for fmt in node:
                attrs = {_xml.local(k): v for k, v in fmt.attrib.items()}
                try:
                    codes[int(attrs.get("numFmtId", ""))] = attrs.get("formatCode", "")
                except ValueError:
                    continue
        elif tag == "cellXfs":
            for xf in node:
                if _xml.local(xf.tag) != "xf":
                    continue
                attrs = {_xml.local(k): v for k, v in xf.attrib.items()}
                try:
                    fmt_id = int(attrs["numFmtId"])
                except (KeyError, ValueError):
                    out.append("")  # no format: General, a plain number
                    continue
                out.append(_format_kind(fmt_id, codes.get(fmt_id)))
    return out


def _format_kind(fmt_id: int, code: str | None) -> str:
    """A number format -> what it displays: a date, a time, both, or a number."""
    if code is None:
        if fmt_id in _DATE_IDS:
            return "date"
        if fmt_id in _TIME_IDS:
            return "time"
        if fmt_id in _DATETIME_IDS:
            return "datetime"
        return ""
    # Only the first section: `0.00;[Red]-0.00` is one format for two signs.
    shown = _FORMAT_LITERAL_RE.sub("", code.split(";", 1)[0]).lower()
    has_time = "h" in shown or "s" in shown
    # `m` is a month on its own or beside `y`/`d`, and a minute beside `h`/`s`.
    has_date = "y" in shown or "d" in shown or ("m" in shown and not has_time)
    if has_date and has_time:
        return "datetime"
    if has_date:
        return "date"
    if has_time:
        return "time"
    return ""


def _column(ref: str) -> tuple[int, int] | None:
    """`"C7"` -> `(column 2, row 7)` — 0-based column, 1-based row."""
    match = _REF_RE.match(ref.strip())
    if not match:
        return None
    letters, digits = match.groups()
    col = 0
    for ch in letters.upper():  # bijective base 26: A=1 .. Z=26, AA=27
        col = col * 26 + (ord(ch) - ord("A") + 1)
    return col - 1, int(digits)


def _grid(root, shared: list[str], formats: list[str], date1904: bool) -> tuple[_table.Grid, bool]:
    """`(grid, dropped_cols)` — one sheet as `_table` takes it (W-287 A1).

    A cell is placed by its `r=` address, so a gap is an empty cell rather than
    the next column's value shifted left; its `kind` comes from `t=` and its
    style's number format; a `mergeCell` is a span. Everything after that —
    writing the value, expanding the span, finding the header, the row budget —
    is `_table.emit`'s, once for every format.

    ⚠ **A BLANK ROW DOES NOT SPEND THE BUDGET** (SR-TABULAR decision 7): a row
    with no filled cell never reaches the table at all. Rows are numbered by
    their `r=`, so a merge's span is in the sheet's own coordinates.
    """
    max_cols = limit("xlsx", "max_cols")
    dropped_cols = False
    grid = _table.Grid(date1904=date1904)
    previous_row = 0
    for node in root.iter():
        tag = _xml.local(node.tag)
        if tag == "mergeCell":
            span = _merge(node)
            if span is not None:
                r0, c0, r1, c1 = span
                if c0 < max_cols:
                    grid.spans.append((r0, c0, r1, min(c1, max_cols - 1)))
            continue
        if tag != "row":
            continue
        number = previous_row + 1
        for key, value in node.attrib.items():
            if _xml.local(key) == "r" and value.strip().isdigit():
                number = int(value)
        previous_row = number
        col = -1
        for cell in node:
            if _xml.local(cell.tag) != "c":
                continue
            col += 1
            for key, value in cell.attrib.items():
                if _xml.local(key) == "r":
                    placed = _column(value)
                    if placed is not None:
                        col = placed[0]
            if col >= max_cols:
                dropped_cols = True
                continue
            grid.cells[(number, col)] = _cell(cell, shared, formats)
    return grid, dropped_cols


def _merge(node) -> tuple[int, int, int, int] | None:
    """`<mergeCell ref="A1:C3"/>` -> `(row0, col0, row1, col1)`, inclusive."""
    for key, value in node.attrib.items():
        if _xml.local(key) != "ref" or ":" not in value:
            continue
        first, _, last = value.partition(":")
        a, b = _column(first), _column(last)
        if a is None or b is None:
            return None
        return min(a[1], b[1]), min(a[0], b[0]), max(a[1], b[1]), max(a[0], b[0])
    return None


def _cell(cell, shared: list[str], formats: list[str]) -> _table.Cell:
    """One `<c>` as `(text, kind)`: what the sheet holds, not yet how it is written."""
    kind = None
    style = 0
    for key, value in cell.attrib.items():
        name = _xml.local(key)
        if name == "t":
            kind = value
        elif name == "s":
            try:
                style = int(value)
            except ValueError:
                style = 0
    value_node = None
    inline = None
    for child in cell:
        tag = _xml.local(child.tag)
        if tag == "v":
            value_node = child
        elif tag == "is":  # an inline string, used when sharing is disabled
            inline = child
    if inline is not None:
        return _table.Cell(_xml.text_of(inline), "text")
    if value_node is None or value_node.text is None:
        return _table.Cell("", "text")
    text = value_node.text.strip()
    if kind == "s":  # an index into sharedStrings
        try:
            return _table.Cell(shared[int(text)], "text")
        except (ValueError, IndexError):
            return _table.Cell("", "text")
    if kind in ("str", "e"):  # a formula's cached string, or an error such as #N/A
        return _table.Cell(text, "text")
    if kind == "b":  # W-287 A1: a boolean is a word, not a digit
        return _table.Cell(text, "bool")
    if kind == "d":  # an ISO-8601 date (strict OOXML); its midnight says nothing
        return _table.Cell(text[: -len("T00:00:00")] if text.endswith("T00:00:00") else text, "text")
    shown = formats[style] if 0 <= style < len(formats) else ""
    return _table.Cell(text, shown or "number")
