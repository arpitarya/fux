"""jsonldoc / svgdoc / imagedoc — three built-in decoders added on 2026-08-29
for `.jsonl`, `.svg`, `.png`/`.jpg`/`.jpeg`/`.gif`.

Shipped as built-ins (`fux.decode.BUILTIN_MODULES`), which — per [ADR-TYPES](
../../docs/adr/0031_types-list.md) decision 1 — automatically widens
`DEFAULT_TYPES` to admit these extensions, reversing the SVG half of that
record's decision 5. These tests load the real committed copy from this
repo's `.fux/decoders/` the same way `fux ingest` does — through
`registry(root)` — so what is under test is the file that actually runs, not
the packaged built-in.

Fixtures are built here rather than committed as binaries, for the same
reason `test_formats.py` gives: a committed `.png` is opaque in a diff.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

from fux.decode import decode

ROOT = Path(__file__).resolve().parents[2]

# -- jsonl -------------------------------------------------------------


def test_jsonl_walks_each_line_as_its_own_record():
    raw = (
        b'{"role": "user", "text": "how do I drain the broker queue"}\n'
        b'{"role": "assistant", "text": "stop consumers first, then drain"}\n'
    )
    out = decode(raw, "chat.jsonl", ROOT)
    assert "drain the broker queue" in out
    assert "stop consumers first, then drain" in out


def test_jsonl_drops_ids_and_timestamps_like_json_does():
    raw = b'{"id": "3f9a8b7c", "text": "thanks", "ts": "2026-08-29T10:00:00Z"}\n'
    out = decode(raw, "chat.jsonl", ROOT)
    assert "3f9a8b7c" not in out
    assert "2026-08-29T10:00:00Z" not in out
    assert "thanks" in out


def test_jsonl_skips_one_bad_line_without_losing_the_rest():
    raw = b'{"text": "first line ok"}\nnot json at all\n{"text": "third line ok"}\n'
    out = decode(raw, "chat.jsonl", ROOT)
    assert "first line ok" in out
    assert "third line ok" in out


def test_jsonl_is_deterministic():
    raw = b'{"b": "second", "a": "first"}\n'
    assert decode(raw, "x.jsonl", ROOT) == decode(raw, "x.jsonl", ROOT)


def test_jsonl_garbage_returns_none():
    assert decode(b"\x00\xff not this format\xfe", "broken.jsonl", ROOT) is None


def test_jsonl_all_bad_lines_returns_none():
    assert decode(b"not json\nalso not json\n", "broken.jsonl", ROOT) is None


# -- svg -----------------------------------------------------------------

SVG = b"""<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">
  <title>Broker failover diagram</title>
  <desc>Shows the primary and replica broker nodes.</desc>
  <g>
    <rect x="0" y="0" width="50" height="20"/>
    <title>Primary node</title>
    <text x="5" y="15">Primary <tspan>(active)</tspan></text>
  </g>
