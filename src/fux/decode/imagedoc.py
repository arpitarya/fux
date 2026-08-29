"""PNG / JPEG / GIF -> Markdown, **embedded text metadata only**.

A raster image's pixels are not a document — there are no words to extract
from a photograph, only from what a human or a tool wrote *about* it. Three
containers carry that:

* PNG `tEXt`/`zTXt`/`iTXt` chunks (`Title`, `Author`, `Description`,
  `Comment`, ...) — the informal keyword registry in the PNG spec.
* JPEG APP1/EXIF `ImageDescription`, `Artist`, `Copyright` (ASCII IFD0 tags
  only — see the limitation below), and `COM` comment segments.
* GIF comment extension blocks (label `0xFE`).

**Format detection is by magic bytes, not by `rel_path`'s extension** — cheap,
and it means a mislabelled file still decodes correctly rather than silently
producing nothing.

⚠ **`.png`/`.jpg`/`.jpeg`/`.gif` joined `DEFAULT_TYPES` on 2026-08-29**
(Arpit, in the same change this decoder shipped) — a genuinely new addition,
not a reversal: [ADR-TYPES](../../../docs/adr/0031_types-list.md) never named
raster images. **Why this is safe where the raw-bytes case measured in that
record was not**: a pure-pixel image with none of the metadata above decodes
to `None` and is **not indexed at all** — there is no equivalent of the `.json`
problem where undecoded bytes inflated `df` for every document, because
nothing is admitted unless a human actually wrote words into the file.

⚠ **This is a hand-rolled minimal reader, not a full parser, because L1
forbids the one library (Pillow) that would make this easy.** Known
limitations, stated rather than hidden:

* JPEG EXIF: only IFD0 ASCII tags (`ImageDescription`, `Artist`,
  `Copyright`). `UserComment` and the Windows `XP*` tags use encodings
  (an 8-byte character-code prefix, UTF-16LE) this module does not decode,
  and the Exif SubIFD is not walked at all.
* PNG `iTXt`/`zTXt` compressed text is capped at `MAX_INFLATED` bytes, the
  same defence `pdfdoc` uses against a decompression bomb.
* Multiple JPEG `COM` segments: only the first is kept.

A consumer who needs more writes `.fux/decoders/imagedoc.py` around a library
of their choosing — the same override seam `pdfdoc.py` documents.
"""

from __future__ import annotations

import struct
import zlib

EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif")

MAX_INFLATED = 1 * 1024 * 1024

_PNG_SIG = b"\x89PNG\r\n\x1a\n"
_JPEG_SOI = b"\xff\xd8"
_GIF_SIGS = (b"GIF87a", b"GIF89a")

_JPEG_APP1 = 0xE1
_JPEG_COM = 0xFE
_JPEG_SOS = 0xDA
_JPEG_ASCII_TAGS = {0x010E: "ImageDescription", 0x013B: "Artist", 0x8298: "Copyright"}


def decode(raw: bytes, rel_path: str) -> str | None:
    if raw.startswith(_PNG_SIG):
        fields = _png_text(raw)
    elif raw.startswith(_JPEG_SOI):
        fields = _jpeg_text(raw)
    elif raw[:6] in _GIF_SIGS:
        fields = _gif_text(raw)
    else:
        return None
    lines: list[str] = []
    for key in sorted(fields):
        value = fields[key]
        if not value:
            continue
        lines.append(f"# {value}" if key.lower() == "title" else f"**{key}:** {value}")
    body = "\n\n".join(lines)
    return body if body.strip() else None


# -- PNG ---------------------------------------------------------------------


def _png_chunks(data: bytes):
    pos = len(_PNG_SIG)
    n = len(data)
    while pos + 8 <= n:
        length = int.from_bytes(data[pos : pos + 4], "big")
        ctype = data[pos + 4 : pos + 8]
        pos += 8
        if length < 0 or pos + length + 4 > n:
            break
        yield ctype, data[pos : pos + length]
        pos += length + 4  # skip the trailing CRC
        if ctype == b"IEND":
            break


def _png_text(data: bytes) -> dict[str, str]:
    out: dict[str, str] = {}
    for ctype, payload in _png_chunks(data):
        try:
            if ctype == b"tEXt":
                keyword, _, text = payload.partition(b"\x00")
                out.setdefault(keyword.decode("latin-1"), text.decode("latin-1"))
            elif ctype == b"zTXt":
                keyword, _, rest = payload.partition(b"\x00")
                if len(rest) < 1 or rest[0] != 0:  # only zlib (method 0) is defined
                    continue
                text = zlib.decompress(rest[1:], 0, MAX_INFLATED).decode("latin-1")
                out.setdefault(keyword.decode("latin-1"), text)
            elif ctype == b"iTXt":
                out.update(_itxt(payload))
        except (UnicodeDecodeError, zlib.error, IndexError, ValueError):
            continue  # one malformed chunk must not drop the rest of the file
    return {k: " ".join(v.split()) for k, v in out.items()}


