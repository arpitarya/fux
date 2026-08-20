"""The two adjacency views, and why they are two."""

from __future__ import annotations

from fux.graph.model import Edge, Graph, edges_from_records


def _record(doc_id: str, edges: list[dict]) -> dict:
    return {"id": doc_id, "edges": edges}


def test_edges_are_lifted_from_committed_records():
    records = [
        _record("file:a.md", [{"kind": "ref", "dst": "file:b.md", "grade": 10}]),
        _record("file:b.md", []),
    ]
    assert edges_from_records(records) == [Edge("file:a.md", "ref", "file:b.md", 10)]


def test_a_record_with_no_edges_contributes_nothing():
    assert edges_from_records([_record("file:a.md", [])]) == []


def test_outbound_is_directed_and_undirected_is_not():
    graph = Graph([Edge("a", "ref", "b", 10)])
    assert [e.dst for e in graph.out_edges("a")] == ["b"]
    assert graph.out_edges("b") == []
    assert graph.neighbours("b") == [("a", 10)]


def test_every_accessor_returns_a_sorted_view():
    """Sorted is L3, not tidiness — float accumulation order depends on it."""
    graph = Graph(
        [
            Edge("a", "ref", "z", 10),
            Edge("a", "ref", "b", 10),
            Edge("a", "code", "m", 8),
        ]
    )
    assert [e.dst for e in graph.out_edges("a")] == ["m", "b", "z"]  # by (kind, dst)
    assert graph.nodes == sorted(graph.nodes)
    assert graph.neighbours("a") == sorted(graph.neighbours("a"))


def test_documents_excludes_tag_nodes():
    graph = Graph([Edge("file:a.md", "tag", "tag:ops", 10)])
    assert graph.documents() == ["file:a.md"]
    assert "tag:ops" in graph.nodes


def test_an_empty_edge_set_is_an_empty_graph():
    graph = Graph([])
    assert len(graph) == 0 and graph.nodes == [] and graph.out_edges("a") == []


def test_the_same_edges_in_any_order_build_the_same_graph():
    edges = [Edge("a", "ref", "b", 10), Edge("b", "ref", "c", 10), Edge("a", "tag", "tag:x", 10)]
    baseline = Graph(edges)
    for rotation in range(1, len(edges)):
        other = Graph(edges[rotation:] + edges[:rotation])
        assert other.edges == baseline.edges
        assert other.nodes == baseline.nodes
        assert [other.neighbours(n) for n in other.nodes] == [
            baseline.neighbours(n) for n in baseline.nodes
        ]
