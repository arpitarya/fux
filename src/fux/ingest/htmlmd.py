"""HTML → Markdown, stdlib `html.parser` — deterministic, good-enough fidelity.

Covers what documentation pages actually use: headings, paragraphs, nested
lists, tables, links, images, inline/block code, blockquotes, emphasis.
Scripts/styles/head chrome are dropped. Output is whitespace-normalized so the
same page always converts to the same bytes (handoff 0002; ADR 0005). Chosen
over MarkItDown-for-HTML as the *default* for determinism — the extra remains
an office-formats converter, not the web path (open question 1).
"""

from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin

_SKIP = {"script", "style", "head", "noscript", "template", "svg", "iframe"}
_BLOCK_BREAK = {"p", "div", "section", "article", "main", "header", "footer", "figure"}
_HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}


def html_to_markdown(html: str) -> str:
    parser = _MdParser()
    parser.feed(html)
    parser.close()
    return parser.result()


def extract_links(html: str, base_url: str) -> list[str]:
    """Absolute hrefs, document order, deduped; fragments stripped."""
    parser = _LinkParser(base_url)
    parser.feed(html)
    parser.close()
    return parser.links


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
                code = "\n".join(l.rstrip() for l in "".join(self.pre_text).strip("\n").split("\n"))
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


class _LinkParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base = base_url
        self.links: list[str] = []
        self._seen: set[str] = set()

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs = dict(attrs)
        if tag == "base" and attrs.get("href"):
            self.base = attrs["href"]
            return
        if tag != "a":
            return
        href = (attrs.get("href") or "").strip()
        if not href or href.startswith(("#", "mailto:", "javascript:", "tel:", "data:")):
            return
        absolute = urljoin(self.base, href).split("#", 1)[0]
        if absolute.startswith(("http://", "https://")) and absolute not in self._seen:
            self._seen.add(absolute)
            self.links.append(absolute)


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
