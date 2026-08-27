"""Shared walk for the Office and OpenDocument families.

Both are a zip of namespaced XML, and both hide the same trap: **a paragraph's
text is split across arbitrarily many runs**. Word will happily store "runbook"
as three runs because a spell-checker touched the middle of it. Joining runs
without care produces "run book"; joining them naively across paragraphs
produces one enormous line with no headings in it.

So the shared piece is not "read the zip" — `_zip.py` does that — it is
**paragraph assembly**, which is the part that is subtle and identical across
six formats.
"""

from __future__ import annotations

# Imports are ABSOLUTE, not relative, and that is what makes this file work in
# both places it runs: as a package module, and as a consumer copy in
# `.fux/decoders/` loaded by path. A path-loaded file has no parent package, so
# `from . import _xml` raises `attempted relative import with no known parent
# package` — the copy would be dead on arrival. Absolute imports mean the file
# fux ships and the file you edit are byte-identical (ADR-DECODE decision 11).
from fux.decode import _xml

#: Word/PowerPoint mark a paragraph's style by name. Matching on the *name*
#: rather than an outline level is deliberate: the level lives in the styles
#: part, and following that indirection means reading a second file to learn
#: something the style name already says in every real document.
_HEADING_NAMES = ("heading", "title", "subtitle", "berschrift")  # Überschrift, de


def paragraph_text(element) -> str:
    """One paragraph's text, runs joined **without** separators.

    No space between runs: a run boundary is a formatting event, not a word
    boundary. Inserting one is how "runbook" becomes "run book" and stops
    matching the query someone actually types.
    """
    pieces: list[str] = []
    for node in element.iter():
        tag = _xml.local(node.tag)
        if tag in ("t", "span") and node.text:
            pieces.append(node.text)
        elif tag in ("tab",):
            pieces.append(" ")
        elif tag in ("br", "cr", "line-break"):
            pieces.append("\n")
    return " ".join("".join(pieces).split())


def heading_level(style: str | None) -> int | None:
    """A style name -> a Markdown heading level, or `None` for body text.

    `Title` outranks `Heading 1` in Word's own hierarchy, so it maps to H1 and
    numbered headings shift down by one. Getting this backwards would put a
    document's title below its sections in the heading field, which is the
    field `extract.py` weights most.
    """
    if not style:
        return None
    lowered = style.lower()
    if not any(name in lowered for name in _HEADING_NAMES):
        return None
    if "title" in lowered:
        return 1
    if "subtitle" in lowered:
        return 2
    digits = "".join(c for c in lowered if c.isdigit())
    if digits:
        return min(int(digits) + 1, 6)
    return 2


def table_markdown(rows: list[list[str]]) -> str:
    """Rows -> a Markdown table, header separator after the first row.

    Empty rows are dropped and short rows padded so the grammar stays valid;
    a malformed table that breaks Markdown parsing downstream would take the
    rest of the document with it.
    """
    rows = [r for r in rows if any(cell.strip() for cell in r)]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    lines: list[str] = []
    for index, row in enumerate(rows):
        cells = [c.replace("|", r"\|") for c in row] + [""] * (width - len(row))
        lines.append("| " + " | ".join(cells) + " |")
        if index == 0:
            lines.append("|" + "---|" * width)
    return "\n".join(lines)
