"""Renderers for the graph verbs: `explain`, `graph`, `path`.

Each is a projection of one :func:`fux.kernel.retrieve` call — none of them
runs its own retrieval. Formats follow docs/cli-examples.md, which is the
normative contract the goldens derive from.
"""

from __future__ import annotations

import json

from ..config import find_root, load
from ..errors import FuxError
from ..kernel import NodeRef, paths_between, retrieve


def _graph_for(config, seed, *, k: int, hops: int = 1):
    return retrieve(config, seed, k=k, expand_hops=hops)


# -- explain ---------------------------------------------------------------


def cmd_explain(args) -> int:
    config = load(find_root())
    graph = _graph_for(config, NodeRef(args.doc), k=args.top)
    node = next((n for n in graph.nodes if n.doc_id == args.doc), None)
    if node is None:
        raise FuxError(f"no document {args.doc!r} in the corpus — try `fux find`")
    edges = [e for e in graph.edges if e.src == args.doc]
    passages = [p for p in graph.passages if p.file == args.doc]

    if args.json:
        print(
            json.dumps(
                {
                    "node": {
                        "path": node.doc_id, "title": node.title,
                        "fidelity": node.fidelity, "chunks": len(passages),
                    },
                    "outline": [p for p in node.outline.split(" › ") if p],
                    "edges": [
                        {"kind": e.kind, "dst": e.dst, "grade": e.grade} for e in edges
                    ],
                    "passages": [
                        {
                            "path": p.file, "line_start": p.start, "line_end": p.end,
                            "score": round(p.score, 3), "text": p.text,
                        }
                        for p in passages
                    ],
                },
                ensure_ascii=False,
            )
        )
        return 0

    title = f"   {node.title}" if node.title else ""
    print(f"{node.doc_id}{title}")
    print(f"fidelity: {node.fidelity} · {len(passages)} chunks")
    if node.outline:
        print(f"\nOutline: {node.outline}")
    if edges:
        print("\nEdges:")
        for i, e in enumerate(edges):
            glyph = "└─" if i == len(edges) - 1 else "├─"
            print(f"  {glyph} {e.kind:<11}→ {e.dst:<40} [{e.grade}]")
    if passages:
        print("\nKey passages:")
        for p in passages:
            loc = p.file if p.start is None else f"{p.file}:{p.start}"
            print(f"  {loc}  (score {p.score:.3f})")
            for line in p.text.split("\n")[:3]:
                print(f"    {line}")
    return 0


# -- graph -----------------------------------------------------------------


def cmd_graph(args) -> int:
    config = load(find_root())
    graph = _graph_for(config, args.query, k=args.top)

    if args.json:
        print(
            json.dumps(
                {
                    "query": args.query,
                    "nodes": [
                        {
                            "path": n.doc_id, "title": n.title, "via": n.via,
                            "score": round(n.score, 5),
                        }
                        for n in graph.nodes
                    ],
                    "edges": [
                        {"src": e.src, "kind": e.kind, "dst": e.dst, "grade": e.grade}
                        for e in graph.edges
                    ],
                },
                ensure_ascii=False,
            )
        )
        return 0

    if not graph.nodes:
        print("No confident matches.")
        print(f'Try: fux find "{args.query}" · broaden the topic · fux ingest new sources')
        return 0
    n_nodes, n_edges = len(graph.nodes), len(graph.edges)
    print(
        f"{n_nodes} node{'' if n_nodes == 1 else 's'} · "
        f"{n_edges} edge{'' if n_edges == 1 else 's'}\n"
    )
    for node in graph.nodes:
        title = node.title or ""
        print(f"  {node.doc_id:<40} {title:<32} ({node.via})")
    if graph.edges:
        print()
        for e in graph.edges:
            print(f"  {e.src} ──{e.kind}──▶ {e.dst}")
    return 0


# -- path ------------------------------------------------------------------


def cmd_path(args) -> int:
    config = load(find_root())
    hops = args.hops
    graph = retrieve(config, NodeRef(args.source), k=1, expand_hops=hops)
    found = paths_between(graph, args.source, args.target)

    if args.json:
        print(
            json.dumps(
                {
                    "source": args.source,
                    "target": args.target,
                    "paths": [
                        {
                            "reliability": p.reliability,
                            "hops": [
                                {"src": h.src, "kind": h.kind, "dst": h.dst, "grade": h.grade}
                                for h in p.hops
                            ],
                        }
                        for p in found
                    ],
                },
                ensure_ascii=False,
            )
        )
        return 0

    if args.source == args.target:
        print(f"{args.source} is the same document (0 hops)")
        return 0
    if not found:
        # Honest emptiness: no route is a finding, not a failure.
        print(
            f"no recorded path from {args.source} to {args.target} "
            f"(within {hops} hop{'' if hops == 1 else 's'})"
        )
        return 0
    print(f"{len(found)} path{'' if len(found) == 1 else 's'}:")
    for p in found:
        print(f"  reliability {p.reliability:.3f}")
        for hop in p.hops:
            print(f"    {hop.src} ──{hop.kind}──▶ {hop.dst}   [{hop.grade}]")
    return 0
