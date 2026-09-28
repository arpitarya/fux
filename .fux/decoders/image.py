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
not a reversal: [SR-TYPES](../../../records/0128_types-list.md) never named
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
  same defence `pdf` uses against a decompression bomb.
* Multiple JPEG `COM` segments: only the first is kept.

A consumer who needs more writes `.fux/decoders/image.py` around a library
of their choosing — the same override seam `pdf.py` documents.
"""

from __future__ import annotations

import struct
import zlib
from fux.constants import fixed
from fux.decode._limits import limit

#: **The reuse key's handle on this decoder** (W-166). Bump it by hand in the
#: same change as any edit that can change what `decode()` returns, and the next
#: `fux ingest` re-extracts the documents bound to THIS decoder and no others.
#: Leaving it alone is the claim that the edit cannot move a byte of output.
#: `tests/decode/test_decoder_versions.py` fails on a changed module that did
#: not bump it. [SR-DECODE](../../../records/0139_decode.md) decision 11a.
VERSION = fixed("decoders.image", "version")  # not bumped by W-225 4a (caps moved, same values) nor 5b (numerals moved, same output)

EXTENSIONS = tuple(fixed("decoders.image", "extensions"))

#: ⚠ **`MAX_INFLATED` is `[limits.image] max_inflated` in .fux/formats.toml** since W-225 stage 4a
#: (SR-LAW-12 decision 9b): read per call through `limit()`, in the extract-config digest.

# Every number the three formats fix -- a signature, a marker, a record layout --
# is `constants.toml [decoders.image]` (SR-LAW-12 decision 6a). A layout is a
# `struct` format, so its size is the offset the walk advances by.
_C = "decoders.image.format"


def _bytes(key: str) -> bytes:
    return fixed(_C, key).encode("latin-1")


_PNG_SIG = _bytes("png_signature")
_PNG_HEAD = struct.Struct(fixed(_C, "png_chunk_head"))  # length, type
_PNG_CRC = struct.calcsize(fixed(_C, "png_chunk_crc"))
_ITXT_FLAGS = struct.Struct(fixed(_C, "itxt_flags"))  # compressed, method

_JPEG_SOI = _bytes("jpeg_soi")
_JPEG_MARKER = struct.Struct(fixed(_C, "jpeg_marker"))  # 0xFF, code
_JPEG_LENGTH = struct.Struct(fixed(_C, "jpeg_length"))  # counts itself
_JPEG_PREFIX = fixed(_C, "jpeg_prefix")
_JPEG_STANDALONE = range(fixed(_C, "jpeg_standalone_first"), fixed(_C, "jpeg_standalone_last") + 1)
_JPEG_APP1 = fixed(_C, "jpeg_app1")
_JPEG_COM = fixed(_C, "jpeg_com")
_JPEG_SOS = fixed(_C, "jpeg_sos")
_EXIF_HEADER = _bytes("exif_header")
_TIFF_ORDERS = {mark.encode("latin-1"): endian for mark, endian in fixed(_C, "tiff_byte_orders").items()}
_TIFF_HEAD = fixed(_C, "tiff_header")  # order mark, magic, IFD0 offset
_TIFF_MAGIC = fixed(_C, "tiff_magic")
_IFD_COUNT = fixed(_C, "ifd_count")
_IFD_ENTRY = fixed(_C, "ifd_entry")  # tag, type, count, value-or-offset
_IFD_OFFSET = fixed(_C, "ifd_offset")
_EXIF_ASCII = fixed(_C, "exif_ascii_type")
_JPEG_ASCII_TAGS = {tag: name for tag, name in fixed(_C, "exif_ascii_tags")}

_GIF_SIGS = tuple(sig.encode("latin-1") for sig in fixed(_C, "gif_signatures"))
_GIF_HEAD = struct.Struct(fixed(_C, "gif_screen"))  # logical screen descriptor
_GIF_EXT = struct.Struct(fixed(_C, "gif_extension"))  # introducer, label
_GIF_IMAGE = struct.Struct(fixed(_C, "gif_image"))  # image descriptor
_GIF_TABLE_FLAG = fixed(_C, "gif_table_flag")
_GIF_TABLE_BITS = fixed(_C, "gif_table_bits")
_GIF_RGB = fixed(_C, "gif_rgb_bytes")
_GIF_TRAILER = fixed(_C, "gif_trailer")
_GIF_EXTENSION = fixed(_C, "gif_extension_introducer")
_GIF_COMMENT = fixed(_C, "gif_comment_label")
_GIF_DESCRIPTOR = fixed(_C, "gif_image_separator")


def decode(raw: bytes, rel_path: str) -> str | None:
    if raw.startswith(_PNG_SIG):
        fields = _png_text(raw)
    elif raw.startswith(_JPEG_SOI):
        fields = _jpeg_text(raw)
    elif raw.startswith(_GIF_SIGS):
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
    while pos + _PNG_HEAD.size <= n:
        length, ctype = _PNG_HEAD.unpack_from(data, pos)
        pos += _PNG_HEAD.size
        if pos + length + _PNG_CRC > n:
            break
        yield ctype, data[pos : pos + length]
        pos += length + _PNG_CRC  # skip the trailing CRC
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
                text = zlib.decompress(rest[1:], 0, limit("image", "max_inflated")).decode("latin-1")
                out.setdefault(keyword.decode("latin-1"), text)
            elif ctype == b"iTXt":
                out.update(_itxt(payload))
        except (UnicodeDecodeError, zlib.error, IndexError, ValueError):
            continue  # one malformed chunk must not drop the rest of the file
    return {k: " ".join(v.split()) for k, v in out.items()}


def _itxt(payload: bytes) -> dict[str, str]:
    keyword, _, rest = payload.partition(b"\x00")
    if len(rest) < _ITXT_FLAGS.size:
        return {}
    compressed, method = _ITXT_FLAGS.unpack_from(rest)
    rest = rest[_ITXT_FLAGS.size :]
    _lang, _, rest = rest.partition(b"\x00")
    _translated, _, text_bytes = rest.partition(b"\x00")
    if compressed:
        if method != 0:
            return {}
        text_bytes = zlib.decompress(text_bytes, 0, limit("image", "max_inflated"))
    return {keyword.decode("latin-1"): text_bytes.decode("utf-8")}


# -- JPEG ----------------------------------------------------------------


def _jpeg_segments(data: bytes):
    pos = len(_JPEG_SOI)
    n = len(data)
    head = _JPEG_MARKER.size
    while pos + head <= n:
        prefix, marker = _JPEG_MARKER.unpack_from(data, pos)
        if prefix != _JPEG_PREFIX:
            pos += 1
            continue
        if marker == 0 or marker in _JPEG_STANDALONE:  # no length field on these
            pos += head
            if marker == _JPEG_SOS:
                break  # compressed scan data follows; nothing after is a segment
            continue
        if pos + head + _JPEG_LENGTH.size > n:
            break
        (length,) = _JPEG_LENGTH.unpack_from(data, pos + head)
        if length < _JPEG_LENGTH.size or pos + head + length > n:
            break
        yield marker, data[pos + head + _JPEG_LENGTH.size : pos + head + length]
        pos += head + length


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
    if not payload.startswith(_EXIF_HEADER):
        return {}
    tiff = payload[len(_EXIF_HEADER) :]
    endian = next((e for mark, e in _TIFF_ORDERS.items() if tiff.startswith(mark)), None)
    if endian is None or len(tiff) < struct.calcsize(endian + _TIFF_HEAD):
        return {}
    _order, magic, ifd_offset = struct.unpack_from(endian + _TIFF_HEAD, tiff)
    if magic != _TIFF_MAGIC:
        return {}
    return _read_ifd0(tiff, ifd_offset, endian)


def _read_ifd0(tiff: bytes, offset: int, endian: str) -> dict[str, str]:
    out: dict[str, str] = {}
    count_fmt, entry = endian + _IFD_COUNT, struct.Struct(endian + _IFD_ENTRY)
    if offset + struct.calcsize(count_fmt) > len(tiff):
        return out
    (count,) = struct.unpack_from(count_fmt, tiff, offset)
    pos = offset + struct.calcsize(count_fmt)
    for _ in range(count):
        if pos + entry.size > len(tiff):
            break
        tag, typ, cnt, value = entry.unpack_from(tiff, pos)
        name = _JPEG_ASCII_TAGS.get(tag)
        if name and typ == _EXIF_ASCII:  # the only encoding read here
            if cnt <= len(value):  # short enough to sit in the entry itself
                raw = value[:cnt]
            else:
                (data_off,) = struct.unpack(endian + _IFD_OFFSET, value)
                raw = tiff[data_off : data_off + cnt]
            text = raw.partition(b"\x00")[0].decode("ascii", errors="replace").strip()
            if text:
                out[name] = text
        pos += entry.size
    return out


# -- GIF -----------------------------------------------------------------


def _gif_text(data: bytes) -> dict[str, str]:
    n = len(data)
    if len(data) < _GIF_HEAD.size:
        return {}
    _sig, _width, _height, packed, _background, _aspect = _GIF_HEAD.unpack_from(data)
    pos = _GIF_HEAD.size
    pos += _color_table(packed)
    comments: list[str] = []
    while pos < n:
        marker = data[pos]
        if marker == _GIF_TRAILER:
            break
        if marker == _GIF_EXTENSION:
            if pos + _GIF_EXT.size > n:
                break
            _introducer, label = _GIF_EXT.unpack_from(data, pos)
            pos += _GIF_EXT.size
            pos, chunk = _skip_subblocks(data, pos)
            if label == _GIF_COMMENT:
                text = " ".join(bytes(chunk).decode("ascii", errors="replace").split())
                if text:
                    comments.append(text)
            continue
        if marker == _GIF_DESCRIPTOR:
            if pos + _GIF_IMAGE.size > n:
                break
            local_packed = _GIF_IMAGE.unpack_from(data, pos)[-1]
            pos += _GIF_IMAGE.size
            pos += _color_table(local_packed)
            if pos >= n:
                break
            pos += 1  # LZW minimum code size
            pos, _ = _skip_subblocks(data, pos)
            continue
        break  # an unrecognised byte here means the walk has lost sync
    return {("Comment" if i == 0 else f"Comment {i + 1}"): c for i, c in enumerate(comments)}


def _color_table(packed: int) -> int:
    """Bytes of the colour table a packed field declares; 0 when it declares none."""
    if not packed & _GIF_TABLE_FLAG:
        return 0
    return _GIF_RGB * (1 << ((packed & _GIF_TABLE_BITS) + 1))


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
