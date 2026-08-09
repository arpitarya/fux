"""FuxVec — binary vector codes, built from scratch on Fux's laws (proposal §6).

Adopting a vector database was never open: it costs dependencies, and ANN
approximates a problem we can solve exactly. What is worth taking is the
*concept*, implemented in stdlib.

**Sign quantization.** A 256-dim int8 embedding becomes a 256-bit code —
bit *i* is `component[i] > 0`. 32 bytes per document, so a million documents
of dense search index cost 32 MB, and the committed lean plane can afford to
carry them (proposal §8c).

**Why this is fast in pure Python.** Hamming distance is
`(q ^ c).bit_count()` — big-int XOR and `int.bit_count()` are C-speed
primitives, so a full-corpus scan needs no library and no index structure.
Search itself lands in M5; this module owns the codes.

The quantization loses magnitude, never identity: candidates found by Hamming
are re-scored with the exact int8 cosine the engine already ships, so the
final ordering is exact. The prefilter only bounds *which* documents get
exact scoring.
"""

from __future__ import annotations

from .model import Vec

CODE_BITS = 256
CODE_BYTES = CODE_BITS // 8


def quantize(vec: Vec) -> bytes:
    """Sign-quantize one embedding into a fixed-width code (little-endian bits)."""
    acc = 0
    for i, component in enumerate(vec.q):
        if component > 0:
            acc |= 1 << i
    return acc.to_bytes(_width(len(vec.q)), "little")


def doc_code(vecs) -> bytes | None:
    """Sign-quantize a document: the scale-weighted mean of its chunk vectors.

    Chunks carry different scales, so components are un-scaled before summing —
    otherwise a chunk with a large scale would dominate the document's signs.
    Returns None when a document has no embeddable chunk; the caller must then
    omit it rather than store an all-zero code, which would sit at a misleading
    middle distance from every query.
    """
    present = [v for v in vecs if v is not None]
    if not present:
        return None
    dim = len(present[0].q)
    acc = [0.0] * dim
    for vec in present:
        for d in range(dim):
            acc[d] += vec.scale * vec.q[d]
    bits = 0
    for d in range(dim):
        if acc[d] > 0:
            bits |= 1 << d
    return bits.to_bytes(_width(dim), "little")


def hamming(a: bytes, b: bytes) -> int:
    """Distance between two codes — one XOR and one popcount, both C-speed."""
    return (int.from_bytes(a, "little") ^ int.from_bytes(b, "little")).bit_count()


def prefilter(query_code: bytes, codes: dict[str, bytes], width: int) -> list[str]:
    """The full-corpus scan: every document, ranked by Hamming distance.

    No index structure and no approximation — 32 bytes per document makes a
    linear scan affordable, and `int.bit_count()` keeps the inner loop in C.
    That is the trade FuxVec exists to make: ANN-class reach with zero
    dependencies and none of the recall anxiety an approximate index carries.

    Ties break on doc id so the candidate set is reproducible; the prefilter
    only decides *which* documents get exact scoring, never their final order.
    """
    q = int.from_bytes(query_code, "little")
    scored = [
        ((q ^ int.from_bytes(code, "little")).bit_count(), doc_id)
        for doc_id, code in codes.items()
    ]
    scored.sort()
    return [doc_id for _, doc_id in scored[:width]]


def _width(dim: int) -> int:
    return max(CODE_BYTES, -(-dim // 8))


__all__ = ["CODE_BITS", "CODE_BYTES", "quantize", "doc_code", "hamming"]
