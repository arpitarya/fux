"""HTML -> Markdown. **Lifted, not written.**

This parser was already in the repo — twice. `.fux/fetchers/http.py` carried it
and `.fux/fetchers/cdp.py` carried a copy marked *"Kept identical to…"*, with
nothing keeping it identical. `http.py`'s own docstring stated the consequence
as a rule it could not enforce:

    Both fetchers must produce the same markdown from the same bytes, or which
    fetcher retrieved a document would change the committed index.

That is **same sources -> same index** (L3) demoted to a code comment. Moving
the pass here makes the requirement structurally true instead of asked for:
there is one implementation, and both fetchers reach it.

**Behaviour is preserved deliberately, including its rough edges.** Anything
this emits differently from the fetcher copies would silently re-rank every
URL-sourced document already in a committed index. Changes to the conversion
belong in their own change, with the goldens re-blessed on purpose.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

EXTENSIONS = (".html", ".htm", ".xhtml")

_SKIP = {"script", "style", "head", "noscript", "template", "svg", "iframe"}
_BLOCK_BREAK = {"p", "div", "section", "article", "main", "header", "footer", "figure"}
_HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}

#: `<meta charset=...>` / `<meta http-equiv=content-type ... charset=...>`.
#: Only the first 4 KiB is searched, which is where the spec requires it and
#: where every real document puts it — and a bounded search keeps a pathological
#: file from turning encoding detection into a scan of the whole document.
_CHARSET_RE = re.compile(rb"""charset\s*=\s*["']?\s*([A-Za-z0-9_\-.:]+)""", re.IGNORECASE)

PREPEND_TITLE_HEADING = True


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
    if raw[:3] == b"\xef\xbb\xbf":
        return "utf-8-sig"
    match = _CHARSET_RE.search(raw[:4096])
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
        self.table_rows: list[list[str]] | None = None
        self.cell: list[str] | None = None

    # -- emit helpers ------------------------------------------------------

    def _flush_inline(self, prefix: str = "") -> None:
        text = " ".join("".join(self.inline).split())
        self.inline = []
        if text:
            quote = "> " * self.quote_depth
            self.blocks.append(f"{quote}{prefix}{text}")

    def _text(self, data: str) -> None:
        if self.pre_depth:
            self.pre_text.append(data)
        elif self.cell is not None:
            self.cell.append(data)
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
            self._flush_inline()
            self.table_rows = []
        elif tag == "tr" and self.table_rows is not None:
            self.table_rows.append([])
        elif tag in ("td", "th") and self.table_rows is not None:
            self.cell = []
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
        elif tag in ("td", "th") and self.table_rows is not None:
            if self.cell is not None and self.table_rows:
                self.table_rows[-1].append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "table":
            self._emit_table()
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

    def _emit_table(self) -> None:
        rows = [r for r in (self.table_rows or []) if r]
        self.table_rows = None
        if not rows:
            return
        width = max(len(r) for r in rows)
        lines = []
        for i, row in enumerate(rows):
            padded = row + [""] * (width - len(row))
            lines.append("| " + " | ".join(padded) + " |")
            if i == 0:
                lines.append("|" + "---|" * width)
        self.blocks.append("\n".join(lines))

    def result(self) -> str:
        self._flush_inline()
        out = "\n\n".join(b for b in self.blocks if b.strip())
        return out + "\n" if out else ""


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
