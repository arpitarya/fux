"""CSV and TSV -> a Markdown table.

⚠ **This decoder inherits `json`'s problem and does not solve it.** A
spreadsheet of numbers has almost no prose in it, and admitting one to a corpus
adds tokens without adding answers — which is the shape
[ADR-TYPES](../../../docs/adr/0031_types-list.md) verdict G measured. `.csv` is
therefore **not** in `DEFAULT_TYPES` either, and a consumer opts in knowing
their data is mostly words.

What it does well: a CSV whose cells *are* words — a decision log, an owner
table, a glossary export — becomes a real table with its header row intact, and
the header row is what makes a cell findable.

**The filename leads as an H1**, added 2026-09-06. Without it a CSV decoded to
a bare table: no heading for `refer/_chunk.py` to open a passage on, no
`phrases` for `extract.py` to mine, and — because a table contains no blank
line — a file over the passage ceiling that the chunker could not split at all.
The chunker now bands oversized tables by rows; this gives the band something
to be a section *of*.

⚠ The columns-as-headings question is deliberately **not** answered here. That
is ranking policy, it belongs in `extract.py`, and putting it in a decoder
would hand ranking to every consumer decoder — see
[`work/proposals/structure-aware-extraction.md`](../../../work/proposals/structure-aware-extraction.md).
"""

from __future__ import annotations

import csv
import io

EXTENSIONS = (".csv", ".tsv")

#: Rows past this are dropped. **Was a hard-coded 500 until 2026-09-06**, and
#: that number was a quiet data loss: a 754-row file decoded to 500 rows, so a
#: fact in row 600 was not decoded, not indexed and **not citable in any
#: configuration** — the `*(table truncated)*` line is the only signal, and
#: nobody diffs it. Found by a lab harness that planted answers past the limit
#: and could not find them (`work/regression/2026-09-06-csv-chunk-granularity/`).
#:
#: Now `.fux/tune.toml [index] max_table_rows`, defaulting to 20 000 (in
#: `fux.toml [decode]` from 2026-09-06 until Arpit moved it on 2026-09-11).
#: `[index]` is tune.toml's one table that changes what is **indexed** —
#: ADR-TUNE decision 13.
from fux.decode._limits import max_table_rows

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
    # The limit counts DATA rows: a consumer who writes 20 000 means twenty
    # thousand records, not 19 999 plus a header. The header is row 0 here and
    # is always kept — without it every cell downstream is unlabelled.
    limit = max_table_rows()
    truncated = len(rows) > limit + 1
    rows = rows[: limit + 1]

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
    name = rel_path.rsplit("/", 1)[-1]
    return f"# {name}\n\n" + "\n".join(lines) + "\n"


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
