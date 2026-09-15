"""PPR-lite expansion and bounded route enumeration."""

from __future__ import annotations

import pytest

from fux.graph.model import Edge, Graph
from fux.graph.walk import DAMPING, HOP_DECAY, ITERATIONS, expand, ppr, reliability, routes


@pytest.fixture
def chain() -> Graph:
    return Graph(
        [
            Edge("a", "ref", "b", 10),
            Edge("b", "ref", "c", 10),
            Edge("c", "ref", "d", 10),
            Edge("x", "ref", "y", 10),
        ]
    )


def test_ppr_scores_decrease_monotonically_with_distance(chain):
    """The parity artefact the lazy walk exists to remove.

    The archived walk moves *all* of a node's mass each step, so on a path
    graph with `ITERATIONS = 3` the node three hops out scored **above** the
    node two hops out — measured 0.154 vs 0.054. A `graph` verb that puts a
    stranger above a neighbour is wrong, not merely imprecise.
    """
    scores = ppr(chain, ["a"])
    assert scores["b"] > scores["c"] > scores["d"] > 0.0


def test_the_walk_is_lazy_and_that_is_load_bearing():
    """Pin the mechanism, not just the symptom — laziness is what makes the
    fixed iteration count safe on a bipartite-ish graph."""
    from fux.graph.walk import LAZINESS

    assert 0 < LAZINESS < 1


def test_ppr_is_personalized_by_rank_not_by_score(chain):
    """The first seed starts with the most mass, so expansion inherits the
    ranker's opinion instead of flattening it."""
    first = ppr(chain, ["a", "x"])
    second = ppr(chain, ["x", "a"])
    assert first["a"] > first["x"]
    assert second["x"] > second["a"]


def test_ppr_is_byte_stable_across_input_orders(chain):
    edges = list(chain.edges)
    baseline = ppr(Graph(edges), ["a"])
    for rotation in range(1, len(edges)):
        assert ppr(Graph(edges[rotation:] + edges[:rotation]), ["a"]) == baseline


def test_ppr_iteration_count_is_fixed_not_a_convergence_test():
    assert isinstance(ITERATIONS, int) and 0 < DAMPING < 1


def test_expand_excludes_the_seeds(chain):
    assert "a" not in {node for node, _ in expand(chain, ["a"], limit=10)}


def test_expand_ties_break_on_id():
    """Two nodes at identical distance must order by id, not by dict order."""
    graph = Graph([Edge("seed", "ref", "z", 10), Edge("seed", "ref", "a", 10)])
    assert [node for node, _ in expand(graph, ["seed"], limit=10)] == ["a", "z"]


def test_ppr_on_an_empty_graph_is_empty():
    assert ppr(Graph([]), ["a"]) == {}
    assert ppr(Graph([Edge("a", "ref", "b", 10)]), []) == {}


def test_routes_finds_the_direct_edge(chain):
    found, _ = routes(chain, "a", "b", hops=2)
    assert len(found) == 1
    assert found[0].reliability == 1.0


def test_routes_are_directed(chain):
    """`path` follows the way the document points — b never said anything about a."""
    assert routes(chain, "b", "a", hops=3)[0] == []


def test_tag_nodes_are_sinks_so_a_route_cannot_launder_through_a_label():
    """Two documents sharing a tag are *related*, not *connected*.

    Routing through a tag would make every pair of documents in a large tag
    two hops apart, which makes `path` useless at exactly the scale it matters.
    """
    graph = Graph(
        [Edge("file:a.md", "tag", "tag:ops", 10), Edge("file:b.md", "tag", "tag:ops", 10)]
    )
    assert routes(graph, "file:a.md", "file:b.md", hops=3)[0] == []


def test_reliability_decays_strictly_with_distance(chain):
    one = routes(chain, "a", "b", hops=3)[0][0].reliability
    two = routes(chain, "a", "c", hops=3)[0][0].reliability
    three = routes(chain, "a", "d", hops=3)[0][0].reliability
    assert 1.0 == one > two > three > 0.0


def test_a_lower_grade_hop_is_less_reliable():
    strong = Graph([Edge("a", "ref", "b", 10)])
    weak = Graph([Edge("a", "code", "b", 8)])
    assert routes(weak, "a", "b", hops=1)[0][0].reliability < routes(strong, "a", "b", hops=1)[0][0].reliability


