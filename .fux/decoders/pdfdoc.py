"""PDF -> Markdown. **Text layer only**, and the refusal is as important as the
extraction.

A PDF has no paragraphs, no headings, and no reading order — it has *drawing
instructions*. `Tj` and `TJ` place glyphs at coordinates, and the "text" is
whatever those instructions spell out. Everything a reader perceives as
structure is inferred.

What this module does, in order:

1. Walk the cross-reference-free way: scan every `stream ... endstream`, inflate
   what inflates. **Deliberately not an xref parse.** A real PDF library
   follows the xref table, then object streams, then compressed xref streams —
   three formats to get right, all of which fail on the malformed files that
   are exactly what a corpus contains. Scanning finds the text in a damaged
   file that a conformant reader refuses.
2. Pull `Tj`/`TJ` operands out of each content stream.
3. Map bytes to characters through the font's `ToUnicode` CMap when there is
   one, because a subset font's byte `0x03` means whatever the CMap says and
   nothing otherwise.

⚠ **A PDF with no text layer returns `None`, and that is the point.** It means
*a model must read this* — a scan, a slide export, a signed form — and it is
what feeds the enrichment queue. A PDF whose text layer fails to *parse* is a
different thing: a decode failure. The two are distinguished below, because
conflating them would hide a real defect inside a normal-looking outcome.

⚠ **This will not match a dedicated library on hard files.** Ligatures, RTL,
multi-column reading order and CID fonts are all approximated. For a *ranking*
index that is usually enough — the terms are there even when the layout is not.
A consumer who needs better writes `.fux/decoders/pdfdoc.py` around `pypdf`,
which is the whole reason the override seam exists (ADR-DECODE §12).
"""

from __future__ import annotations

import re
import zlib

EXTENSIONS = (".pdf",)

MAX_STREAMS = 5000
MAX_INFLATED = 64 * 1024 * 1024
MAX_TEXT_CHARS = 2_000_000

_STREAM_RE = re.compile(rb"stream\r?\n(.*?)endstream", re.DOTALL)
#: `(literal) Tj` and `[(a) -250 (b)] TJ` — the two text-showing operators that
#: carry essentially all real content. `'` and `"` also show text but are rare
#: outside generated forms.
_TJ_RE = re.compile(rb"\((?:\\.|[^()\\])*\)|<[0-9A-Fa-f\s]+>")
_SHOW_RE = re.compile(rb"((?:\[[^\]]*\]|\((?:\\.|[^()\\])*\))\s*(?:TJ|Tj|'|\"))", re.DOTALL)
_TD_RE = re.compile(rb"(T\*|Td|TD|TL)")
_BT_RE = re.compile(rb"BT(.*?)ET", re.DOTALL)
#: `beginbfchar`/`beginbfrange` blocks inside a ToUnicode CMap.
_BFCHAR_RE = re.compile(rb"beginbfchar(.*?)endbfchar", re.DOTALL)
_BFRANGE_RE = re.compile(rb"beginbfrange(.*?)endbfrange", re.DOTALL)
_HEX_RE = re.compile(rb"<([0-9A-Fa-f]+)>")

_ESCAPES = {
    b"n": "\n", b"r": "\r", b"t": "\t", b"b": "\b", b"f": "\f",
    b"(": "(", b")": ")", b"\\": "\\",
}


class NotAPdf(ValueError):
    """The bytes are not a PDF at all — a mislabelled file."""


def decode(raw: bytes, rel_path: str) -> str | None:
    if not raw.lstrip()[:5].startswith(b"%PDF-"):
        return None
    streams = _streams(raw)
    cmap = _to_unicode(streams)
    lines: list[str] = []
    for data in streams:
        lines.extend(_text_from(data, cmap))
        if sum(len(line) for line in lines) > MAX_TEXT_CHARS:
            break

    text = _paragraphs(lines)
    if not text.strip():
        # No text layer. NOT an error: a scanned page is a real document that
        # needs a model, and `None` is exactly that signal.
        return None
    return text


def _streams(raw: bytes) -> list[bytes]:
    """Every stream body, inflated where it inflates.

    Streams that are not Flate — images, fonts, raw data — simply fail to
    inflate and are dropped. That is cheaper and more robust than reading each
    object's `/Filter`, which requires the object parsing this module avoids.
    """
    out: list[bytes] = []
    for match in _STREAM_RE.finditer(raw):
        if len(out) >= MAX_STREAMS:
            break
        body = match.group(1)
        try:
            out.append(zlib.decompressobj().decompress(body, MAX_INFLATED))
        except zlib.error:
            if b"BT" in body and b"ET" in body:
                out.append(body)  # an uncompressed content stream
    return out


