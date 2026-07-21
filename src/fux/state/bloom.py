"""Per-document Bloom term signatures — the lean profile's lexical prefilter.

The question a signature answers is deliberately weak: *could this document
contain these query terms?* That is enough to shrink 100k docs to a handful of
candidates, after which the shipped BM25F does exact scoring. Because the
filter is one-sided (false positives possible, false negatives impossible), a
collision can only add a candidate that then scores poorly — it can never
produce a wrong result or hide a right one.

Production precedent: BitFunnel (SIGIR 2017), the signature index Bing runs —
signatures beat postings when the index must stay small
(https://dl.acm.org/doi/10.1145/3077136.3080789).

**Sizing (handoff 0004 open question 1, decided here → ADR 0008.)** k = 4
hashes; m = 9.6 bits per unique term, byte-aligned, clamped to [8, 128] bytes.
9.6 bits/term puts a k=4 filter at ≈1.35 % false-positive rate — the knee where
more bytes stop buying candidate reduction:

| unique terms | signature | bits/term | FPR |
|--------------|-----------|-----------|-----|
| ≤ 6 | 8 B (floor) | ≥ 10.7 | < 1 % |
| 25 | 30 B | 9.6 | ~1.4 % |
| 50 | 60 B | 9.6 | ~1.4 % |
| 100 | 120 B | 9.6 | ~1.4 % |
| ≥ 107 | 128 B (cap) | ≤ 9.6 | grows with n |

The 128 B cap is the deliberate trade: it bounds the committed plane at
~200 B/doc, and long documents simply surface as candidates more often —
which costs a little scoring time, never correctness.
"""

from __future__ import annotations

import hashlib

K_HASHES = 4
BITS_PER_TERM = 9.6
MIN_BYTES = 8
MAX_BYTES = 128

# Fixed, documented seeds: determinism is the whole point of a committed plane.
_SEEDS = tuple(f"fux-bloom-{i}".encode("ascii") for i in range(K_HASHES))


def signature_bytes(unique_terms: int) -> int:
    """Signature width for a document with ``unique_terms`` distinct terms."""
    want = -(-int(unique_terms * BITS_PER_TERM) // 8)  # ceil to whole bytes
    return max(MIN_BYTES, min(MAX_BYTES, want))


def _positions(term: str, bits: int) -> list[int]:
    return [
        int.from_bytes(hashlib.sha256(seed + term.encode("utf-8")).digest()[:8], "little") % bits
        for seed in _SEEDS
    ]


def build(terms) -> bytes:
    """Signature over a document's distinct terms. Order-independent by design."""
    unique = sorted(set(terms))
    size = signature_bytes(len(unique))
    bits = size * 8
    acc = 0
    for term in unique:
        for pos in _positions(term, bits):
            acc |= 1 << pos
    return acc.to_bytes(size, "little")


def probe(signature: bytes, terms) -> bool:
    """True when *every* term might be present. False is a certainty; True is a maybe."""
    if not signature:
        return False
    bits = len(signature) * 8
    acc = int.from_bytes(signature, "little")
    for term in set(terms):
        for pos in _positions(term, bits):
            if not acc >> pos & 1:
                return False
    return True


def match_count(signature: bytes, terms) -> int:
    """How many of ``terms`` might be present — the lean profile's ranking hint."""
    if not signature:
        return 0
    bits = len(signature) * 8
    acc = int.from_bytes(signature, "little")
    hits = 0
    for term in set(terms):
        if all(acc >> pos & 1 for pos in _positions(term, bits)):
            hits += 1
    return hits


def expected_fpr(signature_len: int, unique_terms: int) -> float:
    """Analytic FPR — used by the tests to keep the sizing table honest."""
    from math import exp

    bits = signature_len * 8
    if not unique_terms:
        return 0.0
    return (1.0 - exp(-K_HASHES * unique_terms / bits)) ** K_HASHES


__all__ = [
    "K_HASHES", "build", "probe", "match_count", "signature_bytes", "expected_fpr",
]
