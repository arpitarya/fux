"""Community detection — deterministic label propagation, $0 stdlib (plan §7).

Replaces graphify's clustering. Synchronous label propagation with sorted,
tie-broken updates so the result is reproducible across runs (no randomness).
Votes are **edge-weighted**: a low-confidence `references` edge (weight 0.25) pulls
a node into a community far less than a precise `calls`/`contains` edge, so the
loose whole-file xref can't over-fragment or mis-merge clusters by raw count.
"""
from __future__ import annotations

_TIE = 1e-9


def _adjacency(nodes: list[dict], edges: list[dict]) -> dict[str, dict[str, float]]:
    ids = {n["id"] for n in nodes}
    adj: dict[str, dict[str, float]] = {n["id"]: {} for n in nodes}
    for e in edges:
        s, t = e.get("source"), e.get("target")
        if s in ids and t in ids and s != t:
            w = float(e.get("weight", 1.0))
            adj[s][t] = adj[s].get(t, 0.0) + w
            adj[t][s] = adj[t].get(s, 0.0) + w
    return adj


def detect(nodes: list[dict], edges: list[dict], max_iter: int = 30) -> dict[str, int]:
    """Return {node_id: community_index}. Indices are stable (sorted by member)."""
    adj = _adjacency(nodes, edges)
    label = {nid: nid for nid in adj}
    order = sorted(adj)
    for _ in range(max_iter):
        changed = False
        for nid in order:
            if not adj[nid]:
                continue
            votes: dict[str, float] = {}
            for nbr, w in adj[nid].items():
                votes[label[nbr]] = votes.get(label[nbr], 0.0) + w
            top = max(votes.values())
            # Deterministic tie-break: smallest label among the (near-)winners.
            best = min(lab for lab, c in votes.items() if top - c < _TIE)
            if label[nid] != best:
                label[nid] = best
                changed = True
        if not changed:
            break
    return _compact(label)


def _compact(label: dict[str, str]) -> dict[str, int]:
    """Map raw labels → 0..k indices, ordered by each community's smallest member."""
    groups: dict[str, list[str]] = {}
    for nid, lab in label.items():
        groups.setdefault(lab, []).append(nid)
    ordered = sorted(groups.values(), key=lambda members: min(members))
    return {nid: idx for idx, members in enumerate(ordered) for nid in members}
