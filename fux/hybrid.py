"""Hybrid retrieval — Reciprocal Rank Fusion of lexical ⊕ semantic ⊕ graph ($0).

Fuses the three ranked lists Fux already produces, instead of using them in
isolation (plan §17.1): BM25 ([recall.py]), local semantic similarity ([embed.py],
which has a `$0` char-trigram fallback so this needs no API), and graph proximity
(BFS from the lexical anchors over the merged code⊕knowledge graph). RRF with
k=60 — the same fusion agentmemory uses — is robust to each list's score scale.
Opt-in via `recall_hybrid` / `fux recall --hybrid`; the default path is unchanged.
"""
from __future__ import annotations

from pathlib import Path

from fux import embed, graphquery, recall
from fux.model import Rule

RRF_K = 60


def fuse(root: Path, query: str, rules: list[Rule], top: int = 6,
         cfg: dict | None = None) -> list[tuple[Rule, float]]:
    by_id = {r.id: r for r in rules}
    rankings: list[list[str]] = []

    lexical = [r.id for r, _ in recall.rank(rules, query, top=len(rules))]
    rankings.append(lexical)

    semantic = _semantic_ranking(query, rules)
    if semantic:
        rankings.append(semantic)

    graphical = _graph_ranking(root, lexical[:3])
    if graphical:
        rankings.append([rid for rid in graphical if rid in by_id])

    scores = _rrf([r for r in rankings if r])
    ranked = sorted((( by_id[i], s) for i, s in scores.items() if i in by_id),
                    key=lambda x: (-x[1], x[0].id))
    return ranked[:top]


def _rrf(rankings: list[list[str]], k: int = RRF_K) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, rid in enumerate(ranking):
            scores[rid] = scores.get(rid, 0.0) + 1.0 / (k + rank + 1)
    return scores


def _semantic_ranking(query: str, rules: list[Rule]) -> list[str]:
    if len(rules) < 2:
        return []
    sims = embed._semantic(query, rules)              # $0 trigram fallback if no model
    order = sorted(zip(rules, sims), key=lambda x: x[1], reverse=True)
    return [r.id for r, s in order if s > 0]


def _graph_ranking(root: Path, anchor_ids: list[str]) -> list[str]:
    """Rules ordered by graph distance from the lexical anchors (closest first)."""
    try:
        graph = graphquery.load(root)
    except SystemExit:
        return []
    adj = graphquery._adj(graph)
    anchors = [f"rule:{rid}" for rid in anchor_ids if f"rule:{rid}" in adj]
    if not anchors:
        return []
    dist: dict[str, int] = {a: 0 for a in anchors}
    frontier = set(anchors)
    for d in range(1, 4):
        nxt = {m for nid in frontier for m in adj.get(nid, ())} - dist.keys()
        for m in nxt:
            dist[m] = d
        frontier = nxt
        if not frontier:
            break
    rules = [(nid[len("rule:"):], dd) for nid, dd in dist.items() if nid.startswith("rule:")]
    return [rid for rid, _ in sorted(rules, key=lambda x: x[1])]
