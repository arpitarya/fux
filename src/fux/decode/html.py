"""HTML -> Markdown. **Lifted, not written.**

This parser was already in the repo — twice. `.fux/fetchers/http.py` carried it
and `.fux/fetchers/cdp.py` carried a copy marked *"Kept identical to…"*, with
nothing keeping it identical. `http.py`'s own docstring stated the consequence
as a rule it could not enforce:

    Both fetchers must produce the same markdown from the same bytes, or which
    fetcher retrieved a document would change the committed index.

That is **same sources -> same index** (L4) demoted to a code comment. Moving
the pass here makes the requirement structurally true instead of asked for:
there is one implementation, and both fetchers reach it.

**Behaviour is preserved deliberately, including its rough edges.** Anything
this emits differently from the fetcher copies would silently re-rank every
URL-sourced document already in a committed index. Changes to the conversion
belong in their own change, with the goldens re-blessed on purpose.
"""

from __future__ import annotations

import codecs
import re
from html.parser import HTMLParser
from fux.constants import fixed
from fux.decode import _table
from fux.decode._limits import limit

#: **The reuse key's handle on this decoder** (W-166). Bump it by hand in the
#: same change as any edit that can change what `decode()` returns, and the next
#: `fux ingest` re-extracts the documents bound to THIS decoder and no others.
#: Leaving it alone is the claim that the edit cannot move a byte of output.
#: `tests/decode/test_decoder_versions.py` fails on a changed module that did
#: not bump it. [SR-DECODE](../../../records/0139_decode.md) decision 11a.
VERSION = fixed("decoders.html", "version")  # 2 (W-287 A2/A4): thead/th header, colspan/rowspan, caption, nested tables, escaped pipes

EXTENSIONS = tuple(fixed("decoders.html", "extensions"))

_SKIP = {"script", "style", "head", "noscript", "template", "svg", "iframe"}
_BLOCK_BREAK = {"p", "div", "section", "article", "main", "header", "footer", "figure"}
#: `<h1>`..`<h6>` -- HTML's six levels are Markdown's (`constants.toml [markdown]`).
_HEADINGS = {f"h{level}": level for level in range(1, fixed("markdown", "max_heading") + 1)}

#: `<meta charset=...>` / `<meta http-equiv=content-type ... charset=...>`.
#: Only the first 4 KiB is searched, which is where the spec requires it and
#: where every real document puts it — and a bounded search keeps a pathological
#: file from turning encoding detection into a scan of the whole document.
_CHARSET_RE = re.compile(rb"""charset\s*=\s*["']?\s*([A-Za-z0-9_\-.:]+)""", re.IGNORECASE)

PREPEND_TITLE_HEADING = True

#: WHATWG's span clamps (`constants.toml [decoders.html.format]`).
_MAX_COLSPAN = fixed("decoders.html.format", "max_colspan")
_MAX_ROWSPAN = fixed("decoders.html.format", "max_rowspan")
_MAX_HEADING = fixed("markdown", "max_heading")


class _Table:
    """One `<table>` being read: its rows, the cell in progress, its caption.

    W-287 A2. A row is `(cells, section)` and a cell `(text, is_th, colspan,
    rowspan)` — the spans are expanded only when the table closes, because a
    `rowspan` reaches rows that have not been read yet.
    """

    def __init__(self) -> None:
        self.rows: list[tuple[list[tuple[str, bool, int, int]], str]] = []
        self.cell: list[str] | None = None
        self.cell_th = False
        self.cell_span = (1, 1)
        self.caption: list[str] | None = None
        self.caption_text = ""
        self.section = "tbody"


def decode(raw: bytes, rel_path: str) -> str | None:
    """One HTML document -> Markdown, or `None` when nothing was extractable.

    `None` rather than an exception for an empty result: a page that is all
    chrome and images has no prose to index, which is a fact about the page and
    not a failure of the run.
    """
    html = raw.decode(_charset(raw), errors="replace")
    markdown = html_to_markdown(html)
    title = extract_title(html)
    heading = "# " + title
    if PREPEND_TITLE_HEADING and title and not markdown.startswith(heading + "\n"):
        markdown = heading + "\n\n" + markdown
    return markdown if markdown.strip() else None


def _charset(raw: bytes) -> str:
    """The document's declared encoding, or utf-8.

    A fetcher learns this from the HTTP `Content-Type` header; a file on disk
    has no header, so the declaration inside the bytes is all there is. An
    unknown or hostile label falls back to utf-8 rather than raising — the
    caller passes `errors="replace"`, so a wrong guess costs a few characters
    and never the document.
    """
    if raw.startswith(codecs.BOM_UTF8):
        return "utf-8-sig"
    match = _CHARSET_RE.search(raw[: limit("html", "charset_scan_bytes")])
    if match:
        label = match.group(1).decode("ascii", errors="replace").strip().lower()
        try:
            "".encode(label)  # cheapest way to ask the codec registry
        except (LookupError, TypeError, ValueError):
            return "utf-8"
        return label
    return "utf-8"


