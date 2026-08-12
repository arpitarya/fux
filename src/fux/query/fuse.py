"""Reciprocal Rank Fusion — the calibration-free way to merge rankings.

**Ported from `archive/v0.26/src/fux/index/fuse.py` with its tests**, per the
port-don't-rewrite rule. The arithmetic is unchanged; only the docstring moved
on, because the supersession `offsets` parameter it carries belongs to a
mechanism this build has not (yet) ported.

    RRF(d) = sum over rankings r containing d of  1 / (k + rank_r(d))

`k` defaults to 60 per Cormack, Clarke & Buettcher (SIGIR 2009), which is also
what the archived engine shipped. No score mixing and no reranker — a
cross-attention reranker needs ~80 MB of model, 8x over the packaging budget,
and that decision is closed with a recorded reopen-trigger.

**`offsets` is kept, unused, and that is deliberate.** In v0.26 it carried the
supersession down-rank penalty (archived ADR-0015, calibrated safe interval
`[11, inf)`, shipped at 15). This build has no supersession mechanism yet, so
nothing passes it. It is ported rather than dropped because the arithmetic is
the part that was calibrated, and re-deriving it later from a description
would be re-doing measurement that has already been paid for.
"""

from __future__ import annotations

__all__ = ["rrf", "RRF_K"]

#: Cormack et al. 2009. Not a tuned value — the literature default the archived
#: engine also used, kept so fused rankings stay comparable across builds.
RRF_K = 60


def rrf(rankings: list[list], k: int = RRF_K, offsets: dict | None = None) -> dict:
    """Fused scores keyed by item; items may appear in any subset of rankings.

    ``offsets`` maps an item to a **rank penalty**: it contributes as though it
    had placed that many positions lower in every ranking that contains it.

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