def test_reliability_is_bounded_by_one():
    assert reliability([Edge("a", "ref", "b", 10)]) == 1.0
    assert reliability([Edge("a", "ref", "b", 10), Edge("b", "ref", "c", 10)]) == HOP_DECAY


def test_the_hop_budget_is_respected(chain):
    assert routes(chain, "a", "d", hops=2)[0] == []
    assert routes(chain, "a", "d", hops=3)[0]


def test_routes_are_simple_so_a_cycle_cannot_unbound_the_search():
    graph = Graph(
        [Edge("a", "ref", "b", 10), Edge("b", "ref", "a", 10), Edge("b", "ref", "c", 10)]
    )
    found, _ = routes(graph, "a", "c", hops=5)
    assert len(found) == 1
    assert [e.dst for e in found[0].hops] == ["b", "c"]


def test_a_node_never_routes_to_itself():
    assert routes(Graph([Edge("a", "ref", "a", 10)]), "a", "a", hops=3)[0] == []


def test_routes_are_ordered_most_reliable_first():
    graph = Graph(
        [
            Edge("a", "ref", "mid", 10),
            Edge("mid", "ref", "z", 10),
            Edge("a", "ref", "z", 8),  # weaker, but direct
        ]
    )
    found, _ = routes(graph, "a", "z", hops=2)
    assert len(found) == 2
    assert [r.reliability for r in found] == sorted((r.reliability for r in found), reverse=True)


# ---------------------------------------------------------------------------
# W-140 row 12 — the expansion budget (Arpit, 2026-09-14, option (c))
# ---------------------------------------------------------------------------


def _dense(n: int) -> Graph:
    """A complete-ish digraph: every node points at every later node.

    Simple-path DFS over this is factorial in `n`, which is the shape the
    budget exists for — `--hops 6` on a real linked corpus is the same
    explosion with more steps in between.
    """
    return Graph([
        Edge(f"n{i}", "ref", f"n{j}", 10)
        for i in range(n) for j in range(n) if i != j
    ])


def test_a_bounded_search_reports_that_it_was_cut_short():
    """🔴 **The whole ruling in one assertion.**

    *No route within N hops* asserts the search finished. *No route found in
    the first N expansions* does not. Returning the first when the second is
    true is a confident answer to a question that was never completed — and
    `fux path` had already shipped this exact ambiguity once.
    """
    found, truncated = routes(_dense(8), "n0", "nope", hops=7, budget=50)
    assert truncated is True
    assert found == [], "nothing was found — and that is not the same as nothing existing"


def test_an_unbounded_search_reports_that_it_was_not():
    """`truncated` is `False` on every search that actually finished, which is
    what makes the `True` mean something."""
    found, truncated = routes(_dense(4), "n0", "n3", hops=3)
    assert truncated is False
    assert found, "the route exists and the search had room to find it"


def test_truncated_describes_the_SEARCH_and_not_the_RESULT_SET():
    """⚠ **A truncated search that found routes is still truncated.**

    It may have missed a better one, so the flag cannot be an empty-list
    sentinel — which is exactly why `routes()` returns a second value rather
    than signalling through the first.
    """
    found, truncated = routes(_dense(9), "n0", "n8", hops=8, budget=40)
    assert truncated is True
    assert found, "some routes were reached before the budget ran out"


def test_the_budget_is_spent_on_node_expansions_and_the_cut_is_deterministic():
    """The unit is node expansions, and `out_edges` is sorted — so *where* the
    budget runs out is a function of the index, not of the machine. Two runs on
    one graph truncate identically, and so do two machines."""
    graph = _dense(9)
    first = routes(graph, "n0", "n8", hops=8, budget=40)
    second = routes(graph, "n0", "n8", hops=8, budget=40)
    assert [r.hops for r in first[0]] == [r.hops for r in second[0]]
    assert first[1] == second[1] is True


def test_a_generous_budget_changes_nothing_about_a_small_search():
    """The default must be inert on every graph small enough to finish — or the
    bound would be a ranking change wearing a safety feature's name."""
    graph = _dense(5)
    bounded, truncated = routes(graph, "n0", "n4", hops=4)
    huge, huge_truncated = routes(graph, "n0", "n4", hops=4, budget=10**9)
    assert truncated is False and huge_truncated is False
    assert [r.hops for r in bounded] == [r.hops for r in huge]
