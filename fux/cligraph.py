"""Graph traversal command handlers — query / path / explain / report ($0)."""
from __future__ import annotations

from fux import graphquery, recall, report
from fux.cliutil import root


def cmd_query(args) -> int:
    here = root()
    graph = graphquery.load(here)
    # Phase 1: anchor on recall-matched rule nodes.
    anchors = [f"rule:{r.id}" for r, _ in recall.run(here, args.query, top=3)]
    anchors = [a for a in anchors if any(n["id"] == a for n in graph["nodes"])]
    # Phase 2: augment with the top-scored code nodes (mirrors graphify's
    # multi-seed scoring — the single shortest-id `find()` surfaced incidental
    # probes over the real implementation). Recall already handles rule anchors.
    _CODE_TYPES = {"code-file", "function", "class", "module"}
    seen = set(anchors)
    terms = [t for t in args.query.lower().split() if len(t) > 2]
    for node in graphquery.score_nodes(graph, terms, types=_CODE_TYPES)[:5]:
        if node["id"] not in seen:
            anchors.append(node["id"])
            seen.add(node["id"])
    if not anchors:
        print(f"fux: nothing in the graph matches '{args.query}'")
        return 1
    _GENERIC = {"main", "run", "test", "__init__", "setup", "teardown"}
    by_id = {n["id"]: n for n in graph["nodes"]}
    printed: set[str] = set()        # global dedup: each node emitted at most once
    # Buffer + budget: cap total output so a broad query can't blow up Claude's
    # context. ~4 chars/token is the usual rule of thumb (graphify uses ~3).
    out: list[str] = []
    char_budget = max(0, getattr(args, "budget", 1200)) * 4
    used = 0

    def emit(line: str) -> bool:
        nonlocal used
        if used + len(line) + 1 > char_budget:
            return False
        out.append(line)
        used += len(line) + 1
        return True

    for a in anchors:
        if not emit(f"# {_fmt(by_id[a])}"):
            break
        printed.add(a)
        anchor_dir = _dirname(by_id[a].get("file") or a)
        nbrs = graphquery.neighbors(graph, a, depth=args.depth)
        # Rank: same-module neighbours first, then by centrality — spends the
        # 15-slot budget on query-relevant nodes, not same-named fns elsewhere.
        nbrs.sort(key=lambda nid: (_dirname(by_id[nid].get("file") or nid) != anchor_dir,
                                   -by_id[nid].get("centrality", 0.0), nid))
        shown = 0
        for nid in nbrs:
            n = by_id[nid]
            if nid in printed or n.get("label", nid) in _GENERIC:
                continue
            printed.add(nid)
            if not emit(f"  → {_fmt(n)}"):
                break
            shown += 1
            if shown >= 15:
                break
        out.append("")
    print("\n".join(out).rstrip())
    return 0


def _dirname(path: str) -> str:
    return path.rsplit("/", 1)[0] if "/" in path else ""


def _fmt(n: dict) -> str:
    """`label (type) — file:line` — the location lets Claude open the exact
    node instead of grepping for it (the round-trip fux exists to save)."""
    head = f"{n.get('label', n['id'])} ({n['type']})"
    loc = n.get("file")
    if loc:
        return f"{head} — {loc}" + (f":{n['line']}" if n.get("line") else "")
    return head


def cmd_path(args) -> int:
    graph = graphquery.load(root())
    a, b = graphquery.find(graph, args.a), graphquery.find(graph, args.b)
    if not a or not b:
        print("fux: could not resolve both endpoints in the graph")
        return 1
    p = graphquery.shortest_path(graph, a["id"], b["id"])
    if not p:
        print(f"no path between {a['label']} and {b['label']}")
        return 1
    by_id = {n["id"]: n for n in graph["nodes"]}
    print(" → ".join(by_id[x].get("label", x) for x in p))
    return 0


def cmd_explain(args) -> int:
    graph = graphquery.load(root())
    node = graphquery.find(graph, args.term)
    if not node:
        print(f"fux: no node matches '{args.term}'")
        return 1
    by_id = {n["id"]: n for n in graph["nodes"]}
    print(f"# {node.get('label', node['id'])} ({node['type']})")
    if node.get("file"):
        print(f"file: {node['file']}" + (f":{node['line']}" if node.get("line") else ""))
    print(f"community: {node.get('community', '—')}\n\nneighbors:")
    for nid in graphquery.neighbors(graph, node["id"], depth=1):
        n = by_id[nid]
        print(f"  · {n.get('label', nid)} ({n['type']})")
    return 0


def cmd_report(_args) -> int:
    from fux import paths
    here = root()
    graph = graphquery.load(here)
    target = paths.Footprint(here).out_file("GRAPH_REPORT.md")
    target.write_text(report.render(graph), encoding="utf-8")
    print(f"✔ graph report → {target}")
    return 0
