"""The three W-160 walk parameters must change NOTHING at their defaults.

**Why this test exists rather than a comment saying so.** W-161 needs
edge-kind selection, link-IDF and a hop bound; it is a ranking change and waits
on [W-156](../../work/open/W-156-prevalence-outside-golden.md). The mechanism is
not a ranking change and does not have to wait — but landing the two together
would make *"the walk moved"* and *"`ask` composes the walk"* one indivisible
diff, and no measurement could then attribute a delta to either.

So the parameters land first, off, and **a parameter added with the change that
uses it is a parameter nobody can prove was inert.** This is the proof.

Each test below asserts two things about one parameter: that its default is a
no-op *to the float*, and that a non-default value actually does something — a
knob that changes nothing at any setting is dead code wearing a feature's name,
and the inertness half would pass for it too.
"""

from __future__ import annotations

from fux.graph.model import Edge, Graph
from fux.graph.walk import ALL_KINDS, expand, link_idf, ppr


def _graph() -> Graph:
    """A small corpus with a hub, a tag, and a node three hops out.

    `hub` is pointed at by three documents, so link-IDF has something to
    discount. `tag:ops` is on two of them, so kind selection has a tag edge to
    exclude. `far` is three hops from `a`, so a hop bound has something to cut.
    """
    return Graph(
        [
            Edge(src="file:a.md", kind="ref", dst="file:hub.md", grade=10),
            Edge(src="file:b.md", kind="ref", dst="file:hub.md", grade=10),
            Edge(src="file:c.md", kind="ref", dst="file:hub.md", grade=10),
            Edge(src="file:a.md", kind="tag", dst="tag:ops", grade=10),
            Edge(src="file:b.md", kind="tag", dst="tag:ops", grade=10),
            Edge(src="file:hub.md", kind="ref", dst="file:mid.md", grade=8),
            Edge(src="file:mid.md", kind="ref", dst="file:far.md", grade=8),
        ]
    )


SEEDS = ["file:a.md", "file:b.md"]


def test_the_fixture_actually_walks_somewhere() -> None:
    """A fixture that scores nothing makes every assertion below vacuous."""
    scores = ppr(_graph(), SEEDS)
    assert len(scores) >= 5, scores
    assert scores["file:hub.md"] > 0


def test_kind_selection_is_inert_at_ALL_KINDS() -> None:
    graph = _graph()
    assert ppr(graph, SEEDS) == ppr(graph, SEEDS, kinds=ALL_KINDS)


def test_kind_selection_does_something_when_it_is_used() -> None:
    """`ref` only — the case W-161 wants: follow links, not tags."""
    graph = _graph()
    with_tags = ppr(graph, SEEDS)
    refs_only = ppr(graph, SEEDS, kinds=frozenset({"ref"}))
    assert "tag:ops" in with_tags
    assert refs_only.get("tag:ops", 0.0) == 0.0 or "tag:ops" not in refs_only
    assert with_tags != refs_only


def test_link_idf_is_inert_when_off() -> None:
    graph = _graph()
    assert ppr(graph, SEEDS) == ppr(graph, SEEDS, link_idf_on=False)


def test_link_idf_demotes_the_hub_when_on() -> None:
    """The hub has three inbound edges; `mid` has one. Turning link-IDF on must
    move mass away from the hub, or the parameter is decorative."""
    graph = _graph()
    off = ppr(graph, SEEDS)
    on = ppr(graph, SEEDS, link_idf_on=True)
    assert on["file:hub.md"] < off["file:hub.md"]


def test_link_idf_is_one_for_a_node_nothing_points_at() -> None:
    assert link_idf(0) == 1.0


def test_link_idf_is_monotone_and_never_reaches_zero() -> None:
    """Not `1 / in_degree`: a hub must stay in the walk, not fall out of it."""
    values = [link_idf(n) for n in (0, 1, 2, 10, 180, 10_000)]
    assert values == sorted(values, reverse=True)
    assert values[-1] > 0.0
    assert 0.15 < link_idf(180) < 0.20, link_idf(180)


def test_max_hops_is_inert_at_none() -> None:
    graph = _graph()
    assert ppr(graph, SEEDS) == ppr(graph, SEEDS, max_hops=None)


def test_max_hops_at_or_above_iterations_is_also_inert() -> None:
    """`iterations = 3` already bounds reach at three hops, so any bound at or
    above it can only re-state what the walk already does. Stated in the
    docstring; asserted here, because *"also inert"* is the half a reader is
    most likely to take on trust."""
    graph = _graph()
    baseline = ppr(graph, SEEDS)
    for bound in (3, 4, 99):
        assert ppr(graph, SEEDS, max_hops=bound) == baseline, bound


def test_max_hops_cuts_the_far_node_when_tight() -> None:
    graph = _graph()
    unbounded = ppr(graph, SEEDS)
    bounded = ppr(graph, SEEDS, max_hops=1)
    assert unbounded.get("file:far.md", 0.0) > 0.0
    assert bounded.get("file:far.md", 0.0) == 0.0


def test_expand_forwards_all_three_and_is_inert_at_its_defaults() -> None:
    """`expand` decides how many come back; `ppr` decides what the numbers mean.
    A parameter that `expand` silently dropped would be inert for the wrong
    reason, and the CLI calls `expand`, never `ppr`."""
    graph = _graph()
    baseline = expand(graph, SEEDS, limit=10)
    assert baseline == expand(
        graph, SEEDS, limit=10, kinds=ALL_KINDS, link_idf_on=False, max_hops=None
    )
    assert baseline != expand(graph, SEEDS, limit=10, link_idf_on=True)
    assert baseline != expand(graph, SEEDS, limit=10, kinds=frozenset({"ref"}))
    assert baseline != expand(graph, SEEDS, limit=10, max_hops=1)
