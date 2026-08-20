"""Consumer-owned URL fetcher — a plain HTTP GET, pure stdlib.

**This file belongs to you, not to fux. It is committed to your repo, at
`.fux/fetchers/http.py`, and fux will never rewrite it.** `fux setup` writes it
once if it is missing; after that it is yours. Fux reads it by path under
`fux ingest --refresh-urls`, calls it to turn each URL into markdown, and
indexes the result exactly like a repo file. Edit anything — add headers, a
proxy, an auth token from your environment, a retry, a different HTML
converter. Fux imports none of that, only this file's entry points.

**This is the default fetcher.** A line in `.fux/sources/urls` with no `fetch=`
attribute comes here. A line that says `fetch=cdp` goes to `cdp.py` instead,
and **nothing escalates automatically** — not on a non-2xx, not on an empty
body, not on a page that is obviously a rendered shell. A plain GET that
returns something useless returns something useless, and a human writes
`fetch=cdp` on that line. A classifier deciding what "too thin" means is how a
navigation bar gets indexed as a runbook. A tiny `wlen` in the index is the
signal that a page needed a browser, and it is one a human reads once.

Living in a dotdir has one consequence worth knowing: linters that skip hidden
directories by default (ruff does) will not lint this file. That is deliberate
— it is your code, not a fux CI target.

The contract fux relies on — keep these names:

    configure(config: dict) -> None  # optional; once after import, before connect()
    connect() -> None        # optional; called once before the first fetch
    fetch(url: str) -> str   # required; the document for one URL, as markdown
    close() -> None          # optional; called once after the last fetch

There is no `connect`/`close` below: they are optional, and a stateless GET has
no batch to bracket.

`fetch` may raise on failure — fux records the URL as skipped (with the error
as the reason) and, if a previous ingest indexed it, keeps that older record
rather than deleting it.

`configure` receives `[sources.url.config]` from `fux.toml` **verbatim**; fux
validates only that it is a table and never reads a key inside it. The
constants below are therefore *defaults*, and the table overrides them — put
tunables in `fux.toml` rather than editing this file, and merges stay clean.

The HTML->markdown pass below is the one `cdp.py` uses. Both fetchers must
produce the same markdown from the same bytes, or which fetcher retrieved a
document would change the committed index — and `fetch=` is a routing
decision, never a property of the document.
"""

from __future__ import annotations

import urllib.request
from html.parser import HTMLParser

# ============= CONFIG - defaults; [sources.url.config] wins =============
# Each name below maps to a snake_case key in fux.toml's
# `[sources.url.config]` table (see `configure` at the bottom of this file).

TIMEOUT_S = 30.0
USER_AGENT = "fux/0.x (+https://github.com/arpitarya/fux)"
MAX_BYTES = 8 * 1024 * 1024  # a page larger than this is a download, not a doc
PREPEND_TITLE_HEADING = True  # ensure the page <title> leads the document


class FetcherError(RuntimeError):
    """Raised for a failure fux should record as a skip, not a crash."""


# ====================================================================
# HTML -> Markdown - stdlib html.parser, deterministic. Kept identical to
# cdp.py's pass on purpose: two fetchers that convert differently would
# make the committed index a function of which one ran.
# Headings matter: fux weights heading terms 3x body at ranking time.
# ====================================================================

_SKIP = {"script", "style", "head", "noscript", "template", "svg", "iframe"}
_BLOCK_BREAK = {"p", "div", "section", "article", "main", "header", "footer", "figure"}
_HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}


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


# ====================================================================
# The contract fux calls.
# ====================================================================

# fux.toml key -> (this module's global, coercion). Add your own keys here;
# fux passes the whole table through without looking inside it.
_SETTINGS = {
    "timeout_s": ("TIMEOUT_S", float),
    "user_agent": ("USER_AGENT", str),
    "max_bytes": ("MAX_BYTES", int),
    "prepend_title_heading": ("PREPEND_TITLE_HEADING", bool),
}


def configure(config: dict) -> None:
    """Called once after import with `[sources.url.config]` from fux.toml.

    Overrides the CONFIG defaults above. An unknown key raises rather than
    being silently ignored — a typo'd tunable that does nothing is the kind of
    failure you find three ingests later.
    """
    unknown = sorted(set(config) - set(_SETTINGS))
    if unknown:
        raise FetcherError(
            f"[sources.url.config] unknown key(s): {', '.join(unknown)} — "
            f"known keys: {', '.join(sorted(_SETTINGS))}"
        )
    for key, value in config.items():
        name, coerce = _SETTINGS[key]
        try:
            globals()[name] = coerce(value)
        except (TypeError, ValueError) as exc:
            raise FetcherError(f"[sources.url.config] {key}: {exc}") from exc


def fetch(url: str) -> str:
    """One URL -> one markdown document. Raise to have fux skip this URL."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
            raw = response.read(MAX_BYTES + 1)
            charset = response.headers.get_content_charset() or "utf-8"
    except Exception as exc:  # every transport failure is a skip, never a crash
        raise FetcherError(f"{type(exc).__name__}: {exc}") from exc
    if len(raw) > MAX_BYTES:
        raise FetcherError(f"response larger than max_bytes ({MAX_BYTES})")

    html = raw.decode(charset, errors="replace")
    markdown = html_to_markdown(html)
    title = extract_title(html)
    heading = "# " + title
    if PREPEND_TITLE_HEADING and title and not markdown.startswith(heading + chr(10)):
        markdown = heading + chr(10) * 2 + markdown
    if not markdown.strip():
        raise FetcherError(f"nothing extractable at {url}")
    return markdown
