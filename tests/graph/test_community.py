"""Label propagation — determinism first, then that it actually separates.

The determinism assertions matter more than the quality ones here. A
non-deterministic community algorithm violates L3 silently: it does not error,
it does not change a ranking, and no retrieval test would ever see it. That is
exactly the failure class W-23 named as its hazard.
"""

from __future__ import annotations

import pytest

from fux.graph.community import MAX_SWEEPS, assign
from fux.graph.model import Edge, Graph


def _clique(prefix: str, size: int, grade: int = 10) -> list[Edge]:
    return [
        Edge(src=f"{prefix}{i}", kind="ref", dst=f"{prefix}{j}", grade=grade)
        for i in range(size)
        for j in range(size)
        if i != j
    ]


def test_two_disconnected_clusters_are_two_communities():
    graph = Graph(_clique("a", 4) + _clique("b", 3))
    labels = assign(graph)
    assert len({labels[f"a{i}"] for i in range(4)}) == 1
    assert len({labels[f"b{i}"] for i in range(3)}) == 1
    assert labels["a0"] != labels["b0"]


def test_a_bridge_does_not_merge_two_dense_clusters():
    """One weak link between two cliques is a bridge, not a merger."""
    graph = Graph(_clique("a", 5) + _clique("b", 5) + [Edge("a0", "code", "b0", 6)])
    labels = assign(graph)
    assert labels["a1"] != labels["b1"]


def test_labels_are_canonical_largest_community_first():
    """`c0` is the biggest community, not whichever node won the propagation.

    Without canonicalisation a label is an arbitrary node id, so adding one
    document can rename every community even when the partition is unchanged —
    a derived plane that churns for no reason.
    """
    graph = Graph(_clique("a", 5) + _clique("b", 2))
    labels = assign(graph)
    assert labels["a0"] == "c0"
    assert labels["b0"] == "c1"


def test_assignment_is_identical_across_runs_and_input_orders():
    """L3: the same edge set in a different order is the same partition.

    Shuffling the input is the cheap proxy for "a different machine" — it is
    what would differ if any iteration order in the algorithm came from a set
    or a dict insertion order rather than from a sort.
    """
    edges = _clique("a", 4) + _clique("b", 4) + [Edge("a0", "tag", "tag:x", 10)]
    baseline = assign(Graph(edges))
    for rotation in range(1, len(edges)):
        rotated = edges[rotation:] + edges[:rotation]
        assert assign(Graph(rotated)) == baseline


def test_no_randomness_is_imported_at_all():
    """The determinism claim, asserted against the source rather than trusted.

    The textbook algorithm is random twice over and the usual fix is a fixed
    seed. This build removes the randomness instead, which is the stronger
    guarantee — so the absence of the import is the thing to pin.
    """
    import ast
    import inspect

    from fux.graph import community

    tree = ast.parse(inspect.getsource(community))
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "random" not in imported, f"community assignment imports {imported}"
    # ...and no call goes out to one either, which an import check alone misses.
    calls = {
        ast.unparse(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    assert not any("random" in call or "shuffle" in call for call in calls), calls


def test_an_isolated_node_is_its_own_community():
    graph = Graph([Edge("a", "ref", "b", 10), Edge("c", "ref", "d", 10)])
    labels = assign(graph)
    assert labels["a"] == labels["b"]
    assert labels["c"] == labels["d"]
    assert labels["a"] != labels["c"]


def test_an_empty_graph_assigns_nothing():
    assert assign(Graph([])) == {}


def test_the_sweep_cap_is_a_count_not_a_convergence_test():
    """A float convergence test is how determinism dies at scale."""
    assert isinstance(MAX_SWEEPS, int) and MAX_SWEEPS > 0


def test_tags_join_the_documents_that_share_them():
    """A tag is a hub: two documents linked only by a shared tag are related."""
    graph = Graph(
        [
            Edge("file:a.md", "tag", "tag:ops", 10),
            Edge("file:b.md", "tag", "tag:ops", 10),
            Edge("file:z.md", "tag", "tag:other", 10),
        ]
    )
    labels = assign(graph)
    assert labels["file:a.md"] == labels["file:b.md"]
    assert labels["file:z.md"] != labels["file:a.md"]
