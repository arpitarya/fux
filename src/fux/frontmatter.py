"""Hand-rolled frontmatter parser/serializer (subset YAML).

This module is the zero-dependency guarantee made concrete: no PyYAML, ever
(CLAUDE.md). The supported subset: plain and quoted scalars (str, int, float,
bool, null; ISO dates stay strings), inline `[a, b]` and block `- item` lists,
nested mappings by two-space indent, and literal `|` blocks. Unknown keys
round-trip untouched — OKF requires consumers to preserve what they don't
understand. Parsing is permissive (OKF §9): malformed input degrades to
"no frontmatter, whole text is body", never an exception.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

_DELIM = "---"
_INT_RE = re.compile(r"^-?\d+$")
_FLOAT_RE = re.compile(r"^-?\d+\.\d+([eE][+-]?\d+)?$")
# Values that would parse back as something other than a plain string must be
# quoted on the way out.
_NEEDS_QUOTE_RE = re.compile(r"^[\-\[\{#>\|&\*!%@`\"']|[:#]\s|:$|^\s|\s$")


@dataclass
class Frontmatter:
    """Parsed document: metadata mapping, body text, 1-based body start line."""

    meta: dict
    body: str
    body_start_line: int = 1


def parse(text: str) -> Frontmatter:
    """Split ``text`` into (meta, body). Permissive: no/broken frontmatter → {}."""
    lines = text.split("\n")
    if not lines or lines[0].rstrip() != _DELIM:
        return Frontmatter({}, text, 1)
    close = None
    for i in range(1, len(lines)):
        if lines[i].rstrip() == _DELIM:
            close = i
            break
    if close is None:  # no closing delimiter: treat everything as body
        return Frontmatter({}, text, 1)
    meta, _ = _parse_mapping(lines[1:close], 0, 0)
    body = "\n".join(lines[close + 1 :])
    return Frontmatter(meta, body, close + 2)


def dumps(meta: dict, body: str) -> str:
    """Serialize deterministically (insertion order; stable quoting rules)."""
    lines = [_DELIM]
    for key, value in meta.items():
        _emit(lines, key, value, 0)
    lines.append(_DELIM)
    return "\n".join(lines) + "\n" + body


# -- parsing ---------------------------------------------------------------


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_mapping(lines: list[str], i: int, indent: int) -> tuple[dict, int]:
    out: dict = {}
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        cur = _indent_of(raw)
        if cur < indent:
            break
        if cur > indent or stripped.startswith("- "):
            i += 1  # stray deeper line or list item outside a key: skip, permissive
            continue
        key, sep, rest = stripped.partition(":")
        if not sep:
            i += 1
            continue
        key, rest = key.strip(), rest.strip()
        if rest in ("|", ">"):
            out[key], i = _collect_literal(lines, i + 1, indent)
        elif rest == "":
            out[key], i = _parse_nested(lines, i + 1, indent)
        else:
            out[key] = _parse_scalar(rest)
            i += 1
    return out, i


def _parse_nested(lines: list[str], i: int, indent: int):
    """A key with no inline value: nested mapping, block list, or null."""
    j = i
    while j < len(lines) and not lines[j].strip():
        j += 1
    if j >= len(lines) or _indent_of(lines[j]) <= indent:
        return None, i
    if lines[j].strip().startswith("- "):
        return _parse_list(lines, j, _indent_of(lines[j]))
    return _parse_mapping(lines, j, _indent_of(lines[j]))


def _parse_list(lines: list[str], i: int, indent: int) -> tuple[list, int]:
    out = []
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue
        if _indent_of(lines[i]) < indent or not stripped.startswith("- "):
            break
        out.append(_parse_scalar(stripped[2:].strip()))
        i += 1
    return out, i


def _collect_literal(lines: list[str], i: int, indent: int) -> tuple[str, int]:
    """Literal `|` block: deeper-indented lines verbatim; trailing blanks dropped."""
    block: list[str] = []
    block_indent = None
    while i < len(lines):
        raw = lines[i]
        if raw.strip():
            if _indent_of(raw) <= indent:
                break
            if block_indent is None:
                block_indent = _indent_of(raw)
            block.append(raw[block_indent:])
        else:
            block.append("")
        i += 1
    while block and not block[-1]:
        block.pop()
    return "\n".join(block), i


def _parse_scalar(token: str):
    if token.startswith('"') and token.endswith('"') and len(token) >= 2:
        try:
            return json.loads(token)
        except ValueError:
            return token[1:-1]
    if token.startswith("'") and token.endswith("'") and len(token) >= 2:
        return token[1:-1].replace("''", "'")
    if " #" in token:  # unquoted inline comment
        token = token.split(" #", 1)[0].rstrip()
    if token.startswith("[") and token.endswith("]"):
        inner = token[1:-1].strip()
        return [_parse_scalar(p) for p in _split_inline(inner)] if inner else []
    low = token.lower()
    if low in ("true", "false"):
        return low == "true"
    if low in ("null", "~", ""):
        return None
    if _INT_RE.match(token):
        return int(token)
    if _FLOAT_RE.match(token):
        return float(token)
    return token


def _split_inline(inner: str) -> list[str]:
    """Split an inline list body on top-level commas, honoring quotes."""
    parts, buf, quote = [], [], None
    for ch in inner:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch == ",":
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    return [p for p in parts if p]


# -- serialization ---------------------------------------------------------


def _emit(lines: list[str], key: str, value, indent: int) -> None:
    pad = " " * indent
    if isinstance(value, dict):
        lines.append(f"{pad}{key}:")
        for k, v in value.items():
            _emit(lines, k, v, indent + 2)
    elif isinstance(value, list):
        if not value:
            lines.append(f"{pad}{key}: []")
        else:
            lines.append(f"{pad}{key}:")
            for item in value:
                lines.append(f"{pad}  - {_fmt_scalar(item)}")
    elif isinstance(value, str) and "\n" in value:
        lines.append(f"{pad}{key}: |")
        for ln in value.split("\n"):
            lines.append(f"{pad}  {ln}" if ln else "")
    else:
        lines.append(f"{pad}{key}: {_fmt_scalar(value)}")


def _fmt_scalar(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    s = str(value)
    if (
        not s
        or _NEEDS_QUOTE_RE.search(s)
        or _INT_RE.match(s)
        or _FLOAT_RE.match(s)
        or s.lower() in ("true", "false", "null", "~")
        or "[" == s[:1]
    ):
        return json.dumps(s, ensure_ascii=False)
    return s
