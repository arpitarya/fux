"""Generic XML -> Markdown — DocBook, OpenAPI, Maven poms, RSS, anything.

Element names become headings and text becomes body, on the same reasoning as
`jsondoc`: the name of a thing describes the thing under it.

⚠ **The DOCTYPE refusal in `_xml.py` applies here and is the point.** A
hand-written XML document is the most likely place in the whole corpus to
carry an entity declaration, which is both the billion-laughs vector and the
XXE one. A DTD-validated config that gets skipped is a small loss; a decoder
that fetches a URL during ingest breaks **L4** without ever calling a socket
we wrote.
"""

from __future__ import annotations

# Imports are ABSOLUTE, not relative, and that is what makes this file work in
# both places it runs: as a package module, and as a consumer copy in
# `.fux/decoders/` loaded by path. A path-loaded file has no parent package, so
# `from . import _xml` raises `attempted relative import with no known parent
# package` — the copy would be dead on arrival. Absolute imports mean the file
# fux ships and the file you edit are byte-identical (ADR-DECODE decision 11).
from fux.decode import _xml
from fux.decode.jsondoc import MAX_DEPTH

EXTENSIONS = (".xml",)

#: An attribute value long enough to be a sentence is prose (a `description=`,
#: a `title=`); shorter ones are ids, types and flags.
MIN_ATTR_LEN = 12


def decode(raw: bytes, rel_path: str) -> str | None:
    try:
        root = _xml.parse(raw)
    except _xml.UnsafeXml:
        return None
    lines: list[str] = []
    _walk(root, lines, depth=1)
    body = "\n\n".join(lines)
    return body if body.strip() else None


def _walk(element, out: list[str], *, depth: int) -> None:
    if depth > MAX_DEPTH:
        return
    name = _xml.local(element.tag)
    children = list(element)

    own_text = " ".join((element.text or "").split())
    if own_text:
        out.append(f"**{name}:** {own_text}")
    elif children:
        out.append("#" * min(depth, 6) + " " + name)

    # `element.attrib` is a dict in document order; sorted so two serialisations
    # of one document decode identically (L3).
    for key in sorted(element.attrib):
        value = " ".join(element.attrib[key].split())
        if len(value) >= MIN_ATTR_LEN:
            out.append(f"**{key}:** {value}")

    for child in children:
        _walk(child, out, depth=depth + 1)
        # Text after a child element — `<p>a <b>x</b> tail</p>` — is real prose
        # and is the one thing a naive element walk always loses.
        tail = " ".join((child.tail or "").split())
        if tail:
            out.append(tail)
