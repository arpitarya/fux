"""The one table module — every table format becomes Markdown HERE (W-287 stage A).

**Arpit, 2026-10-19 (Cowork):** *"how about we build 1 decoder just for table
and internally html, docs and xlsx use the same?"* So `xlsx.py`, `html.py`,
`docx.py` and `csv.py` are PARSERS: each turns its format into a `Grid` of
placed cells and spans, and `emit()` does everything after that, once:

    Grid  ->  values  ->  spans  ->  header  ->  limits  ->  Markdown

Before this, three copies of the emitter (`_ooxml.table_markdown`,
`html.py::_emit_table`, `csv.py`'s own loop) each made their own choices, and
SR-TABULAR decision 7's phantom-row defect was exactly *"two files, one record,
one of them right."* One emitter cannot disagree with itself.

**A decoder extension, not a decoder** (W-288, SR-DECODE decision 24): no
suffix, never chosen by the registry. Its `VERSION` rides in the reuse key of
every decoder whose `USES` names `table` — `csv`, `docx`, `html`, `xlsx`, and
`drawio` and `mail` through `html` — so a change here that can move a byte of
output bumps `constants.toml [extensions.table] version`, and nothing else.
[SR-TABULAR](../../../../records/0150_tabular.md) owns this file.

**What `emit()` decides, in order:**

1. **values** — a cell's `kind` says what the source holds; the text is written
   as a person writes it: a date `2026-07-11`, a time `14:30`, both
   `2026-07-11 14:30`, a boolean `true`/`false`, a number its shortest decimal.
   Whitespace collapses; a caller's `max_cell_chars` caps the length.
2. **spans** — a merged region (`mergeCells`, `colspan`/`rowspan`, `gridSpan`/
   `vMerge`) repeats its anchor's value into every cell it covers, in the rows
   the table holds.
3. **header** — declared header rows win (`<thead>`, a run of `<th>` rows; several
   combine per column: `Q1` over `Revenue` reads `Q1 Revenue`). Otherwise, when
   the caller passes `header_fill_percent`, the first row whose SOURCE-filled
   cells reach that share of the width — rows above it are prose (a title
   banner). Otherwise the first row. *Source-filled*: a banner merged across five
   columns filled one cell, not five.

   ⚠ **The threshold is a decoder cap, `[limits.<decoder>] header_fill_percent`,
   not an `[index]` key** — it moves no committed index byte (the index is a bag
   of terms, and a banner's words are the same body terms either way), which
   SR-TUNE decision 1's rule says keeps it out of `[index]`. It changes which
   words a ROW PASSAGE repeats as its column names. SR-TABULAR decision 8.
4. **limits** — `row_limit` counts DATA rows below the header; a blank row
   spends nothing because a blank row never reaches here.
5. **Markdown** — a column empty in every row (header included) is dropped: it
   names nothing and holds nothing. Short rows pad; `|` is escaped. Edge pipes
   and a separator row: exactly what `text/chunk.py::_table_bands` parses back,
   which `tests/decode/test_tables.py` proves per format (the round-trip gate).

Imports are absolute: a consumer copy of a decoder in `.fux/decoders/` loads by
path and has no parent package (SR-DECODE decision 11).
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field

from fux.constants import fixed

#: This decoder extension's version. It rides in the reuse key of every decoder
#: whose `USES` names it (SR-DECODE decision 24), so bump it — in
#: `constants.toml [extensions.table]` — when an edit can change what a decoder
#: using it RETURNS. `tests/decode/test_decoder_versions.py` fails on a changed
#: extension whose `VERSION` line the diff did not touch.
VERSION = fixed("extensions.table", "version")

__all__ = ["Cell", "Grid", "Table", "emit"]

_PERCENT = fixed("radix", "percent")
_EPOCH_1900 = _dt.date.fromisoformat(fixed("decoders.xlsx.format", "epoch_1900"))
_EPOCH_1900_EARLY = _dt.date.fromisoformat(fixed("decoders.xlsx.format", "epoch_1900_early"))
_EPOCH_1904 = _dt.date.fromisoformat(fixed("decoders.xlsx.format", "epoch_1904"))
_PHANTOM_LEAP_DAY = fixed("decoders.xlsx.format", "phantom_leap_day")
_SECONDS_PER_DAY = fixed("decoders.xlsx.format", "seconds_per_day")


@dataclass(frozen=True)
class Cell:
    """One source cell: its text as the source wrote it, and what it IS.

    `kind` is `text`, `number`, `bool`, `date`, `time` or `datetime`. The parser
    says what a value is; `emit()` decides how it is written. A date-kinded
    cell's text is a serial day number (the spreadsheet convention)."""

    text: str
    kind: str


@dataclass
class Grid:
    """A table as the source laid it out: cells at `(row, col)`, 0-based in the
    source's own order, sparse; and the merged regions."""

    cells: dict[tuple[int, int], Cell] = field(default_factory=dict)
    #: `(row0, col0, row1, col1)`, inclusive; the anchor is `(row0, col0)`.
    spans: list[tuple[int, int, int, int]] = field(default_factory=list)
    #: Rows the source DECLARED as header (`<thead>`, a run of `<th>`).
    header: tuple[int, ...] = ()
    #: The workbook counts serial dates from 1904 (`workbookPr date1904`).
    date1904: bool = False


@dataclass(frozen=True)
class Table:
    """What `emit()` returns: pre-header prose lines, the Markdown table (`""`
    when nothing was left), and whether `row_limit` cut a tail."""

    prose: tuple[str, ...]
    markdown: str
    truncated: bool


