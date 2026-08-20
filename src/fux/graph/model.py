"""The graph's shape: an edge, and the two adjacency views built from edges.

**Two views, deliberately, because the verbs ask different questions.**

- **Directed** — an edge points the way the document points. `path` uses this,
  because "a route from A to B" means A said something about B, not that
  somebody once mentioned them together. Tag nodes are *sinks* here: a record
  carries `tag:ops` outbound and a tag carries nothing, so a route never
  launders itself through a shared label.
- **Undirected** — the same edges, both ways. `community` and PPR use this,
  because relatedness is symmetric and because a tag is exactly the hub that
  should pull its documents together.

The edge vocabulary is `ingest/edges.py`'s and is not re-decided here:
`ref` / `tag` / `code`, graded `EXTRACTED` 10 · `AMBIG` 8 · `INFERRED` 6.
Grade is the edge weight everywhere in this package, so a basename-resolved
`code` edge propagates four fifths of what a resolved link does, and nothing
has to invent a second weighting scheme.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Edge", "Graph", "TAG_PREFIX"]

TAG_PREFIX = "tag:"


@dataclass(frozen=True, order=True)
class Edge:
    """One resolved relationship. Ordered so a sort is the canonical order."""

    src: str
    kind: str
    dst: str
    grade: int


class Graph:
    """Adjacency over a set of edges. Every accessor returns sorted lists.

    **Sorted is not tidiness, it is L3.** Community assignment and PPR both
    accumulate over neighbours, and float accumulation is not associative — an
    unsorted traversal makes the same corpus produce different bytes on
    different runs. Every iteration order in this package is derived from a
    sort on ids.
    """

    def __init__(self, edges: list[Edge]) -> None:
        self.edges = sorted(edges)
        self._out: dict[str, list[Edge]] = {}
        self._both: dict[str, list[tuple[str, int]]] = {}
        nodes: set[str] = set()
        for edge in self.edges:
            nodes.add(edge.src)
            nodes.add(edge.dst)
            self._out.setdefault(edge.src, []).append(edge)
            self._both.setdefault(edge.src, []).append((edge.dst, edge.grade))
            self._both.setdefault(edge.dst, []).append((edge.src, edge.grade))
        self.nodes = sorted(nodes)
        for adjacency in self._both.values():
            adjacency.sort()

    def out_edges(self, node: str) -> list[Edge]:
        """Outbound edges, canonically ordered. `path` and `explain` read this."""
        return list(self._out.get(node, ()))

    def neighbours(self, node: str) -> list[tuple[str, int]]:
        """Undirected `(neighbour, grade)` pairs. Community and PPR read this."""
        return list(self._both.get(node, ()))

    def documents(self) -> list[str]:
        """Nodes that are documents — everything that is not a tag."""
        return [n for n in self.nodes if not n.startswith(TAG_PREFIX)]

    def __len__(self) -> int:
        return len(self.nodes)


def edges_from_records(records: list[dict]) -> list[Edge]:
    """Lift the committed `edges` arrays into `Edge`s.

    A record's `edges` are already resolved and already dropped if dangling
    (`ingest/edges.py`), so there is nothing to validate here — only to lift.
    """
    out: list[Edge] = []
    for record in records:
        src = record["id"]
        for edge in record.get("edges", ()):
            out.append(
                Edge(src=src, kind=edge["kind"], dst=edge["dst"], grade=int(edge["grade"]))
            )
    return sorted(out)
