"""Reciprocal rank fusion — `-q`, W-109.

## Why this module exists at all, given RRF was deleted

Score-space fusion was removed with the dense lane on 2026-08-25, and
[ADR-PORT-LIST](../../docs/adr/0015_port-list.md) rule 1 says a revival comes
back **with a record**. This is that revival, and it is a different object:

- **The deleted lane fused a BM25F score with a cosine.** Two quantities on
  unrelated scales, where one silently dominates on any corpus where the other
  happens to be small.
- **This fuses RANKS.** `1 / (k + rank)` is scale-free by construction, so
  there is no scale for a corpus to break.

Cormack, Clarke & Buettcher 2009, *Reciprocal Rank Fusion outperforms Condorcet
and individual Rank Learning Methods* — https://doi.org/10.1145/1571941.1572114
— and `k = 60` is their constant, not a tuned one.

## What `score` means afterwards, and why it is said out loud

🔴 **A fused result's `score` is an RRF score, not a BM25F score.** They are
not comparable: RRF sums small reciprocals, BM25F sums idf-weighted
saturations, and nothing maps one onto the other. `--json` carries
`"fused": true` on a fused payload so a consumer cannot read one as the other
by accident.

**The alternative was worse.** Reporting the best arm's BM25F score while
ordering by RRF would make `score` non-monotone with the order it is printed
in — a list whose second row scores higher than its first, with nothing saying
why.
"""

from __future__ import annotations

import dataclasses

__all__ = ["K", "rrf", "fuse_results"]

#: Cormack et al. 2009's constant. **Not tuned here and not a `tune.toml` key**
#: — a knob on it would be a knob on a published constant, measured on TREC
#: collections, with nothing in this repo able to beat it at 10 documents.
K = 60


def rrf(rank_lists: list[list[str]], k: int = K) -> dict[str, float]:
    """`id -> fused score`, from ranked id lists. Rank 0 is best.

    A document absent from a list contributes nothing from it — **not a
    penalty**. RRF's whole shape is that presence is evidence and absence is
    silence; scoring absence would make a list that returned five results
    punish a document worse than a list that returned fifty.
    """
    scores: dict[str, float] = {}
    for ranks in rank_lists:
        for i, doc_id in enumerate(ranks):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + i + 1)
    return scores


def fuse_results(result_lists: list[list], top: int, k: int = K) -> list:
    """Fuse several `run_query` result lists into one, by rank.

    Each element of `result_lists` is a list of `AskResult`, already ranked.
    Returns `top` results carrying the **fused** score, ordered
    `(-round(score, 9), id)` — the same sort key `rank()` uses, so the two
    orderings are broken the same way and a fused list is as reproducible as an
    unfused one.

    **The result object comes from the arm that ranked it best**, so its `loc`,
    `title`, `headings` and `archived` are a real document's, not a merge of
    several views of it. Only `score` is replaced.
    """
    if not result_lists:
        return []
    if len(result_lists) == 1:
        return list(result_lists[0][:top])

    scores = rrf([[r.id for r in results] for results in result_lists], k)

    best_seen: dict[str, tuple[int, object]] = {}
    for results in result_lists:
        for i, result in enumerate(results):
            current = best_seen.get(result.id)
            if current is None or i < current[0]:
                best_seen[result.id] = (i, result)

    ordered = sorted(scores, key=lambda doc_id: (-round(scores[doc_id], 9), doc_id))
    return [
        dataclasses.replace(best_seen[doc_id][1], score=scores[doc_id])
        for doc_id in ordered[:top]
    ]
