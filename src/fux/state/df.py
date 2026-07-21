"""`state/df/` — the exact document-frequency sidecar (handoff §C, amended 2026-07-21).

**Why this exists.** The lean profile can re-derive any document's text exactly,
so it can compute exact *term frequencies*. What it cannot recover from a
50-document candidate set is the *corpus-level* statistics BM25F needs: how many
chunks exist, how long they are on average, and in how many of them each term
appears. Estimating those from Bloom signatures would make lean rankings
*approximately* right. Arpit's call on the M3 escalation: don't soften the
guarantee — store the missing inputs exactly.

With this sidecar, lean and full feed the scorer **the same numbers by
construction**, so identical rankings are a property of the design rather than
a hope confirmed by sampling.

Note what `df` counts here: BM25F scores *chunks*, so `df` is the number of
chunks containing a term and `n` is the total chunk count — not documents.

**Layout.**

- `state/df/_stats.bin` — one header record: total_docs, total_chunks, and the
  summed heading/path/body token counts. Sums are stored as integers, not
  averages, for two reasons: integers round-trip exactly, and
  `avg_wlen = (h·ΣH + p·ΣP + b·ΣB) / n` can then be recomputed for *any*
  `[engine.bm25f]` weights without re-ingesting.
- `state/df/XX.bin` — terms whose hash starts with byte XX: hashes sorted
  ascending and delta-encoded, each followed by a varint df.

Stats live in their own file rather than being repeated per bucket: they change
whenever any document does, and duplicating them 256 times would dirty every
bucket on every commit, defeating the sharding.

**Collisions are detected, never tolerated.** Two distinct terms sharing a u64
hash would silently merge their frequencies and break the exactness claim. The
builder checks for that and fails loudly (see :func:`build`).
"""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path

from ..errors import FuxError
from .format import HEADER, _header_ok, read_bucket, write_bucket

STATS_NAME = "_stats.bin"


def term_hash(term: str) -> int:
    return int.from_bytes(hashlib.sha256(term.encode("utf-8")).digest()[:8], "little")


def bucket_of_term(term: str) -> str:
    return f"{hashlib.sha256(term.encode('utf-8')).digest()[0]:02x}"


class CorpusStats:
    """Exact corpus-level BM25F inputs, reconstructible for any field weights."""

    __slots__ = ("total_docs", "total_chunks", "sum_heading", "sum_path", "sum_body", "df")

    def __init__(self, total_docs: int, total_chunks: int, sum_heading: int,
                 sum_path: int, sum_body: int, df: dict[int, int]):
        self.total_docs = total_docs
        self.total_chunks = total_chunks
        self.sum_heading = sum_heading
        self.sum_path = sum_path
        self.sum_body = sum_body
        self.df = df

    def avg_wlen(self, params) -> float:
        """The Searcher's average weighted length, recomputed from stored sums.

        Algebraically the same quantity: the Searcher averages per-chunk
        weighted lengths, and a weighted sum of averages equals the average of
        weighted sums.
        """
        if not self.total_chunks:
            return 1.0
        weighted = (
            params.heading * self.sum_heading
            + params.path * self.sum_path
            + params.body * self.sum_body
        )
        return weighted / self.total_chunks

    def df_of(self, term: str) -> int:
        return self.df.get(term_hash(term), 0)


# -- varint ----------------------------------------------------------------


def _put_varint(out: bytearray, value: int) -> None:
    while value >= 0x80:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)


