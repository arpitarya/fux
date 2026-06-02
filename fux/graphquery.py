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
