"""JSON Lines (`.jsonl`) -> Markdown. One JSON value per line, same reasoning
as `jsondoc`: keys become headings, string values become body, everything
else is dropped.

**Not the same decoder as `.json`.** A `.jsonl` file is not one JSON document
— `json.loads` on the whole file fails on any file with more than one line —
it is a stream of independent records, most commonly one row per line from a
log, an export, or a chat/eval transcript. That shape is exactly a JSON array
without the enclosing `[` `]` and `,`, so each line is parsed and walked on
its own; one bad line (a truncated final line from a still-writing process is
the common case) is skipped rather than failing the whole file.

Deliberately its own module, copying `jsondoc`'s `_walk` rather than
importing it — the override seam works by module name, so a consumer who
wants different JSONL handling must be able to take that and nothing else
(same reasoning `tomldoc` states for why it does not import `jsondoc._walk`).
"""

from __future__ import annotations

import json

# Imports are ABSOLUTE, not relative, and that is what makes this file work in
# both places it runs: as a package module, and as a consumer copy in
# `.fux/decoders/` loaded by path. A path-loaded file has no parent package, so
# `from . import jsondoc` raises `attempted relative import with no known
# parent package` — the copy would be dead on arrival.
from fux.decode.jsondoc import MAX_DEPTH, _prose

EXTENSIONS = (".jsonl",)

#: Records past this are a dataset rather than a document — the same judgement
#: `csvdoc.MAX_ROWS` makes for the row-oriented shape this format shares.
MAX_RECORDS = 500


def decode(raw: bytes, rel_path: str) -> str | None:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None
    records = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # one bad line in a stream must not drop the rest
        if len(records) >= MAX_RECORDS:
            break
    if not records:
        return None
    lines: list[str] = []
    _walk(records, lines, depth=1, label=None)
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
    text = _prose(node)
    if text:
        out.append(f"**{label}:** {text}" if label else text)
