"""Graph traversal command handlers — query / path / explain / report ($0)."""
from __future__ import annotations

from fux import graphquery, recall, report
from fux.cliutil import root


def cmd_query(args) -> int:
    here = root()
    graph = graphquery.load(here)
    # Anchor lexically on rules, then traverse the graph from each anchor.
    anchors = [f"rule:{r.id}" for r, _ in recall.run(here, args.query, top=3)]
    anchors = [a for a in anchors if any(n["id"] == a for n in graph["nodes"])]
    if not anchors:
        node = graphquery.find(graph, args.query)
        anchors = [node["id"]] if node else []
    if not anchors:
        print(f"fux: nothing in the graph matches '{args.query}'")
        return 1
    by_id = {n["id"]: n for n in graph["nodes"]}
    for a in anchors:
        print(f"# {by_id[a].get('label', a)} ({by_id[a]['type']})")
        for nid in graphquery.neighbors(graph, a, depth=args.depth):
            n = by_id[nid]
            print(f"  → {n.get('label', nid)} ({n['type']})")
        print()
    return 0


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
