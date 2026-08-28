"""TOML -> Markdown. Free: `tomllib` is stdlib on the Python L7 already requires.

Same shape as `jsondoc` and for the same reason — a table name is a heading, a
string value is prose, a number is not a word. It is a separate module rather
than a branch inside `jsondoc` because the override seam works **by module
name**: a consumer who wants different TOML handling must be able to take that
and nothing else.
"""

from __future__ import annotations

import tomllib

# Imports are ABSOLUTE, not relative, and that is what makes this file work in
# both places it runs: as a package module, and as a consumer copy in
# `.fux/decoders/` loaded by path. A path-loaded file has no parent package, so
# `from . import _xml` raises `attempted relative import with no known parent
# package` — the copy would be dead on arrival. Absolute imports mean the file
# fux ships and the file you edit are byte-identical (ADR-DECODE decision 11).
from fux.decode.jsondoc import MAX_DEPTH, _prose

EXTENSIONS = (".toml",)


def decode(raw: bytes, rel_path: str) -> str | None:
    try:
        data = tomllib.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None
    lines: list[str] = []
    _walk(data, lines, depth=1, label=None)
    body = "\n\n".join(lines)
    return body if body.strip() else None


def _walk(node, out: list[str], *, depth: int, label: str | None) -> None:
    if depth > MAX_DEPTH:
        return
    if isinstance(node, dict):
        if label:
            out.append("#" * min(depth, 6) + " " + label)
        for key in sorted(node, key=str):
            _walk(node[key], out, depth=depth + 1, label=str(key))
        return
    if isinstance(node, list):
        if label:
            out.append("#" * min(depth, 6) + " " + label)
        for item in node:
            _walk(item, out, depth=depth + 1, label=None)
        return
    # `tomllib` returns real `datetime` objects for dates, so unlike JSON the
    # timestamp noise never reaches `_prose` as a string — it is dropped here
    # by not being a `str` at all.
    text = _prose(node)
    if text:
        out.append(f"**{label}:** {text}" if label else text)
