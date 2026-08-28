"""CSV and TSV -> a Markdown table.

⚠ **This decoder inherits `jsondoc`'s problem and does not solve it.** A
spreadsheet of numbers has almost no prose in it, and admitting one to a corpus
adds tokens without adding answers — which is the shape
[ADR-TYPES](../../../docs/adr/0031_types-list.md) verdict G measured. `.csv` is
therefore **not** in `DEFAULT_TYPES` either, and a consumer opts in knowing
their data is mostly words.

What it does well: a CSV whose cells *are* words — a decision log, an owner
table, a glossary export — becomes a real table with its header row intact, and
the header row is what makes a cell findable.

⚠ The columns-as-headings question is deliberately **not** answered here. That
is ranking policy, it belongs in `extract.py`, and putting it in a decoder
would hand ranking to every consumer decoder — see
[`work/proposals/structure-aware-extraction.md`](../../../work/proposals/structure-aware-extraction.md).
"""

from __future__ import annotations

import csv
import io

EXTENSIONS = (".csv", ".tsv")

#: Rows past this are a dataset rather than a document. Truncating keeps the
#: header and the first, most representative rows, which is what a search hit
#: actually needs to be useful.
MAX_ROWS = 500

#: Guards against a malformed quote turning one line into one enormous field.
MAX_CELL_CHARS = 500


def decode(raw: bytes, rel_path: str) -> str | None:
    text = raw.decode("utf-8-sig", errors="replace")
    if not text.strip():
        return None
    delimiter = "\t" if rel_path.lower().endswith(".tsv") else _sniff(text)
    try:
        rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    except csv.Error:
        return None

    rows = [r for r in rows if any(cell.strip() for cell in r)]
    if not rows:
        return None
    truncated = len(rows) > MAX_ROWS
    rows = rows[:MAX_ROWS]

    width = max(len(r) for r in rows)
    lines: list[str] = []
    for index, row in enumerate(rows):
        cells = [_cell(c) for c in row] + [""] * (width - len(row))
        lines.append("| " + " | ".join(cells) + " |")
        if index == 0:
            lines.append("|" + "---|" * width)
    if truncated:
        # Said in the document rather than hidden, so a reader of a search hit
        # knows the tail exists. Not a row count — a count would change with
        # the file and make the text a moving target for no benefit.
        lines.append("")
        lines.append("*(table truncated)*")
    return "\n".join(lines) + "\n"


def _cell(value: str) -> str:
    # Pipes would break the table grammar; escaping rather than dropping keeps
    # the term searchable, which is the only thing that matters downstream.
    return " ".join(value.split())[:MAX_CELL_CHARS].replace("|", r"\|")


def _sniff(text: str) -> str:
    """Comma unless a semicolon file is obviously semicolon-separated.

    `csv.Sniffer` is avoided deliberately: it is heuristic, it raises on short
    files, and a *heuristic* in the ingest path means the same bytes could be
    read two ways on two machines. Counting two candidates in the first line is
    boring, total, and reproducible.
    """
    first = text.splitlines()[0] if text.splitlines() else ""
    return ";" if first.count(";") > first.count(",") else ","
