"""GRAPH_REPORT.md — god nodes + community structure, like graphify's report (plan §7)."""
from __future__ import annotations

from collections import Counter

from fux import graphquery


def render(graph: dict) -> str:
    nodes = graph["nodes"]
    by_id = {n["id"]: n for n in nodes}
    meta = graph["meta"]
    lines = ["# Fux GRAPH_REPORT", "",
             f"_{len(nodes)} nodes · {len(graph['edges'])} edges · "
             f"{meta.get('code_files', 0)} code files · {meta.get('rules', 0)} rules · "
             f"{meta.get('communities', 0)} communities._", ""]
    lines += _types(nodes)
    lines += _edges(graph["edges"])
    lines += _god(graph, by_id)
    lines += _chokepoints(graph, by_id)
    lines += _communities(nodes)
    return "\n".join(lines).rstrip() + "\n"


def _types(nodes: list[dict]) -> list[str]:
    counts = Counter(n["type"] for n in nodes)
    out = ["## Node types", ""]
    out += [f"- {t}: {c}" for t, c in sorted(counts.items(), key=lambda kv: -kv[1])]
    return out + [""]


def _edges(edges: list[dict]) -> list[str]:
    """Edge mix by type + confidence — INFERRED edges are the loose, down-weighted ones."""
    by_type = Counter(e.get("type") for e in edges)
    inferred = sum(1 for e in edges if e.get("confidence") == "INFERRED")
    out = ["## Edges", "", f"_{inferred} of {len(edges)} are INFERRED "
           "(low-confidence `references`, down-weighted in clustering/centrality)._", ""]
    out += [f"- {t}: {c}" for t, c in sorted(by_type.items(), key=lambda kv: -kv[1])]
    return out + [""]


def _god(graph: dict, by_id: dict) -> list[str]:
    out = ["## God nodes (highest connectivity)", ""]
    for nid, deg in graphquery.god_nodes(graph, 12):
        if deg == 0:
            continue
        n = by_id[nid]
        out.append(f"- **{n.get('label', nid)}** ({n['type']}) — {deg} edges")
    return out + [""]


def _chokepoints(graph: dict, by_id: dict) -> list[str]:
    """Architectural centrality (PageRank) — bridges a raw degree count misses."""
    out = ["## Chokepoints (PageRank centrality)", ""]
    for nid, score in graphquery.chokepoints(graph, 12):
        n = by_id.get(nid)
        if n is None or score <= 0:
            continue
        out.append(f"- **{n.get('label', nid)}** ({n['type']}) — {score:.4f}")
    return out + [""]


def _communities(nodes: list[dict]) -> list[str]:
    groups: dict[int, list[dict]] = {}
    for n in nodes:
        groups.setdefault(n.get("community", -1), []).append(n)
    out = ["## Communities", ""]
    for cid in sorted(g for g in groups if g >= 0):
        members = groups[cid]
        if len(members) < 2:
            continue
        labels = ", ".join(sorted(m.get("label", m["id"]) for m in members)[:12])
        out.append(f"- **community {cid}** ({len(members)} nodes): {labels}")
    return out + [""]
