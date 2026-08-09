"""YAML-subset frontmatter parser/serializer — $0, dependency-free (plan §3, §6).

Handles the shapes Fux emits: scalars, block & flow sequences, nested mappings
(``edges:``), and sequences of mappings (``examples:``). Not a full YAML parser —
deliberately small and deterministic over the substrate we control.
"""
from __future__ import annotations

from fux.scalars import scalar as _scalar

DELIM = "---"


def split(text: str) -> tuple[dict, str]:
    """Return (frontmatter dict, body) from a markdown file's text."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != DELIM:
        return {}, text
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == DELIM), None)
    if end is None:
        return {}, text
    fm = parse(lines[1:end])
    body = "\n".join(lines[end + 1 :]).lstrip("\n")
    return fm, body


def parse(lines: list[str]) -> dict:
    """Parse indentation-structured YAML-subset lines into a dict."""
    result, _ = _block(lines, 0, _indent(lines, 0))
    return result


def _indent(lines: list[str], i: int) -> int:
    return len(lines[i]) - len(lines[i].lstrip(" ")) if i < len(lines) else 0


def _block(lines: list[str], i: int, indent: int):
    """Parse a mapping or sequence at the given indent; return (value, next_i)."""
    n = len(lines)
    while i < n and not lines[i].strip():
        i += 1
    if i >= n or _indent(lines, i) < indent:
        return {}, i
    if lines[i].lstrip().startswith("- "):
        return _sequence(lines, i, indent)
    return _mapping(lines, i, indent)


def _mapping(lines: list[str], i: int, indent: int):
    out: dict = {}
    n = len(lines)
    while i < n:
        if not lines[i].strip():
            i += 1
            continue
        if _indent(lines, i) != indent:
            break
        key, _, rest = lines[i].strip().partition(":")
        rest = rest.strip()
        i += 1
        if rest:
            out[key] = _scalar(rest)
        elif i < n and _indent(lines, i) > indent:
            out[key], i = _block(lines, i, _indent(lines, i))
        else:
            out[key] = None
    return out, i


def _sequence(lines: list[str], i: int, indent: int):
    out: list = []
    n = len(lines)
    while i < n and lines[i].strip() and _indent(lines, i) == indent and lines[i].lstrip().startswith("- "):
        first = lines[i].lstrip()[2:]
        if ":" in first and not first.startswith(("'", '"', "[")):
            key, _, rest = first.partition(":")
            item = {key.strip(): _scalar(rest.strip())} if rest.strip() else {}
            i += 1
            child = indent + 2
            while i < n and lines[i].strip() and _indent(lines, i) >= child and not lines[i].lstrip().startswith("- "):
                k, _, v = lines[i].strip().partition(":")
                item[k.strip()] = _scalar(v.strip())
                i += 1
            out.append(item)
        else:
            out.append(_scalar(first))
            i += 1
    return out, i
