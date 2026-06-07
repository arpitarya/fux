"""Graph traversal — query / path / explain over .fux/out/graph.json ($0, plan §7).

The graphify-replacement query value: traverse EXTRACTED edges instead of
grepping. Pure stdlib BFS over the merged code+knowledge graph.
"""
from __future__ import annotations

import json
from collections import deque
from pathlib import Path

from fux import paths


def load(root: Path) -> dict:
    f = paths.Footprint(root).out / "graph.json"
    if not f.exists():
        raise SystemExit("fux: no graph yet — run `fux build` first.")
    return json.loads(f.read_text(encoding="utf-8"))


def _adj(graph: dict) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = {n["id"]: set() for n in graph["nodes"]}
    for e in graph["edges"]:
        if e["source"] in adj and e["target"] in adj:
            adj[e["source"]].add(e["target"])
            adj[e["target"]].add(e["source"])
    return adj


def find(graph: dict, term: str) -> dict | None:
    """Resolve a free-text term to the best-matching node."""
    t = term.lower().strip()
    nodes = graph["nodes"]
    exact = [n for n in nodes if n["id"].lower() == t or n.get("label", "").lower() == t]
    if exact:
        return exact[0]
    part = [n for n in nodes if t in n["id"].lower() or t in n.get("label", "").lower()]
    return min(part, key=lambda n: len(n["id"])) if part else None


def score_nodes(graph: dict, terms: list[str], types: set[str] | None = None) -> list[dict]:
    """Score every node by query-term overlap, return best-first (mirrors graphify).

    +1 per term found in the node label, +0.5 per term in its id/file path. This
    surfaces the *implementation* (`GrowwSource`) over an incidental shortest-id
    match (`groww_probe.py`) — the single-pick `find()` couldn't. `$0`, stdlib.
    """
    tl = [t.lower() for t in terms]
    scored: list[tuple[float, str, dict]] = []
    for n in graph["nodes"]:
        if types and n.get("type") not in types:
            continue
        label = (n.get("label") or "").lower()
        ident = (n["id"] + " " + (n.get("file") or "")).lower()
        s = sum(1 for t in tl if t in label) + sum(0.5 for t in tl if t in ident)
        if s > 0:
            scored.append((s, n["id"], n))
    scored.sort(key=lambda x: (-x[0], x[1]))   # score desc, id tie-break → deterministic
    return [n for _, _, n in scored]


def neighbors(graph: dict, node_id: str, depth: int = 1) -> list[str]:
    adj = _adj(graph)
    seen, frontier = {node_id}, {node_id}
    for _ in range(depth):
        nxt = {m for nid in frontier for m in adj.get(nid, ())} - seen
        seen |= nxt
        frontier = nxt
    return sorted(seen - {node_id})


def shortest_path(graph: dict, a: str, b: str) -> list[str] | None:
    adj = _adj(graph)
    if a not in adj or b not in adj:
        return None
    prev, q = {a: None}, deque([a])
    while q:
        cur = q.popleft()
        if cur == b:
            path = [cur]
            while prev[path[-1]] is not None:
                path.append(prev[path[-1]])
            return list(reversed(path))
        for m in sorted(adj[cur]):
            if m not in prev:
                prev[m] = cur
                q.append(m)
    return None


def god_nodes(graph: dict, top: int = 12) -> list[tuple[str, int]]:
    deg: dict[str, int] = {n["id"]: 0 for n in graph["nodes"]}
    for e in graph["edges"]:
        if e["source"] in deg:
            deg[e["source"]] += 1
        if e["target"] in deg:
            deg[e["target"]] += 1
    return sorted(deg.items(), key=lambda kv: (-kv[1], kv[0]))[:top]


def pagerank(graph: dict, damping: float = 0.85, iterations: int = 100,
             tol: float = 1e-9) -> dict[str, float]:
    """Deterministic PageRank over the undirected merged graph ($0, stdlib).

    Finds *architectural* centrality — chokepoints a raw degree count misses (a
    node bridging two communities outranks a locally-busy leaf). Nodes are visited
    in sorted order so float accumulation is reproducible across runs (plan §17.19b).
    """
    ids = sorted(n["id"] for n in graph["nodes"])
    n = len(ids) or 1
    adj = _adj(graph)
    deg = {nid: len(adj.get(nid, ())) for nid in ids}
    rank = {nid: 1.0 / n for nid in ids}
    base = (1.0 - damping) / n
    for _ in range(iterations):
        dangling = damping * sum(rank[nid] for nid in ids if deg[nid] == 0) / n
        nxt = {nid: base + dangling for nid in ids}
        for nid in ids:
            if deg[nid]:
                share = damping * rank[nid] / deg[nid]
                for m in sorted(adj[nid]):
                    nxt[m] += share
        if sum(abs(nxt[nid] - rank[nid]) for nid in ids) < tol:
            rank = nxt
            break
        rank = nxt
    return rank


def chokepoints(graph: dict, top: int = 12) -> list[tuple[str, float]]:
    """Top nodes by PageRank centrality (desc), id-tie-broken for determinism."""
    pr = pagerank(graph)
    return sorted(pr.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
