"""JSON Lines (`.jsonl`) -> Markdown. One JSON value per line, same reasoning
as `json`: keys become headings, string values become body, everything
else is dropped.

**Not the same decoder as `.json`.** A `.jsonl` file is not one JSON document
— `json.loads` on the whole file fails on any file with more than one line —
it is a stream of independent records, most commonly one row per line from a
log, an export, or a chat/eval transcript. That shape is exactly a JSON array
without the enclosing `[` `]` and `,`, so each line is parsed and walked on
its own; one bad line (a truncated final line from a still-writing process is
the common case) is skipped rather than failing the whole file.

Deliberately its own module, copying `json`'s `_walk` rather than
importing it — the override seam works by module name, so a consumer who
wants different JSONL handling must be able to take that and nothing else
(same reasoning `toml` states for why it does not import `json._walk`).
"""

from __future__ import annotations

import json

# Imports are ABSOLUTE, not relative, and that is what makes this file work in
# both places it runs: as a package module, and as a consumer copy in
# `.fux/decoders/` loaded by path. A path-loaded file has no parent package, so
# `from . import json` raises `attempted relative import with no known
# parent package` — the copy would be dead on arrival.
from fux.decode.json import MAX_DEPTH, _label, _prose

#: **The reuse key's handle on this decoder** (W-166). Bump it by hand in the
#: same change as any edit that can change what `decode()` returns, and the next
#: `fux ingest` re-extracts the documents bound to THIS decoder and no others.
#: Leaving it alone is the claim that the edit cannot move a byte of output.
#: `tests/decode/test_decoder_versions.py` fails on a changed module that did
#: not bump it. [SR-DECODE](../../../records/0139_decode.md) decision 11a.
VERSION = 1

EXTENSIONS = (".jsonl",)

#: Records past this are a dataset rather than a document — the same judgement
#: `csv.MAX_ROWS` makes for the row-oriented shape this format shares.
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
    # 🔴 **A `# <filename>` TITLE, and the sibling records under it.**
    # Without it the first `## Record 1` becomes the document's TITLE --
    # `extract.py` takes the shallowest heading -- so every `.jsonl` in a
    # corpus was titled "Record 1" in a heavily-weighted field. Measured
    # 2026-09-11 over this repo: **96 documents** (86 `.jsonl`, 10 `.json`)
    # lost a real title to a generic one, and **not one gained anything**.
    # It is also exactly what `DECODER-SKILL.md` tells a decoder author to
    # do -- *emit them as SIBLINGS at one level under a `# <filename>`
    # title* -- so the shipped decoder was violating its own documented
    # contract.
    lines: list[str] = [f"# {rel_path.rsplit('/', 1)[-1]}"]
    for index, record in enumerate(records, start=1):
        block: list[str] = []
        _walk(record, block, depth=2, label=None)
        if not block:
            continue
        # ⚠ **The record boundary is the chunk boundary, and it used to be
        # invisible.** Walking the whole list under one `label=None` emitted no
        # heading between records, so `refer/_chunk.py` saw one undivided
        # passage and a citation spanning six unrelated log lines read as one
        # statement. A JSONL record is the natural unit of this format — one
        # line in, one section out.
        lines.append(f"## Record {index}")
        lines.extend(block)
    body = "\n\n".join(lines)
    return body if body.strip() else None


def _walk(node, out: list[str], *, depth: int, label: str | None) -> None:
    if depth > MAX_DEPTH:
        return
    if isinstance(node, dict):
        if label:
            out.append(_label(label, depth))
        for key in sorted(node, key=str):
            _walk(node[key], out, depth=depth + 1, label=str(key))
        return
    if isinstance(node, list):
        if label:
            out.append(_label(label, depth))
        for item in node:
            _walk(item, out, depth=depth + 1, label=None)
        return
    text = _prose(node)
    if text:
        out.append(f"**{label}:** {text}" if label else text)