def _itxt(payload: bytes) -> dict[str, str]:
    keyword, _, rest = payload.partition(b"\x00")
    if len(rest) < 2:
        return {}
    compressed, method = rest[0], rest[1]
    rest = rest[2:]
    _lang, _, rest = rest.partition(b"\x00")
    _translated, _, text_bytes = rest.partition(b"\x00")
    if compressed:
        if method != 0:
            return {}
        text_bytes = zlib.decompress(text_bytes, 0, MAX_INFLATED)
    return {keyword.decode("latin-1"): text_bytes.decode("utf-8")}


# -- JPEG ----------------------------------------------------------------


def _jpeg_segments(data: bytes):
    pos = 2  # past the SOI marker
    n = len(data)
    while pos + 1 < n:
        if data[pos] != 0xFF:
            pos += 1
            continue
        marker = data[pos + 1]
        if marker == 0 or 0xD0 <= marker <= 0xD9:  # no length field on these
            pos += 2
            if marker == _JPEG_SOS:
                break  # compressed scan data follows; nothing after is a segment
            continue
        if pos + 4 > n:
            break
        length = int.from_bytes(data[pos + 2 : pos + 4], "big")
        if length < 2 or pos + 2 + length > n:
            break
        yield marker, data[pos + 4 : pos + 2 + length]
        pos += 2 + length


def _jpeg_text(data: bytes) -> dict[str, str]:
    out: dict[str, str] = {}
    for marker, payload in _jpeg_segments(data):
        try:
            if marker == _JPEG_APP1:
                out.update(_exif_ascii(payload))
            elif marker == _JPEG_COM:
                text = " ".join(payload.decode("latin-1").split())
                if text:
                    out.setdefault("Comment", text)
        except (UnicodeDecodeError, struct.error, IndexError):
            continue
    return out


def _exif_ascii(payload: bytes) -> dict[str, str]:
    if not payload.startswith(b"Exif\x00\x00"):
        return {}
    tiff = payload[6:]
    if len(tiff) < 8 or tiff[:2] not in (b"II", b"MM"):
        return {}
    endian = "<" if tiff[:2] == b"II" else ">"
    if struct.unpack_from(endian + "H", tiff, 2)[0] != 42:
        return {}
    (ifd_offset,) = struct.unpack_from(endian + "I", tiff, 4)
    return _read_ifd0(tiff, ifd_offset, endian)


def _read_ifd0(tiff: bytes, offset: int, endian: str) -> dict[str, str]:
    out: dict[str, str] = {}
    if offset + 2 > len(tiff):
        return out
    (count,) = struct.unpack_from(endian + "H", tiff, offset)
    pos = offset + 2
    for _ in range(count):
        if pos + 12 > len(tiff):
            break
        tag, typ, cnt = struct.unpack_from(endian + "HHI", tiff, pos)
        name = _JPEG_ASCII_TAGS.get(tag)
        if name and typ == 2:  # type 2 == ASCII, the only encoding read here
            value_off = pos + 8
            if cnt <= 4:
                raw = tiff[value_off : value_off + cnt]
            else:
                (data_off,) = struct.unpack_from(endian + "I", tiff, value_off)
                raw = tiff[data_off : data_off + cnt]
            text = raw.split(b"\x00", 1)[0].decode("ascii", errors="replace").strip()
            if text:
                out[name] = text
        pos += 12
    return out


# -- GIF -----------------------------------------------------------------


def _gif_text(data: bytes) -> dict[str, str]:
    n = len(data)
    if len(data) < 13:
        return {}
    packed = data[10]
    pos = 13
    if packed & 0x80:
        pos += 3 * (2 ** ((packed & 0x07) + 1))
    comments: list[str] = []
    while pos < n:
        marker = data[pos]
        if marker == 0x3B:  # trailer
            break
        if marker == 0x21:  # extension
            if pos + 2 > n:
                break
            label = data[pos + 1]
            pos += 2
            pos, chunk = _skip_subblocks(data, pos)
            if label == 0xFE:
                text = " ".join(bytes(chunk).decode("ascii", errors="replace").split())
                if text:
                    comments.append(text)
            continue
        if marker == 0x2C:  # image descriptor
            if pos + 10 > n:
                break
            local_packed = data[pos + 9]
            pos += 10
            if local_packed & 0x80:
                pos += 3 * (2 ** ((local_packed & 0x07) + 1))
            if pos >= n:
                break
            pos += 1  # LZW minimum code size
            pos, _ = _skip_subblocks(data, pos)
            continue
        break  # an unrecognised byte here means the walk has lost sync
    return {("Comment" if i == 0 else f"Comment {i + 1}"): c for i, c in enumerate(comments)}


def _skip_subblocks(data: bytes, pos: int) -> tuple[int, bytearray]:
    """Consume a GIF sub-block sequence, returning the position after it and
    its concatenated bytes. Shared by extension blocks and image data — both
    use the same length-prefixed-blocks-until-a-zero-length-block grammar.
    """
    n = len(data)
    out = bytearray()
    while pos < n:
        size = data[pos]
        pos += 1
        if size == 0:
            break
        out.extend(data[pos : pos + size])
        pos += size
    return pos, out
