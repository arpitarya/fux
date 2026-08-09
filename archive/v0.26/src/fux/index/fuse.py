"""Reciprocal Rank Fusion — the calibration-free way to merge rankings.

RRF(d) = Σ_r 1 / (k + rank_r(d)) over the rankings that contain d. k defaults
to 60 per the literature (Cormack et al. 2009); configurable via
`[engine.hybrid] rrf_k`. No score mixing, no reranker (closed decision —
compare/query-engine.compare.md records the reopen-trigger).
"""

from __future__ import annotations


def rrf(rankings: list[list], k: int = 60, offsets: dict | None = None) -> dict:
    """Fused scores keyed by item; items may appear in any subset of rankings.

    ``offsets`` maps an item to a **rank penalty**: it contributes as though it
    had placed that many positions lower in every ranking that contains it.
    Used for supersession down-ranking (ADR 0015) — the penalised set is exactly
    the documents whose author marked them superseded in frontmatter.

    A penalty demotes; it never removes. The item keeps a non-zero contribution
    at any offset, so a question genuinely *about* a retired decision can still
    reach it. ``None``/empty leaves the arithmetic untouched — identity, not an
    approximation of it.
    """
    scores: dict = {}
    if not offsets:
        for ranking in rankings:
            for position, item in enumerate(ranking, start=1):
                scores[item] = scores.get(item, 0.0) + 1.0 / (k + position)
        return scores
    for ranking in rankings:
        for position, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + position + offsets.get(item, 0))
    return scores
