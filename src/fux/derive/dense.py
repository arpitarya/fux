"""The dense lane — an int-cached Hamming scan over the committed `code` codes.

Every record already carries a 32-byte FuxVec sign-quantized code (ADR-RECORD,
written at M1, unqueried until now). This module makes it searchable, at the
one cost that matters: **decoding base64 into a Python `int` once per build**
instead of once per query.

## Why a full scan and no index

`(q ^ c).bit_count()` is two C-speed primitives on a big int. At 32 bytes a
document, a million documents is 32 MB of codes and a linear scan is
affordable — so there is no ANN structure, no approximation, and none of the
recall anxiety an approximate index carries. That is the trade FuxVec was
built to make; this module just stops paying the base64 tax per query.

## Where this sits relative to the differential law

The lexical accelerator must be byte-identical to the scan. **The dense lane
is a different lane**, not a faster version of an existing one, so it has
nothing to be identical *to* — it adds a ranking that scan never produced.
Fusing it into `ask` would therefore change results by construction, which is
why fusion is **default-off** here and why `ask` without flags remains exactly
the lexical answer the differential proves. Turning it on is a measured
decision, not a build-time one; see `docs/adr/0005-*` and the playground
measurement.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

from . import format as fmt

CODES_NAME = "codes.jsonl"

__all__ = ["CODES_NAME", "build_codes", "load_codes", "hamming_ranking"]


def _decode(code: str) -> int:
    """base64url (unpadded) -> int. The per-build cost this module exists to pay once."""
    padding = "=" * (-len(code) % 4)
    return int.from_bytes(base64.urlsafe_b64decode(code + padding), "little")


def build_codes(directory: Path, docs: list[dict], codes: list[list[str]]) -> int:
    """Write the docidx-ordered code table — **a list of codes per document**.

    W-76 Phase 7 made this per-chunk. It is a *cache of a sign test on
    committed bytes*: the `int8` vectors are in `.fux/index/`, and these are
    one bit per dimension derived from them. Deleting the table costs speed and
    nothing else, which is exactly why it belongs in the derived plane while
    the vectors do not.

    A document with nothing embeddable is stored as `[]` rather than as an
    all-zero code: a zero code sits at a misleading middle distance from every
    query, which would make unembeddable documents quietly rankable.
    """
    payload = json.dumps(codes, separators=(",", ":")).encode("ascii") + b"\n"
    (directory / CODES_NAME).write_bytes(payload)
    return len(payload)


def load_codes(root: Path) -> list[list[int]]:
    """The code table as ints — a list per document, docidx-ordered."""
    path = fmt.runtime_dir(root) / CODES_NAME
    if not path.exists():
        return []
    raw = json.loads(path.read_bytes())
    out: list[list[int]] = []
    for entry in raw:
        if entry is None:
            out.append([])
        elif isinstance(entry, str):  # a pre-Phase-7 table: one code per doc
            out.append([_decode(entry)])
        else:
            out.append([_decode(c) for c in entry])
    return out


def nearest_docs(query_code: int, codes: list[list[int]], limit: int) -> list[int]:
    """Docidxs whose BEST chunk is nearest the query, nearest first.

    The prefilter, and the whole reason the derived table exists: a popcount
    over one int per chunk, versus 256 multiply-adds per chunk for the exact
    score. It narrows the corpus to `limit` documents that the `int8` rescore
    can then afford to look at properly.

    Ties break on docidx so the ranking is reproducible — the dense lane feeds
    a fusion whose input order must not depend on iteration order.
    """
    scored = []
    for docidx, chunk_codes in enumerate(codes):
        if not chunk_codes:
            continue
        best = min((query_code ^ code).bit_count() for code in chunk_codes)
        scored.append((best, docidx))
    scored.sort()
    return [docidx for _, docidx in scored[:limit]]


def hamming_ranking(query_code: int, codes: list[int | None], width: int) -> list[int]:
    """Docidxs ordered by Hamming distance to the query, nearest first.

    Ties break on docidx so the ranking is reproducible — the dense lane feeds
    a fusion whose input order must not depend on dict iteration.
    """
    scored = [
        ((query_code ^ code).bit_count(), docidx)
        for docidx, code in enumerate(codes)
        if code is not None
    ]
    scored.sort()
    return [docidx for _, docidx in scored[:width]]
