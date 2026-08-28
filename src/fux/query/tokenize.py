"""The tokenizer both sides of a match share. **Analyzer v2** (W-76 Phase 1).

The pipeline itself lives in `analyzer.py`; this module is the stable entry
point `ingest/` and `query/` have always imported, kept so that every caller
continues to get *the same* analysis by construction rather than by review.

v1 was: lowercase, `[a-z0-9_]+`, drop 50 stopwords. v2 adds identifier
splitting (before lowercasing, which is the only point at which `camelCase`
is still recoverable) and Porter stemming (after stopwords, before hashing).

**A v2 index and a v1 index cannot be mixed**, and nothing tries: the shard
header pins `analyzer`, `store/reader.py` refuses a shard written by another
one, and `ingest`'s carry-forward is gated on the same header. A bump
therefore invalidates every carried field at once, which is the property that
makes it safe to change this file at all.
"""

from __future__ import annotations

from .analyzer import _STOPWORDS, analyze, analyze_pairs

__all__ = ["tokenize", "tokenize_pairs", "_STOPWORDS"]


def tokenize(text: str) -> list[str]:
    """Analyzed terms in document order, with duplicates (they are the tf)."""
    return analyze(text)


def tokenize_pairs(text: str) -> list[tuple[str, str]]:
    """`(surface, analyzed)` for the same terms `tokenize` returns.

    The query side's view of the same pipeline: `confidence` reports the word
    the user typed, not the stem the index is keyed by. Exported here rather
    than imported from `analyzer` directly for the reason this module exists at
    all — one stable entry point, so every caller gets the same analysis by
    construction.
    """
    return analyze_pairs(text)