def html_to_markdown(html: str) -> str:
    parser = _MdParser()
    parser.feed(html)
    parser.close()
    return parser.result()


def extract_title(html: str) -> str:
    parser = _TitleParser()
    parser.feed(html)
    parser.close()
    return parser.title.strip()


class _MdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self.inline: list[str] = []
        self.skip_depth = 0
        self.pre_depth = 0
        self.pre_text: list[str] = []
        self.heading: int | None = None
        self.quote_depth = 0
        self.list_stack: list[tuple[str, int]] = []  # (kind, counter)
        self.href: list[str] = []
        #: Open tables, innermost last. A table opened inside a cell is NESTED:
        #: it is flattened into that cell when it closes (W-287 A2), where it
        #: used to reset the outer table and lose every row read so far.
        self.tables: list[_Table] = []
        #: The level of the last heading emitted — a `<caption>` becomes a
        #: heading one level below it. The title the decoder prepends is H1.
        self.last_level = 1

    # -- emit helpers ------------------------------------------------------

    def _flush_inline(self, prefix: str = "") -> None:
        text = " ".join("".join(self.inline).split())
        self.inline = []
        if text:
            quote = "> " * self.quote_depth
            self.blocks.append(f"{quote}{prefix}{text}")

    def _text(self, data: str) -> None:
        table = self.tables[-1] if self.tables else None
        if self.pre_depth:
            self.pre_text.append(data)
        elif table is not None and table.caption is not None:
            table.caption.append(data)
        elif table is not None and table.cell is not None:
            table.cell.append(data)
        else:
            self.inline.append(data)

    # -- parser events -----------------------------------------------------

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs = dict(attrs)
        if tag in _SKIP:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag == "pre":
            self._flush_inline()
            self.pre_depth += 1
        elif tag in _HEADINGS:
            self._flush_inline()
            self.heading = _HEADINGS[tag]
        elif tag in ("ul", "ol"):
            self._flush_inline()
            self.list_stack.append((tag, 0))
        elif tag == "li":
            self._flush_inline()
        elif tag == "blockquote":
            self._flush_inline()
            self.quote_depth += 1
        elif tag == "table":
            if not self.tables:
                self._flush_inline()
            self.tables.append(_Table())
        elif tag == "caption" and self.tables:
            self.tables[-1].caption = []
        elif tag in ("thead", "tbody", "tfoot") and self.tables:
            self.tables[-1].section = tag
        elif tag == "tr" and self.tables:
            table = self.tables[-1]
            self._close_cell(table)
            table.rows.append(([], table.section))
        elif tag in ("td", "th") and self.tables:
            table = self.tables[-1]
            self._close_cell(table)
            table.cell = []
            table.cell_th = tag == "th"
            table.cell_span = (_span(attrs.get("colspan"), _MAX_COLSPAN), _span(attrs.get("rowspan"), _MAX_ROWSPAN))
        elif tag == "a":
            self.href.append(attrs.get("href", ""))
            self._text("[")
        elif tag == "img":
            alt = attrs.get("alt", "") or "image"
            src = attrs.get("src", "")
            self._text(f"![{alt}]({src})")
        elif tag == "code" and not self.pre_depth:
            self._text("`")
        elif tag in ("b", "strong"):
            self._text("**")
        elif tag in ("i", "em"):
            self._text("*")
        elif tag == "br":
            self._flush_inline()
        elif tag in ("hr",):
            self._flush_inline()
            self.blocks.append("---")
        elif tag in _BLOCK_BREAK:
            self._flush_inline()

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return
        if tag == "pre":
            self.pre_depth = max(0, self.pre_depth - 1)
            if not self.pre_depth:
                code = "\n".join(
                    line.rstrip() for line in "".join(self.pre_text).strip("\n").split("\n")
                )
                self.pre_text = []
                self.blocks.append(f"```\n{code}\n```")
        elif tag in _HEADINGS:
            level = self.heading or _HEADINGS[tag]
            self._flush_inline(prefix="#" * level + " ")
            self.heading = None
            self.last_level = level
        elif tag in ("ul", "ol"):
            self._flush_inline()
            if self.list_stack:
                self.list_stack.pop()
        elif tag == "li":
            indent = "  " * max(0, len(self.list_stack) - 1)
            if self.list_stack and self.list_stack[-1][0] == "ol":
                kind, count = self.list_stack[-1]
                self.list_stack[-1] = (kind, count + 1)
                self._flush_inline(prefix=f"{indent}{count + 1}. ")
            else:
                self._flush_inline(prefix=f"{indent}- ")
        elif tag == "blockquote":
            self._flush_inline()
            self.quote_depth = max(0, self.quote_depth - 1)
        elif tag in ("td", "th") and self.tables:
            self._close_cell(self.tables[-1])
        elif tag == "caption" and self.tables:
            table = self.tables[-1]
            if table.caption is not None:
                table.caption_text = " ".join("".join(table.caption).split())
            table.caption = None
        elif tag in ("thead", "tbody", "tfoot") and self.tables:
            self.tables[-1].section = "tbody"
        elif tag == "table" and self.tables:
            table = self.tables.pop()
            self._close_cell(table)
            if self.tables:
                self._nest(table, self.tables[-1])
            else:
                self._emit_table(table)
        elif tag == "a":
            href = self.href.pop() if self.href else ""
            self._text(f"]({href})" if href else "]")
        elif tag == "code" and not self.pre_depth:
            self._text("`")
        elif tag in ("b", "strong"):
            self._text("**")
        elif tag in ("i", "em"):
            self._text("*")
        elif tag in _BLOCK_BREAK:
            self._flush_inline()

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self._text(data)

    def _close_cell(self, table: _Table) -> None:
        """End the cell in progress, if any — `</td>` is optional in HTML."""
        if table.cell is None:
            return
        if table.rows:
            text = " ".join("".join(table.cell).split())
            colspan, rowspan = table.cell_span
            table.rows[-1][0].append((text, table.cell_th, colspan, rowspan))
        table.cell = None

    def _nest(self, inner: _Table, outer: _Table) -> None:
        """A nested table, flattened into the outer cell it sits in: its caption,
        then each row's cells, rows separated by `;`."""
        rows = [" ".join(t for t, *_ in cells if t) for cells, _section in inner.rows]
        text = "; ".join(r for r in [inner.caption_text, *rows] if r)
        if outer.cell is not None and text:
            outer.cell.append(" " + text + " ")

    def _emit_table(self, table: _Table) -> None:
        """W-287 A2/A4 — the table as a `Grid` for `_table.emit`; a caption is
        its heading, one level below the last heading emitted."""
        grid = _grid(table.rows)
        # Read only when the table declares no header: a `<th>` table needs no
        # threshold, and `html_to_markdown` is called with no repository bound.
        percent = None if grid.header else limit("html", "header_fill_percent")
        out = _table.emit(
            grid,
            header_fill_percent=percent,
            row_limit=None,
            max_cell_chars=None,
        )
        if not out.markdown:
            if table.caption_text:
                self.blocks.append(table.caption_text)
            return
        if table.caption_text:
            level = min(self.last_level + 1, _MAX_HEADING)
            self.blocks.append("#" * level + " " + table.caption_text)
        if out.prose:
            self.blocks.append("\n".join(out.prose))
        self.blocks.append(out.markdown)

    def result(self) -> str:
        self._flush_inline()
        out = "\n\n".join(b for b in self.blocks if b.strip())
        return out + "\n" if out else ""