def _get_varint(blob: bytes, offset: int) -> tuple[int, int]:
    value = shift = 0
    while True:
        byte = blob[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, offset
        shift += 7


# -- pack / unpack ---------------------------------------------------------


def pack_bucket(entries: list[tuple[int, int]]) -> bytes:
    """``(term_hash, df)`` pairs → one bucket. Hashes ascending, delta-encoded."""
    out = bytearray(HEADER)
    previous = 0
    for hash_, df in sorted(entries):
        _put_varint(out, hash_ - previous)  # ascending, so deltas are non-negative
        _put_varint(out, df)
        previous = hash_
    return bytes(out)


def unpack_bucket(blob: bytes, name: str = "df") -> dict[int, int]:
    _header_ok(blob, name)
    out: dict[int, int] = {}
    offset = len(HEADER)
    previous = 0
    while offset < len(blob):
        delta, offset = _get_varint(blob, offset)
        df, offset = _get_varint(blob, offset)
        previous += delta
        out[previous] = df
    return out


def pack_stats(total_docs: int, total_chunks: int, sums: tuple[int, int, int]) -> bytes:
    return HEADER + struct.pack("<QQQQQ", total_docs, total_chunks, *sums)


def unpack_stats(blob: bytes) -> tuple[int, int, tuple[int, int, int]]:
    _header_ok(blob, f"df/{STATS_NAME}")
    values = struct.unpack_from("<QQQQQ", blob, len(HEADER))
    return values[0], values[1], (values[2], values[3], values[4])


# -- build / persist -------------------------------------------------------


def build(files: dict[str, dict]) -> tuple[CorpusStats, dict[str, list]]:
    """Compute exact corpus statistics from the built index.

    Recomputed from the in-memory index every ingest rather than maintained by
    delta. The index is already fully loaded at this point, so a single pass
    costs what the Searcher's own postings build costs — and recomputation
    cannot drift, which a running total can. The bytes are identical either way.
    """
    from ..index.bm25f import path_tokens, tokenize
    from collections import Counter

    df: dict[int, int] = {}
    seen_terms: dict[int, str] = {}
    total_chunks = 0
    sums = [0, 0, 0]
    for doc_id in sorted(files):
        meta = files[doc_id]
        ptoks = Counter(path_tokens(doc_id))
        title = meta.get("title", "")
        for chunk in meta["chunks"]:
            htoks = Counter(tokenize(chunk["heading"]) + tokenize(title))
            btoks = Counter(tokenize(chunk["text"]))
            total_chunks += 1
            sums[0] += sum(htoks.values())
            sums[1] += sum(ptoks.values())
            sums[2] += sum(btoks.values())
            for term in set(htoks) | set(ptoks) | set(btoks):
                hashed = term_hash(term)
                previous = seen_terms.setdefault(hashed, term)
                if previous != term:
                    # 64-bit collision: two terms would share one df and the
                    # exactness guarantee would quietly become an approximation.
                    raise FuxError(
                        f"df sidecar: hash collision between {previous!r} and {term!r} "
                        "— please report this; the corpus cannot be indexed exactly"
                    )
                df[hashed] = df.get(hashed, 0) + 1
    stats = CorpusStats(len(files), total_chunks, sums[0], sums[1], sums[2], df)

    buckets: dict[str, list] = {}
    for hashed, count in df.items():
        buckets.setdefault(f"{hashed & 0xFF:02x}", []).append((hashed, count))
    return stats, buckets


def write_df(root: Path, stats: CorpusStats, buckets: dict[str, list]) -> None:
    base = root / ".fux/state/df"
    write_bucket(base / STATS_NAME, pack_stats(
        stats.total_docs, stats.total_chunks,
        (stats.sum_heading, stats.sum_path, stats.sum_body),
    ))
    want = {f"{b}.bin" for b in buckets} | {STATS_NAME}
    for bucket, entries in buckets.items():
        write_bucket(base / f"{bucket}.bin", pack_bucket(entries))
    if base.is_dir():
        for path in base.glob("*.bin"):
            if path.name not in want:
                path.unlink()


def load_df(root: Path) -> CorpusStats | None:
    """Read the sidecar back. None when a corpus has no committed df plane."""
    base = root / ".fux/state/df"
    stats_blob = read_bucket(base / STATS_NAME)
    if stats_blob is None:
        return None
    total_docs, total_chunks, sums = unpack_stats(stats_blob)
    df: dict[int, int] = {}
    for path in sorted(base.glob("*.bin")):
        if path.name == STATS_NAME:
            continue
        df.update(unpack_bucket(path.read_bytes(), f"df/{path.name}"))
    return CorpusStats(total_docs, total_chunks, sums[0], sums[1], sums[2], df)


__all__ = [
    "CorpusStats", "build", "write_df", "load_df", "term_hash", "bucket_of_term",
    "pack_bucket", "unpack_bucket", "pack_stats", "unpack_stats", "STATS_NAME",
]
