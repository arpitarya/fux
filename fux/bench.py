"""Recall metrics — recall@k and MRR over a labelled query set ($0, plan §17.4).

Pure functions so the same logic backs both the test-suite eval and any future
`fux bench`. A "result" is ``(ranked_ids, expected_id)``: the retriever's ranked
rule ids for a query, and the id that *should* surface. This is the LoCoMo /
LongMemEval-style harness that lets Fux quote a real recall@k.
"""
from __future__ import annotations

Result = tuple[list[str], str]


def recall_at_k(results: list[Result], k: int) -> float:
    if not results:
        return 0.0
    hits = sum(1 for ranked, expected in results if expected in ranked[:k])
    return hits / len(results)


def mrr(results: list[Result]) -> float:
    if not results:
        return 0.0
    total = 0.0
    for ranked, expected in results:
        if expected in ranked:
            total += 1.0 / (ranked.index(expected) + 1)
    return total / len(results)


def report(results: list[Result], ks=(1, 3, 5)) -> dict[str, float]:
    out = {f"recall@{k}": round(recall_at_k(results, k), 3) for k in ks}
    out["mrr"] = round(mrr(results), 3)
    return out
