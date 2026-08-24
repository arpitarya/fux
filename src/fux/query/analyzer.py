"""Analyzer v2 — the pipeline both `ingest/` and `query/` run, in that order.

    split identifiers  ->  lower  ->  stopwords  ->  stem  ->  (caller hashes)

**The order is the whole design, and two steps are load-bearing in a way that
is easy to get backwards:**

1. **Splitting happens BEFORE lowercasing.** Analyzer v1 lowercased first and
   matched `[a-z0-9_]+`, which destroys `camelCase` irrecoverably —
   `getUserName` arrives at the index as one opaque token `getusername`, and
   no later step can recover `get`, `user`, `name`. Case is the only signal
   that a boundary was there.
2. **Stemming happens BEFORE hashing**, and the hash is taken of the final
   analyzed token. Ingest and query import this module rather than
   reimplementing it, because a one-step divergence between the two sides
   produces a silent no-match: the query hashes a string the index never
   wrote, so the term simply is not found. There is no error to see.

**Whole AND parts are both emitted.** `getUserName` yields `getusername`,
`get`, `user`, `name`. The whole token keeps exact-identifier queries precise;
the parts are what make `user name` find it at all. Identifier-aware
tokenization is the single largest lift available to BM25 on code
([arXiv 2605.18561](https://arxiv.org/html/2605.18561)) — the best BM25
variant adds only ~0.2 % on top of it.

**Measured on this repo (411 documents, 2026-08-23):** splitting takes the
token count from 546 142 to 563 296 (x1.03) and distinct-per-document postings
from 190 512 to 193 884 (x1.02). Small *because this corpus is prose markdown*;
a codebase will differ, and that is not measured here.
"""

from __future__ import annotations

import re

from .stem import stem as _stem

#: Matched against the ORIGINAL text, not a lowercased copy — see the module
#: docstring. Hyphen is absent from the class, so `kebab-case` splits here for
#: free, exactly as it did under v1.
_WORD_RE = re.compile(r"[A-Za-z0-9_]+")

#: The three places a real identifier boundary can sit. Splitting on
#: BOUNDARIES rather than matching runs is what stops an acronym-plus-digit
#: token being shattered: an earlier run-matching version turned `BM25F` into
#: `bm`, `25`, `f`, which is three junk terms and a lost one.
#:
#:   `_`                         snake_case
#:   lower/digit -> upper        getUser, bm25F
#:   upper -> upper+lower        HTTPServer
#:
#: A token with none of these has no boundary in it and is left whole:
#: `sha256`, `utf8`, `k1`, `v0` are single terms, and stripping them into
#: pieces loses the only thing that made them identifying.
_BOUNDARY_RE = re.compile(r"_+|(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")

_STOPWORDS = frozenset(
    """a an and are as at be but by for from has have how i if in into is it its
    of on or that the their then there these this to was were what when where
    which who why will with you your we our not can may""".split()
)


def split_identifier(raw: str) -> list[str]:
    """The parts of one raw token, or `[]` when there is no boundary in it.

    Handles `snake_case`, `camelCase`, `PascalCase` and acronym boundaries
    together, because real identifiers mix them (`HTTP_userName`). Single
    characters are dropped: the `F` in `BM25F` is noise as a standalone term.
    """
    parts = [p for p in _BOUNDARY_RE.split(raw) if p]
    if len(parts) < 2:
        return []
    return [p for p in parts if len(p) > 1]


def analyze(text: str) -> list[str]:
    """Text to final analyzed terms, in document order, WITH duplicates.

    Duplicates are the point: the caller counts them into a term frequency.
    Returning a set here would silently flatten every tf to 1.
    """
    out: list[str] = []
    for raw in _WORD_RE.findall(text):
        for token in (raw, *split_identifier(raw)):
            lowered = token.lower()
            if lowered in _STOPWORDS:
                continue
            out.append(_stem(lowered))
    return out