def _to_unicode(streams: list[bytes]) -> dict[bytes, str]:
    """The union of every `ToUnicode` CMap in the file.

    Merging all of them is an approximation: a document with two subset fonts
    that assign different meanings to the same byte will get one of them wrong.
    Reading per-font mappings needs the resource dictionary, and therefore the
    object graph this module deliberately does not parse. **Stated rather than
    hidden** — it is the known cost of the scanning approach.
    """
    cmap: dict[bytes, str] = {}
    for data in streams:
        if b"beginbfchar" not in data and b"beginbfrange" not in data:
            continue
        for block in _BFCHAR_RE.findall(data):
            hexes = _HEX_RE.findall(block)
            for i in range(0, len(hexes) - 1, 2):
                src, dst = hexes[i], hexes[i + 1]
                cmap.setdefault(_unhex(src), _utf16(dst))
        for block in _BFRANGE_RE.findall(data):
            hexes = _HEX_RE.findall(block)
            for i in range(0, len(hexes) - 2, 3):
                low, high, dst = hexes[i], hexes[i + 1], hexes[i + 2]
                try:
                    start, end = int(low, 16), int(high, 16)
                except ValueError:
                    continue
                if end - start > 65535:
                    continue
                base = _utf16(dst)
                if len(base) != 1:
                    continue
                width = len(low) // 2
                for offset in range(end - start + 1):
                    key = (start + offset).to_bytes(width, "big")
                    cmap.setdefault(key, chr(ord(base) + offset))
    return cmap


def _unhex(value: bytes) -> bytes:
    try:
        return bytes.fromhex(value.decode("ascii"))
    except ValueError:
        return b""


def _utf16(value: bytes) -> str:
    raw = _unhex(value)
    try:
        return raw.decode("utf-16-be", errors="replace")
    except (UnicodeDecodeError, LookupError):
        return ""


def _text_from(data: bytes, cmap: dict[bytes, str]) -> list[str]:
    """Text-showing operands inside `BT ... ET` blocks, one entry per line break.

    Line breaks come from the positioning operators (`Td`, `TD`, `T*`), which is
    the only structural signal available without laying out glyph coordinates.
    """
    out: list[str] = []
    for block in _BT_RE.findall(data):
        current: list[str] = []
        position = 0
        for match in _SHOW_RE.finditer(block):
            if _TD_RE.search(block, position, match.start()) and current:
                out.append("".join(current))
                current = []
            position = match.end()
            current.append(_operand(match.group(1), cmap))
        if current:
            out.append("".join(current))
    return out


def _operand(operand: bytes, cmap: dict[bytes, str]) -> str:
    pieces: list[str] = []
    for token in _TJ_RE.findall(operand):
        if token.startswith(b"<"):
            raw = _unhex(bytes(c for c in token[1:-1] if not chr(c).isspace()))
            pieces.append(_mapped(raw, cmap))
        else:
            pieces.append(_literal(token[1:-1], cmap))
    return "".join(pieces)


def _literal(body: bytes, cmap: dict[bytes, str]) -> str:
    out: list[str] = []
    index = 0
    while index < len(body):
        char = body[index : index + 1]
        if char == b"\\" and index + 1 < len(body):
            nxt = body[index + 1 : index + 2]
            if nxt in _ESCAPES:
                out.append(_ESCAPES[nxt])
                index += 2
                continue
            if nxt.isdigit():  # octal
                digits = body[index + 1 : index + 4]
                octal = bytes(c for c in digits if 48 <= c <= 55)
                try:
                    out.append(chr(int(octal, 8)))
                except ValueError:
                    pass
                index += 1 + len(octal)
                continue
            index += 2
            continue
        out.append(_mapped(char, cmap))
        index += 1
    return "".join(out)


def _mapped(raw: bytes, cmap: dict[bytes, str]) -> str:
    if not raw:
        return ""
    if cmap:
        out: list[str] = []
        index = 0
        while index < len(raw):
            two = raw[index : index + 2]
            one = raw[index : index + 1]
            if two in cmap:
                out.append(cmap[two])
                index += 2
            elif one in cmap:
                out.append(cmap[one])
                index += 1
            else:
                out.append(one.decode("latin-1", errors="replace"))
                index += 1
        return "".join(out)
    return raw.decode("latin-1", errors="replace")


def _paragraphs(lines: list[str]) -> str:
    """Lines -> paragraphs, joining hyphenated line breaks.

    A PDF breaks words across lines with a hyphen; leaving them produces terms
    like "run-" and "book" that match nothing. Rejoining is the single highest
    -value cleanup available at this level and costs one branch.
    """
    blocks: list[str] = []
    current: list[str] = []
    for line in lines:
        text = " ".join(line.split())
        if not text:
            if current:
                blocks.append(_join(current))
                current = []
            continue
        current.append(text)
    if current:
        blocks.append(_join(current))
    return "\n\n".join(b for b in blocks if b.strip())


def _join(lines: list[str]) -> str:
    out = ""
    for line in lines:
        if out.endswith("-"):
            out = out[:-1] + line
        elif out:
            out += " " + line
        else:
            out = line
    return out
