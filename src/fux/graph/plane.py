"""`.fux/runtime/graph.json` — the derived graph plane.

## Why the graph plane is derived and not committed

Edges are already committed, on the records that own them. Communities are
**not**, and that is a decision rather than an omission: a community label is
a global property of the whole edge set, so adding one document can legally
change the label of documents it has no edge to. Committing that means a
one-file commit produces a diff across the corpus — the opposite of what the
committed plane is optimised for.

So the split follows the wire/runtime split the rest of the engine already
uses: **edges are committed because they are local and diffable; communities
are derived because they are global and would not be.** The plane is
gitignored, disposable, and rebuilt by `fux build` from the committed shards
alone — the same contract the accelerator has.

Edges are copied in alongside the communities so a graph query reads one file
instead of every shard. That is a speed decision with no semantic content:
the committed records remain the source of truth, and a stale plane is
refused rather than trusted.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..errors import FuxError
from . import community as community_mod
from .model import Edge, Graph, edges_from_records

__all__ = ["GRAPH_NAME", "SCHEMA", "build_plane", "load", "GraphPlane"]

GRAPH_NAME = "graph.json"
SCHEMA = "fux.graph.v1"


class GraphPlane:
    """The loaded plane: a `Graph`, plus the community each node landed in."""

    def __init__(self, graph: Graph, communities: dict[str, str]) -> None:
        self.graph = graph
        self.communities = communities

    def community_of(self, node: str) -> str | None:
        return self.communities.get(node)

    def members(self, label: str) -> list[str]:
        return sorted(n for n, c in self.communities.items() if c == label)


def build_plane(directory: Path, records: list[dict]) -> int:
    """Write the plane. Returns bytes written, matching the build's convention."""
    edges = edges_from_records(records)
    graph = Graph(edges)
    communities = community_mod.assign(graph)

    payload = {
        "schema": SCHEMA,
        # Sorted, and a list of lists rather than a list of objects: this file
        # is machine-written and machine-read, and four values per edge beats
        # four repeated keys per edge at a million of them.
        "edges": [[e.src, e.kind, e.dst, e.grade] for e in graph.edges],
        "communities": {node: communities[node] for node in sorted(communities)},
    }
    text = json.dumps(payload, indent=None, sort_keys=False, separators=(",", ":")) + "\n"
    path = directory / GRAPH_NAME
    path.write_text(text, encoding="utf-8")
    return len(text.encode("utf-8"))


def load(root: Path) -> GraphPlane:
    """Read the plane, or fail with the command that creates it."""
    from ..derive import format as fmt

    path = fmt.runtime_dir(root) / GRAPH_NAME
    if not path.exists():
        raise FuxError("the graph lane needs the derived plane - run `fux build` first")

    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != SCHEMA:
        raise FuxError(
            f"{path} has schema {payload.get('schema')!r}, expected {SCHEMA!r} - "
            "run `fux build` to rebuild the derived plane"
        )

    edges = [Edge(src=s, kind=k, dst=d, grade=g) for s, k, d, g in payload["edges"]]
    return GraphPlane(Graph(edges), dict(payload["communities"]))
