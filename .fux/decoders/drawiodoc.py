"""`.drawio` / `.dio` -> Markdown — the labels in an architecture diagram.

Niche and worth it: a team's architecture lives in diagrams, and the box labels
are exactly the terms someone searches for. Today they are invisible.

The format is XML, but the interesting part is usually **deflated and
base64'd** inside a `<diagram>` element — draw.io compresses the model by
default. `zlib` and `base64` are both stdlib, so this stays `$0`; the only
subtlety is that the payload is *raw* deflate with no zlib header, which needs
a negative window size.

⚠ **Labels are HTML fragments**, so they are converted through `htmldoc` rather
than stripped by hand — one HTML implementation, per ADR-DECODE.
"""

from __future__ import annotations

import base64
import re
import zlib
from urllib.parse import unquote

# Imports are ABSOLUTE, not relative, and that is what makes this file work in
# both places it runs: as a package module, and as a consumer copy in
# `.fux/decoders/` loaded by path. A path-loaded file has no parent package, so
# `from . import _xml` raises `attempted relative import with no known parent
# package` — the copy would be dead on arrival. Absolute imports mean the file
# fux ships and the file you edit are byte-identical (ADR-DECODE decision 11).
from fux.decode import _xml
from fux.decode.htmldoc import html_to_markdown

EXTENSIONS = (".drawio", ".dio")

MAX_INFLATED = 16 * 1024 * 1024
_TAG_RE = re.compile(r"<[^>]+>")


def decode(raw: bytes, rel_path: str) -> str | None:
    try:
        root = _xml.parse(raw)
    except _xml.UnsafeXml:
        return None

    blocks: list[str] = []
    for diagram in root.iter():
        if _xml.local(diagram.tag) != "diagram":
            continue
        name = ""
        for key, value in diagram.attrib.items():
            if _xml.local(key) == "name":
                name = value
        model = _model(diagram)
        if model is None:
            continue
        labels = _labels(model)
        if not labels:
            continue
        blocks.append(f"## {name}" if name else "## Diagram")
        blocks.extend(f"- {label}" for label in labels)

    body = "\n\n".join(blocks)
    return body if body.strip() else None


def _model(diagram):
    """The `mxGraphModel` element, inflating the compressed payload if needed."""
    for child in diagram:
        if _xml.local(child.tag) == "mxGraphModel":
            return child  # stored uncompressed; nothing to do
    payload = (diagram.text or "").strip()
    if not payload:
        return None
    try:
        compressed = base64.b64decode(payload, validate=True)
        # -15: raw deflate, no zlib header. draw.io writes it this way and a
        # default-window inflate simply fails, which reads as "not a diagram".
        inflated = zlib.decompressobj(-15).decompress(compressed, MAX_INFLATED)
    except (ValueError, zlib.error):
        return None
    try:
        return _xml.parse_text(unquote(inflated.decode("utf-8", errors="replace")))
    except _xml.UnsafeXml:
        return None


def _labels(model) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    # Document order, not sorted: a diagram's cells are laid out in a meaningful
    # sequence and `extract.py` scores earlier text slightly higher.
    for cell in model.iter():
        if _xml.local(cell.tag) != "mxCell":
            continue
        value = ""
        for key, attr in cell.attrib.items():
            if _xml.local(key) == "value":
                value = attr
        if not value.strip():
            continue
        text = _plain(value)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _plain(value: str) -> str:
    if "<" not in value:
        return " ".join(value.split())
    converted = html_to_markdown(value)
    return " ".join(_TAG_RE.sub(" ", converted).split())
