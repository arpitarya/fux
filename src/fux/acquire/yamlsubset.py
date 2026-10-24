"""The fux YAML subset, read — the grammar `.fux/sources.yaml` is written in.

**Owned by [SR-SOURCES](../../../records/0116_sources.md)** (W-294). Arpit ruled
YAML for the include manifest on 2026-10-24, *for hand-editing*; L2 rules out a
YAML package, and the standard library has none, so this is hand-rolled — the
`node/src/config/toml.mjs` precedent. Its Node twin is
`node/src/ingest/yamlsubset.mjs`, and `tests/test_sources_yaml_differential.py`
feeds both the same fixtures.

**A subset, and a strict one.** Everything outside it is a loud refusal naming
`file:line`, never a best guess:

- **Read:** block maps, block lists, plain / single-quoted / double-quoted
  scalars, and `#` comments — at a line's start, or after whitespace, which is
  YAML's own rule and is what keeps `page#frag` text while `page #frag` is a
  comment.
- **Refused:** flow `{}` / `[]`, anchors `&` and aliases `*`, tags `!`,
  `---` / `...` documents and `%` directives, block scalars `|` `>`, a `?`
  complex key, tab indentation, a duplicate key in one map, and a plain value
  holding `: `.

🔴 **Typing is the schema's, never this reader's.** Every scalar comes back as
TEXT plus whether it was quoted; nothing here turns `no`, `on`, `null`, `~`,
`1.10` or `010` into a boolean, a null or a number. `sourcesfile.py` decides
what each position may hold — which is why `no` stays a path where a path is
expected. A key with nothing after it and no block beneath is `Null`, the one
shape the schema needs to tell *empty* from *absent*.

Each node carries its line span and a scalar its column span, because the
writer (`fux add` / `fux remove`) edits the file **textually** — one line in,
one line or block out — and never re-renders it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..constants import table
from ..errors import FuxError

__all__ = ["Map", "Null", "Pair", "Scalar", "Seq", "parse", "message"]

#: The refusal texts, `constants.toml [yaml_subset]` — read by both planes.
_TEXTS = table("yaml_subset")

#: The c-indicators that cannot start a plain scalar (YAML 1.2 §5.3), each with
#: the refusal it earns. `-`, `?` and `:` are left out: each may start a plain
#: scalar when a non-space follows, and the line parser handles `- ` and `? `.
_START = {
    "{": "flow", "}": "flow", "[": "flow", "]": "flow",
    "&": "anchor", "*": "alias", "!": "tag",
    "|": "block", ">": "block",
    "@": "reserved", "`": "reserved", ",": "reserved", "%": "reserved",
}

#: The grammar's own characters. Code, not values (SR-LAW-12 decision 6,
#: `grammar`): changing one is a different language, not a different setting.
_SPACE = " "
_COMMENT = "#"
_ITEM = "- "
_COLON = ":"
#: The three escapes a double-quoted value may carry. A path or a URL needs no
#: other; anything else is refused rather than guessed at.
_ESCAPES = ("\\", '"', "/")
_DOC_MARKERS = ("---", "...")


def message(name: str, origin: str, line: int, **fill: object) -> str:
    """`origin:line: <text>` — the one shape every refusal takes, both planes."""
    return f"{origin}:{line}: " + _TEXTS[name].format(**fill)


def _fail(name: str, origin: str, line: int, **fill: object) -> FuxError:
    return FuxError(message(name, origin, line, **fill))


@dataclass(frozen=True)
class Scalar:
    """One value, as text. `col`..`end` is its span on `line`, quotes included."""

    text: str
    line: int
    col: int
    end: int
    quoted: bool

    @property
    def last(self) -> int:
        return self.line


@dataclass(frozen=True)
class Null:
    """`key:` with nothing after it and no block beneath it."""

    line: int

    @property
    def last(self) -> int:
        return self.line


@dataclass(frozen=True)
class Seq:
    items: tuple
    line: int
    last: int


@dataclass(frozen=True)
class Pair:
    key: str
    line: int
    value: object


@dataclass(frozen=True)
class Map:
    pairs: dict = field(default_factory=dict)
    line: int = 0
    last: int = 0


@dataclass(frozen=True)
class _Line:
    no: int
    indent: int
    content: str


def _is_item(content: str) -> bool:
    return content == _ITEM.strip() or content.startswith(_ITEM)


def _strip_plain_comment(text: str) -> str:
    """Cut a `#` comment: one at the start, or one after whitespace (YAML's rule)."""
    if text.startswith(_COMMENT):
        return ""
    for i, ch in enumerate(text):
        if ch == _COMMENT and i > 0 and text[i - 1] == _SPACE:
            return text[:i]
    return text


def _lines(text: str, origin: str) -> list[_Line]:
    out: list[_Line] = []
    for no, raw in enumerate(text.split("\n"), start=1):
        raw = raw.removesuffix("\r")
        stripped = raw.lstrip(" \t")
        if not stripped or stripped.startswith(_COMMENT):
            continue
        lead = raw[: len(raw) - len(stripped)]
        if "\t" in lead:
            raise _fail("tab", origin, no)
        indent = len(lead)
        if indent == 0:
            for marker in _DOC_MARKERS:
                if stripped == marker or stripped.startswith(marker + _SPACE):
                    raise _fail("document", origin, no, token=marker)
            if stripped.startswith("%"):
                raise _fail("directive", origin, no)
        out.append(_Line(no, indent, stripped))
    return out


def _key_split(content: str) -> "tuple[str, int] | None":
    """`(key, offset of what follows the colon)` when `content` is `key: ...`."""
    if content[:1] in ("'", '"'):
        return None
    body = _strip_plain_comment(content).rstrip()
    for i, ch in enumerate(body):
        if ch == _COLON and (i + 1 == len(body) or body[i + 1] == _SPACE):
            return body[:i].rstrip(), i + 1
    return None


def _check_key(key: str, origin: str, line: int) -> None:
    if not key:
        raise _fail("key", origin, line, token=":")
    if key.startswith("? ") or key == "?":
        raise _fail("complex_key", origin, line)
    first = key[0]
    if first in _START:
        raise _fail(_START[first], origin, line, token=first)


def _scalar(content: str, line: _Line, offset: int, origin: str) -> Scalar:
    """The value starting at `offset` of `line.content`, comment and all checked."""
    col = line.indent + offset
    text = content[offset:]
    first = text[:1]
    if first == '"' or first == "'":
        value, used = _quoted(text, first, origin, line.no)
        rest = text[used:]
        tail = rest.lstrip(_SPACE)
        if tail and not (tail.startswith(_COMMENT) and len(tail) < len(rest)):
            raise _fail("after_quote", origin, line.no)
        return Scalar(value, line.no, col, col + used, True)
    if first in _START:
        raise _fail(_START[first], origin, line.no, token=first)
    if text.startswith(_ITEM) or text == _ITEM.strip():
        raise _fail("reserved", origin, line.no, token=_ITEM.strip())
    if text.startswith("? "):
        raise _fail("complex_key", origin, line.no)
    value = _strip_plain_comment(text).rstrip(_SPACE)
    if _COLON + _SPACE in value or value.endswith(_COLON):
        raise _fail("colon_space", origin, line.no)
    return Scalar(value, line.no, col, col + len(value), False)


def _quoted(text: str, quote: str, origin: str, line: int) -> tuple[str, int]:
    """A quoted scalar's value and how many characters it used, quotes included."""
    out: list[str] = []
    i = 1
    while i < len(text):
        ch = text[i]
        if quote == "'":
            if ch == "'":
                if text[i + 1 : i + 2] == "'":
                    out.append("'")
                    i += 2
                    continue
                return "".join(out), i + 1
        else:
            if ch == "\\":
                nxt = text[i + 1 : i + 2]
                if nxt not in _ESCAPES:
                    raise _fail("escape", origin, line, token="\\" + nxt)
                out.append(nxt)
                i += 2
                continue
            if ch == '"':
                return "".join(out), i + 1
        out.append(ch)
        i += 1
    raise _fail("unclosed", origin, line)


class _Parser:
    def __init__(self, lines: list[_Line], origin: str) -> None:
        self.lines = lines
        self.origin = origin
        self.i = 0

    def peek(self) -> "_Line | None":
        return self.lines[self.i] if self.i < len(self.lines) else None

    def block(self, indent: int):
        line = self.peek()
        assert line is not None
        if _is_item(line.content):
            return self.seq(indent, compact=False)
        return self.map(indent, first=None)

    def nested(self, owner: _Line, indent: int, *, allow_compact: bool):
        """What sits beneath `owner` (a `key:` or a bare `-`), or `None`."""
        self.i += 1
        nxt = self.peek()
        if nxt is not None and nxt.indent > indent:
            return self.block(nxt.indent)
        if allow_compact and nxt is not None and nxt.indent == indent and _is_item(nxt.content):
            return self.seq(indent, compact=True)
        return None

    def expect_no_deeper(self, indent: int) -> None:
        nxt = self.peek()
        if nxt is not None and nxt.indent > indent:
            raise _fail("indent", self.origin, nxt.no)

    def seq(self, indent: int, *, compact: bool) -> Seq:
        items: list = []
        start = self.peek().no
        last = start
        while (line := self.peek()) is not None and line.indent == indent:
            if not _is_item(line.content):
                if compact:
                    break
                raise _fail("mixed", self.origin, line.no)
            rest_at = len(line.content) - len(line.content[1:].lstrip(_SPACE))
            rest = line.content[rest_at:]
            if not _strip_plain_comment(rest).strip():
                child = self.nested(line, indent, allow_compact=False)
                if child is None:
                    raise _fail("empty_item", self.origin, line.no)
            elif _key_split(rest) is not None:
                virtual = _Line(line.no, line.indent + rest_at, rest)
                child = self.map(virtual.indent, first=virtual)
            else:
                child = _scalar(rest, _Line(line.no, line.indent + rest_at, rest), 0, self.origin)
                self.i += 1
                self.expect_no_deeper(indent)
            items.append(child)
            last = child.last
        return Seq(tuple(items), start, last)

    def map(self, indent: int, *, first: "_Line | None") -> Map:
        pairs: dict[str, Pair] = {}
        line = first if first is not None else self.peek()
        start = line.no
        last = start
        while True:
            content = line.content
            if _is_item(content):
                raise _fail("mixed", self.origin, line.no)
            split = _key_split(content)
            if split is None:
                token = _strip_plain_comment(content).strip()
                raise _fail("key", self.origin, line.no, token=token)
            key, after = split
            _check_key(key, self.origin, line.no)
            if key in pairs:
                raise _fail("duplicate", self.origin, line.no, key=key, first=pairs[key].line)
            rest = content[after:]
            offset = after + (len(rest) - len(rest.lstrip(_SPACE)))
            if not _strip_plain_comment(content[offset:]).strip():
                value = self.nested(line, indent, allow_compact=True)
                if value is None:
                    value = Null(line.no)
            else:
                value = _scalar(content, line, offset, self.origin)
                self.i += 1
                self.expect_no_deeper(indent)
            pairs[key] = Pair(key, line.no, value)
            last = value.last
            nxt = self.peek()
            if nxt is None or nxt.indent != indent:
                break
            line = nxt
        return Map(pairs, start, last)


def parse(text: str, *, origin: str):
    """The document's root node — a `Map`, `Seq` or `Scalar` — or `None` when the
    file holds nothing but comments and blank lines."""
    lines = _lines(text, origin)
    if not lines:
        return None
    parser = _Parser(lines, origin)
    root = parser.block(lines[0].indent)
    leftover = parser.peek()
    if leftover is not None:
        raise _fail("dedent" if leftover.indent < lines[0].indent else "indent", origin, leftover.no)
    return root