</svg>"""


def test_svg_root_title_becomes_the_heading():
    out = decode(SVG, "diagram.svg", ROOT)
    assert "# Broker failover diagram" in out


def test_svg_desc_and_nested_labels_are_body_prose():
    out = decode(SVG, "diagram.svg", ROOT)
    assert "Shows the primary and replica broker nodes." in out
    assert "Primary node" in out


def test_svg_text_and_tspan_merge_without_duplication():
    out = decode(SVG, "diagram.svg", ROOT)
    assert out.count("active") == 1
    assert "Primary (active)" in out


def test_svg_with_no_labels_returns_none():
    bare = b'<svg xmlns="http://www.w3.org/2000/svg"><rect width="1" height="1"/></svg>'
    assert decode(bare, "bare.svg", ROOT) is None


def test_svg_with_doctype_returns_none():
    raw = (
        b'<?xml version="1.0"?><!DOCTYPE svg><svg xmlns="http://www.w3.org/2000/svg">'
        b"<title>x</title></svg>"
    )
    assert decode(raw, "doctype.svg", ROOT) is None


def test_svg_garbage_returns_none():
    assert decode(b"\x00\xff not xml at all", "broken.svg", ROOT) is None


# -- images --------------------------------------------------------------


def _png_chunk(ctype: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + ctype
        + payload
        + struct.pack(">I", zlib.crc32(ctype + payload))
    )


def _make_png(text_chunks) -> bytes:
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    body = _png_chunk(b"IHDR", ihdr)
    for keyword, text, mode in text_chunks:
        if mode == "tEXt":
            body += _png_chunk(b"tEXt", keyword.encode("latin-1") + b"\x00" + text.encode("latin-1"))
        elif mode == "zTXt":
            comp = zlib.compress(text.encode("latin-1"))
            body += _png_chunk(b"zTXt", keyword.encode("latin-1") + b"\x00\x00" + comp)
        elif mode == "iTXt":
            payload = keyword.encode("latin-1") + b"\x00\x00\x00\x00\x00" + text.encode("utf-8")
            body += _png_chunk(b"iTXt", payload)
    body += _png_chunk(b"IDAT", zlib.compress(b"\x00"))
    body += _png_chunk(b"IEND", b"")
    return sig + body


def test_png_text_chunks_of_every_kind():
    png = _make_png(
        [
            ("Title", "Failover Runbook Diagram", "tEXt"),
            ("Description", "generated for the SRE onboarding doc", "zTXt"),
            ("Comment", "exported from Excalidraw — café build", "iTXt"),
        ]
    )
    out = decode(png, "runbook.png", ROOT)
    assert "# Failover Runbook Diagram" in out
    assert "generated for the SRE onboarding doc" in out
    assert "café build" in out  # iTXt is UTF-8; the umlaut must survive


def test_png_with_no_text_chunks_returns_none():
    assert decode(_make_png([]), "blank.png", ROOT) is None


def test_png_garbage_returns_none():
    assert decode(b"\x89PNG\r\n\x1a\n" + b"\xff" * 40, "broken.png", ROOT) is None


def _make_jpeg_with_exif(description: str, comment: str) -> bytes:
    desc_bytes = description.encode("ascii") + b"\x00"
    ifd_header = struct.pack("<H", 1)
    next_ifd = struct.pack("<I", 0)
    ifd_offset = 8
    data_offset = ifd_offset + len(ifd_header) + 12 + len(next_ifd)
    ifd_body = struct.pack("<HHII", 0x010E, 2, len(desc_bytes), data_offset)
    tiff = b"II" + struct.pack("<HI", 42, ifd_offset) + ifd_header + ifd_body + next_ifd + desc_bytes
    app1 = b"Exif\x00\x00" + tiff
    app1_seg = b"\xff\xe1" + struct.pack(">H", len(app1) + 2) + app1
    com_bytes = comment.encode("latin-1")
    com_seg = b"\xff\xfe" + struct.pack(">H", len(com_bytes) + 2) + com_bytes
    return b"\xff\xd8" + app1_seg + com_seg + b"\xff\xda\x00\x02\x00" + b"\xff\xd9"


def test_jpeg_exif_description_and_comment():
    jpeg = _make_jpeg_with_exif("Broker rack, row 4", "shot for the incident report")
    out = decode(jpeg, "rack.jpg", ROOT)
    assert "Broker rack, row 4" in out
    assert "shot for the incident report" in out


def test_jpeg_garbage_returns_none():
    assert decode(b"\xff\xd8\xff\xff\xff\xff", "broken.jpg", ROOT) is None


def _gif_comment_block(text: bytes) -> bytes:
    out = bytearray(b"\x21\xfe")
    for i in range(0, len(text), 250):
        chunk = text[i : i + 250]
        out.append(len(chunk))
        out += chunk
    out.append(0)
    return bytes(out)


def _make_gif(comment: bytes) -> bytes:
    header = b"GIF89a" + struct.pack("<HH", 1, 1) + bytes([0x00, 0, 0])
    body = _gif_comment_block(comment) if comment else b""
    img_desc = b"\x2c" + struct.pack("<HHHH", 0, 0, 1, 1) + bytes([0x00])
    lzw = bytes([2, 2]) + b"\x44\x01" + bytes([0])
    trailer = b"\x3b"
    return header + body + img_desc + lzw + trailer


def test_gif_comment_extension():
    gif = _make_gif(b"frame captured during the outage window")
    out = decode(gif, "outage.gif", ROOT)
    assert "frame captured during the outage window" in out


def test_gif_with_no_comment_returns_none():
    assert decode(_make_gif(b""), "plain.gif", ROOT) is None


def test_gif_garbage_returns_none():
    assert decode(b"GIF89a" + b"\xff" * 20, "broken.gif", ROOT) is None
