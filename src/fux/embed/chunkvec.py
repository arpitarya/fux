"""Per-chunk vectors — committed. W-76 Phase 7.

**Arpit's fork A ruling, 2026-08-23:**

> *"I would like everything committed. … I don't want to run `fux build`. I want
> it committed. I'm going to clone the repo and run the query. That's all."*

So the `int8` vectors are **committed**, and the 256-bit sign codes become the
**derived** Hamming prefilter over them. `fux build` stays what it already is:
a speed step that never changes an answer.

## What replaced what

The document-level `code` field (one vector per whole document, sign-quantized
to 32 bytes) was removed in Phase 1. It is not replaced by nothing — the same
Hamming scan returns here, but as the *first pass over real data* rather than
as the answer:

| | Phase 1 and earlier | here |
|---|---|---|
| unit | one vector per **document** | one per **chunk** (~9.8/doc measured) |
| precision | 1 bit per dimension | **8 bits** per dimension |
| where | committed `code` field | committed `vectors`; sign codes derived |
| role | *was* the dense lane | the fast first pass over it |

The unit is the fix. A 12 KB document with ten sections averaged into one point
sits near none of them, which is why the old lane fixed 3 graded queries and
broke 9.

## Why the scale is not stored

`Vec` carries `q` (int8 components) and a `scale`. Ranking uses cosine
similarity, and **the scales cancel**:

    cos(s_a*q_a, s_b*q_b) = dot(q_a,q_b) / (|q_a| |q_b|)

So only `q` is committed. That is 256 bytes per chunk instead of 260, and —
more importantly — **it keeps a float out of the committed plane entirely**,
which is what makes L3 hold here without an argument about float formatting.

## Determinism

Pure Python throughout, deliberately. ADR-GRAPH proved fux's float maths is
byte-identical across x86-64 Linux and arm64 macOS; that result is what makes
committing model-derived bytes safe, and **it was proved for stdlib only**.
A numpy fast path would put committed bytes at risk — W-76 veto 5.
"""

from __future__ import annotations

import base64
from math import sqrt

from .model import Vec


def encode(vec: Vec) -> str:
    """One chunk vector to unpadded base64url of its int8 components."""
    raw = bytes((c & 0xFF) for c in vec.q)
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode(text: str) -> tuple[int, ...]:
    """Back to signed components. The inverse of `encode`, exactly."""
    padded = text + "=" * (-len(text) % 4)
    raw = base64.urlsafe_b64decode(padded)
    return tuple(c - 256 if c > 127 else c for c in raw)


def sign_code(components) -> bytes:
    """The derived Hamming prefilter code for one chunk.

    Identical in shape to the `code` field Phase 1 removed — one bit per
    dimension — but computed per chunk and never committed. It is a **cache of
    a sign test on committed bytes**, which is why it belongs in the derived
    plane: deleting it costs speed and nothing else.
    """
    bits = 0
    for i, component in enumerate(components):
        if component > 0:
            bits |= 1 << i
    return bits.to_bytes(max(32, -(-len(components) // 8)), "little")


def cosine(a, b) -> float:
    """Cosine similarity between two int8 component tuples.

    Returns `0.0` for a zero vector rather than raising: a chunk of punctuation
    embeds to zero, and a zero-vector chunk should simply never match rather
    than take the whole query down.
    """
    dot = 0
    na = 0
    nb = 0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0 or nb == 0:
        return 0.0
    return dot / (sqrt(na) * sqrt(nb))


def max_sim(query_components, chunk_vectors) -> float:
    """A document scores as its BEST-matching chunk, not its average one.

    This is the whole point of going per-chunk. Averaging chunk scores would
    reintroduce exactly the dilution that made the document-level code fail:
    a document that answers the question in one section and discusses nine
    other things would score below a document that is vaguely on-topic
    throughout.
    """
    best = 0.0
    for encoded in chunk_vectors:
        score = cosine(query_components, decode(encoded))
        if score > best:
            best = score
    return best
