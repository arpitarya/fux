"""Community detection — deterministic label propagation, $0 stdlib (plan §7).

Replaces graphify's clustering. Synchronous label propagation with sorted,
tie-broken updates so the result is reproducible across runs (no randomness).
"""
from __future__ import annotations

from collections import Counter


def _adjacency(nodes: list[dict], edges: list[dict]) -> dict[str, set[str]]:
    ids = {n["id"] for n in nodes}
    adj: dict[str, set[str]] = {n["id"]: set() for n in nodes}
    for e in edges:
        s, t = e.get("source"), e.get("target")
        if s in ids and t in ids and s != t:
            adj[s].add(t)
            adj[t].add(s)
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
            votes = Counter(label[n] for n in adj[nid])
            top = max(votes.values())
            # Deterministic tie-break: smallest label among the winners.
            best = min(lab for lab, c in votes.items() if c == top)
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