def _span(value, cap: int) -> int:
    """A `colspan`/`rowspan` attribute as a count: 1 when absent or nonsense,
    clamped to WHATWG's ceiling. `rowspan="0"` spans the rest of the table."""
    try:
        n = int(str(value).strip())
    except (TypeError, ValueError):
        return 1
    if n == 0:
        return cap
    return max(1, min(n, cap))


def _grid(rows) -> _table.Grid:
    """The rows an HTML table held -> a `_table.Grid` (W-287 A2).

    A cell is placed at the first column no earlier `rowspan` still holds;
    `colspan`/`rowspan` become a span; a row with no cells is no row. The
    declared header is the `<thead>` rows, else a leading run of rows whose
    every cell is a `<th>`; with neither, `_table.emit` finds it by fill.
    """
    grid = _table.Grid()
    pending: dict[int, int] = {}  # column -> rows still covered below
    sections: list[str] = []
    all_th: list[bool] = []
    r = -1
    for cells, section in rows:
        if not cells:
            continue
        r += 1
        sections.append(section)
        all_th.append(all(th for _t, th, *_ in cells))
        occupied = set(pending)
        for col, left in list(pending.items()):
            if left <= 1:
                del pending[col]
            else:
                pending[col] = left - 1
        col = 0
        for text, _th, colspan, rowspan in cells:
            while col in occupied:
                col += 1
            grid.cells[(r, col)] = _table.Cell(text, "text")
            if colspan > 1 or rowspan > 1:
                grid.spans.append((r, col, r + rowspan - 1, col + colspan - 1))
            for k in range(colspan):
                occupied.add(col + k)
                if rowspan > 1:
                    pending[col + k] = rowspan - 1
            col += colspan
    head = [i for i, section in enumerate(sections) if section == "thead"]
    if not head:
        while len(head) < len(all_th) and all_th[len(head)]:
            head.append(len(head))
    grid.header = tuple(head)
    return grid


class _TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "title" and not self.title:
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