def emit(
    grid: Grid,
    *,
    header_fill_percent: int | None,
    row_limit: int | None,
    max_cell_chars: int | None,
) -> Table:
    """A `Grid` -> its prose and its Markdown table — the module docstring's five steps."""
    rows: dict[int, dict[int, str]] = {}
    for (r, c), cell in sorted(grid.cells.items()):
        text = _value(cell, grid.date1904, max_cell_chars)
        if text:
            rows.setdefault(r, {})[c] = text
    if not rows:
        return Table((), "", False)
    numbers = sorted(rows)
    filled = {r: len(rows[r]) for r in numbers}
    source = {r: dict(rows[r]) for r in numbers}
    for r0, c0, r1, c1 in sorted(grid.spans):
        anchor = rows.get(r0, {}).get(c0)
        if anchor is None:
            continue
        for r in numbers:
            if r0 <= r <= r1:
                for c in range(c0, c1 + 1):
                    rows[r].setdefault(c, anchor)
    width = max(max(cells) + 1 for cells in rows.values())
    expanded = {r: [rows[r].get(c, "") for c in range(width)] for r in numbers}

    declared = set(grid.header)
    prose: list[str] = []
    if declared & set(numbers):
        header = _combine([expanded[r] for r in numbers if r in declared])
        body = [expanded[r] for r in numbers if r not in declared]
    else:
        at = 0
        if header_fill_percent is not None:
            at = _header_index([filled[r] for r in numbers], width, header_fill_percent)
        prose = [" ".join(source[r][c] for c in sorted(source[r])) for r in numbers[:at]]
        header = expanded[numbers[at]]
        body = [expanded[r] for r in numbers[at + 1 :]]

    truncated = row_limit is not None and len(body) > row_limit
    if truncated:
        body = body[:row_limit]
    return Table(tuple(prose), _markdown(_drop_empty_columns([header, *body])), truncated)


def _value(cell: Cell, date1904: bool, max_cell_chars: int | None) -> str:
    if cell.kind in ("date", "time", "datetime"):
        text = _serial(cell.text, cell.kind, date1904)
    elif cell.kind == "number":
        text = _number(cell.text)
    elif cell.kind == "bool":
        text = {"1": "true", "0": "false"}.get(cell.text.strip(), cell.text)
    else:
        text = cell.text
    text = " ".join(text.split())
    return text[:max_cell_chars] if max_cell_chars is not None else text


def _number(text: str) -> str:
    """A number as its shortest decimal: `3`, never `3.0`; `0.1`, never `1.0E-1`."""
    text = text.strip()
    try:
        return str(int(text))
    except ValueError:
        pass
    try:
        value = float(text)
    except ValueError:
        return text
    if value != value or value in (float("inf"), float("-inf")):
        return text
    # `repr` is the shortest string that reads back as the same float; only its
    # `.0` on a whole number is something no person writes.
    return repr(value).removesuffix(".0")


def _serial(text: str, kind: str, date1904: bool) -> str:
    """A serial date-time as a person writes it: `2026-07-11`, `14:30`, both.

    The 1900 system's serial 60 is 1900-02-29, a day that never existed (Lotus's
    leap-year bug, kept by Excel for compatibility); it is left a number rather
    than invented. So is a negative serial, which no epoch reaches.
    """
    try:
        serial = float(text)
    except ValueError:
        return text
    if serial < 0 or (not date1904 and int(serial) == _PHANTOM_LEAP_DAY):
        return _number(text)
    days, seconds = divmod(round(serial * _SECONDS_PER_DAY), _SECONDS_PER_DAY)
    if date1904:
        epoch = _EPOCH_1904
    else:
        epoch = _EPOCH_1900 if days > _PHANTOM_LEAP_DAY else _EPOCH_1900_EARLY
    try:
        moment = _dt.datetime.combine(epoch, _dt.time()) + _dt.timedelta(days=days, seconds=seconds)
    except OverflowError:
        return _number(text)
    date = moment.date().isoformat()
    # `HH:MM`, and `HH:MM:SS` only when the second is not zero.
    clock = moment.time().isoformat(timespec="seconds" if moment.second else "minutes")
    if kind == "date":
        return date
    if kind == "time":
        return clock
    return f"{date} {clock}"


def _header_index(filled: list[int], width: int, percent: int) -> int:
    """The first row whose source-filled count reaches `percent` of `width`, or 0.

    Integer arithmetic — `count * 100 >= width * percent` — so no float rounding
    can put the boundary on one side on one machine and the other on another.
    A row that reaches it is the header even when a later row is fuller: a
    header is a position, not a score.
    """
    for index, count in enumerate(filled):
        if count and count * _PERCENT >= width * percent:
            return index
    return 0


def _combine(rows: list[list[str]]) -> list[str]:
    """Several header rows -> one, per column: `Q1` over `Revenue` reads
    `Q1 Revenue`. A value a span repeated down a column is said once."""
    out = []
    for i in range(max(len(r) for r in rows)):
        words: list[str] = []
        for row in rows:
            value = row[i] if i < len(row) else ""
            if value and (not words or words[-1] != value):
                words.append(value)
        out.append(" ".join(words))
    return out


def _drop_empty_columns(rows: list[list[str]]) -> list[list[str]]:
    width = max(len(row) for row in rows)
    keep = [i for i in range(width) if any(i < len(row) and row[i] for row in rows)]
    return [[row[i] if i < len(row) else "" for i in keep] for row in rows]


def _markdown(rows: list[list[str]]) -> str:
    width = max(len(row) for row in rows)
    if not width:
        return ""
    lines = []
    for index, row in enumerate(rows):
        cells = [c.replace("|", r"\|") for c in row] + [""] * (width - len(row))
        lines.append("| " + " | ".join(cells) + " |")
        if index == 0:
            lines.append("|" + "---|" * width)
    return "\n".join(lines)
