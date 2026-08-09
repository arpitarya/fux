"""Retrieval metrics, at document level, exactly as pre-registered.

Ranking mirrors ``fux find``: score a pool of chunks with the archived BM25F,
aggregate per file by **max chunk score**, order by ``(-round(score, 9), path)``.
That aggregation rule is copied from the archived ``_run_find`` rather than
reinvented, because a different tie-break would make the two arms differ for a
reason that has nothing to do with pruning.

Definitions are frozen in ``PRE-REGISTRATION.md``; the docstrings here restate
them so a reader of the code does not have to trust a second file.
"""

from __future__ import annotations

import math

from fux.index.bm25f import Searcher

__all__ = [
    "CHUNK_POOL",
    "MRR_DEPTH",
    "rank_documents",
    "rank_of",
    "score_queries",
    "aggregate",
    "rare_term_slice",
]

CHUNK_POOL = 200  # archived `_FIND_POOL` — chunks scored before aggregation
MRR_DEPTH = 50  # reciprocal rank is 0 beyond this depth (pre-registered)


def rank_documents(searcher: Searcher, query: str, *, pool: int = CHUNK_POOL) -> list[tuple[str, float]]:
    """``[(path, score)]`` best first — the archived find aggregation, unchanged."""
    best: dict[str, float] = {}
    for result in searcher.search(query, top=pool):
        current = best.get(result.file)
        if current is None or result.score > current:
            best[result.file] = result.score
    return sorted(best.items(), key=lambda kv: (-round(kv[1], 9), kv[0]))


def rank_of(ranked: list[tuple[str, float]], gold: str) -> int | None:
    """1-based rank of ``gold``, matched by path suffix (the lab harness rule)."""
    for i, (path, _score) in enumerate(ranked, start=1):
        if path == gold or path.endswith(gold):
            return i
    return None


def score_queries(ranks: list[int | None]) -> dict[str, float]:
    """hit@5, P@10 and MRR over a list of gold ranks (``None`` = not retrieved).

    * **hit@5** — fraction with ``rank <= 5``.
    * **P@10** — ``|relevant ∩ top-10| / 10``. With one gold document per query
      this is ``hit@10 / 10`` by construction; it is reported because the
      handoff asks for it, not because it carries independent signal.
    * **MRR** — mean ``1/rank`` truncated at ``MRR_DEPTH``.
    """
    n = len(ranks)
    if n == 0:
        return {"hit@5": 0.0, "P@10": 0.0, "MRR": 0.0, "n": 0}
    hit5 = sum(1 for r in ranks if r is not None and r <= 5)
    hit10 = sum(1 for r in ranks if r is not None and r <= 10)
    rr = sum(1.0 / r for r in ranks if r is not None and r <= MRR_DEPTH)
    return {
        "hit@5": round(hit5 / n, 6),
        "P@10": round((hit10 / 10.0) / n, 6),
        "MRR": round(rr / n, 6),
        "n": n,
    }


def aggregate(per_query: dict[str, int | None], keys: list[str]) -> dict[str, float]:
    """Metrics restricted to ``keys`` (a slice), preserving their order."""
    return score_queries([per_query[k] for k in keys])


def rare_term_slice(
    queries: list[str], baseline: Searcher, tokenize_fn
) -> tuple[list[str], bool]:
    """The bottom-tercile-by-minimum-df queries, plus a degeneracy flag.

    "Rare" is only meaningful against a collection, so the slice is
    corpus-relative: rank every query by the **minimum baseline df** among its
    terms that exist in the index, then take the bottom ``ceil(n/3)``.

    Returns ``(slice_keys, degenerate)``. ``degenerate`` is True when every
    query shares the same minimum df — the slice then says nothing about rare
    terms, which is a finding about the eval set and is reported as such rather
    than quietly counted as a pass.
    """
    stat: dict[str, int] = {}
    for q in queries:
        dfs = [
            len(baseline.postings[t])
            for t in dict.fromkeys(tokenize_fn(q))
            if t in baseline.postings
        ]
        stat[q] = min(dfs) if dfs else 0
    if not queries:
        return [], True
    ordered = sorted(queries, key=lambda q: (stat[q], q))
    size = math.ceil(len(ordered) / 3)
    degenerate = len({stat[q] for q in queries}) <= 1
    return ordered[:size], degenerate
