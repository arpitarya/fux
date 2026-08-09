"""Binary record formats for `.fux/state/` (handoff 0004 §C).

Three parallel bucket families — ``codes``, ``sigs``, ``meta`` — each sharded
256 ways by the first byte of ``sha256(doc_id)``. Sharding is what makes the
plane commit-friendly: a change touching 50 docs rewrites a few small files
instead of one 20 MB blob, so git deltas stay proportional to the edit.

Every file is ``FUXSTATE1\\0`` + a u16 format version, then fixed-layout
little-endian records **sorted by doc_hash**. Sorting is not cosmetic: it is
what makes "same sources → byte-identical bucket" true, and therefore what
keeps a re-ingest from showing up as a spurious diff.
"""

from __future__ import annotations

import hashlib
import json
import struct
import zlib
from pathlib import Path

from ..errors import FuxError

MAGIC = b"FUXSTATE1\0"
FORMAT_VERSION = 1
HEADER = MAGIC + struct.pack("<H", FORMAT_VERSION)
CODE_BYTES = 32  # 256-bit FuxVec code
_ZLIB_LEVEL = 9  # pinned: the committed bytes must not vary with the caller


def doc_hash(doc_id: str) -> int:
    """u64 identity for a doc. Its low byte *is* the bucket, by construction."""
    return int.from_bytes(hashlib.sha256(doc_id.encode("utf-8")).digest()[:8], "little")


def bucket_of(doc_id: str) -> str:
    return f"{hashlib.sha256(doc_id.encode('utf-8')).digest()[0]:02x}"


def _header_ok(blob: bytes, name: str) -> None:
    if blob[: len(MAGIC)] != MAGIC:
        raise FuxError(
            f"state bucket {name} is corrupt (bad magic) — "
            "delete `.fux/state/` and re-run `fux ingest`"
        )
    (version,) = struct.unpack_from("<H", blob, len(MAGIC))
    if version != FORMAT_VERSION:
        raise FuxError(
            f"state bucket {name} has format {version} (expected {FORMAT_VERSION}) — "
            "re-run `fux ingest`"
        )


# -- codes: (u64 doc_hash, 32 B code) --------------------------------------


def pack_codes(records: list[tuple[int, bytes]]) -> bytes:
    parts = [HEADER]
    for dh, code in sorted(records):
        if len(code) != CODE_BYTES:
            raise FuxError(f"FuxVec code must be {CODE_BYTES} bytes, got {len(code)}")
        parts.append(struct.pack("<Q", dh) + code)
    return b"".join(parts)


def unpack_codes(blob: bytes, name: str = "codes") -> dict[int, bytes]:
    _header_ok(blob, name)
    out: dict[int, bytes] = {}
    offset = len(HEADER)
    stride = 8 + CODE_BYTES
    while offset < len(blob):
        (dh,) = struct.unpack_from("<Q", blob, offset)
        out[dh] = blob[offset + 8 : offset + stride]
        offset += stride
    return out


# -- sigs: (u64 doc_hash, u16 sig_len, sig bytes) --------------------------


def pack_sigs(records: list[tuple[int, bytes]]) -> bytes:
    parts = [HEADER]
    for dh, sig in sorted(records):
        parts.append(struct.pack("<QH", dh, len(sig)) + sig)
    return b"".join(parts)


def unpack_sigs(blob: bytes, name: str = "sigs") -> dict[int, bytes]:
    _header_ok(blob, name)
    out: dict[int, bytes] = {}
    offset = len(HEADER)
    while offset < len(blob):
        dh, length = struct.unpack_from("<QH", blob, offset)
        offset += 10
        out[dh] = blob[offset : offset + length]
        offset += length
    return out


# -- meta: (u64 doc_hash, u16 rec_len, zlib(json)) -------------------------


def pack_meta(records: list[tuple[int, dict]]) -> bytes:
    parts = [HEADER]
    for dh, payload in sorted(records, key=lambda r: r[0]):
        raw = json.dumps(
            payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        blob = zlib.compress(raw, _ZLIB_LEVEL)
        parts.append(struct.pack("<QH", dh, len(blob)) + blob)
    return b"".join(parts)


def unpack_meta(blob: bytes, name: str = "meta") -> dict[int, dict]:
    _header_ok(blob, name)
    out: dict[int, dict] = {}
    offset = len(HEADER)
    while offset < len(blob):
        dh, length = struct.unpack_from("<QH", blob, offset)
        offset += 10
        try:
            out[dh] = json.loads(zlib.decompress(blob[offset : offset + length]))
        except (zlib.error, ValueError) as exc:
            raise FuxError(
                f"state bucket {name} is corrupt ({exc}) — "
                "delete `.fux/state/` and re-run `fux ingest`"
            ) from exc
        offset += length
    return out


def write_bucket(path: Path, blob: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.is_file() or path.read_bytes() != blob:
        path.write_bytes(blob)


def read_bucket(path: Path) -> bytes | None:
    return path.read_bytes() if path.is_file() else None
