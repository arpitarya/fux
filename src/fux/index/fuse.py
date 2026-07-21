"""Reciprocal Rank Fusion — the calibration-free way to merge rankings.

RRF(d) = Σ_r 1 / (k + rank_r(d)) over the rankings that contain d. k defaults
to 60 per the literature (Cormack et al. 2009); configurable via
`[engine.hybrid] rrf_k`. No score mixing, no reranker (closed decision —
compare/query-engine.compare.md records the reopen-trigger).
"""

from __future__ import annotations


def rrf(rankings: list[list], k: int = 60) -> dict:
    """Fused scores keyed by item; items may appear in any subset of rankings."""
    scores: dict = {}
    for ranking in rankings:
        for position, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + position)
    return scores
