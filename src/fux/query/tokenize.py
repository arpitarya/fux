"""The tokenizer/analyzer — ported from `archive/v0.26/src/fux/index/bm25f.py`,
plus stopword filtering (the M1 build-time addition below).

Lowercase runs of `[a-z0-9_]`, minus a fixed English stopword list. Shared by
`ingest/` (building a document's `terms`) and `query/` (tokenizing the
question) so the two sides of a match are guaranteed to agree.

`path_tokens` is not ported: M1's postings carry only `heading`/`body` (the
compare doc's schema of record, §5) — the archived third `path` field is
dropped, recorded in ADR-0004.

Stopword filtering was not in the archived module or the M1 handoff spec —
added after R2 measured its absence: on this repo's corpus, un-filtered BM25F
let a glossary's dictionary-style repetition of "what"/"is"/"the" outrank a
focused, correct answer on a natural-language question (measured, not
hypothetical; see ADR-0004 and docs/conformance/2026-08-10-m1-t0-slice/).
Standard IR practice, not tuned to that one query — the list below is the
same one `archive/v0.26/src/fux/graph/extract.py` already used for its
top-terms extraction.
"""

from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[a-z0-9_]+")

_STOPWORDS = frozenset(
    """a an and are as at be but by for from has have how i if in into is it its
    of on or that the their then there these this to was were what when where
    which who why will with you your we our not can may""".split()
)


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS]
