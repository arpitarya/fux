"""PPR-lite expansion: determinism, grade weighting, and fusion behaviour.

Constants are fixed by the handoff (damping 0.85, 3 iterations, top-10 ≥ 0.01,
EXTRACTED 1.0 / INFERRED 0.6, decay 0.8/hop). These tests pin the *properties*
those constants exist to produce — reproducibility and a defensible ordering —
rather than re-asserting the numbers, which config already documents.
"""

from __future__ import annotations

import json

import pytest

from fux.config import GraphParams, load
from fux.errors import FuxError
from fux.kernel import Edge, NodeRef, SeedDoc, _expanded, ppr, retrieve

from test_ingest import run

PARAMS = GraphParams()


def seeds(*ids):
    return [SeedDoc(doc_id=i, score=1.0) for i in ids]


def hub_edges():
    """a → b → c, plus a → d, so mass spreads at different depths."""
    return [
        Edge("a", "references", "b"),
        Edge("b", "references", "c"),
        Edge("a", "references", "d"),
    ]


# -- the algorithm ---------------------------------------------------------


def test_ppr_spreads_mass_from_seeds():
    scores = ppr(hub_edges(), seeds("a"), PARAMS)
    assert scores.get("b", 0) > 0 and scores.get("d", 0) > 0
    assert scores.get("c", 0) > 0  # two hops away, still reached in 3 iterations


def test_closer_nodes_score_higher():
    scores = ppr(hub_edges(), seeds("a"), PARAMS)
    assert scores["b"] > scores["c"], "a two-hop node must not outrank a one-hop node"


def test_extracted_edges_propagate_more_than_inferred():
    edges = [
        Edge("a", "references", "solid", "EXTRACTED"),
        Edge("a", "about", "soft", "INFERRED"),
    ]
    scores = ppr(edges, seeds("a"), PARAMS)
    assert scores["solid"] > scores["soft"]


def test_seed_rank_personalizes_the_walk():
    """The top-ranked seed must start with more mass than the second."""
    edges = [Edge("a", "references", "x"), Edge("b", "references", "y")]
    scores = ppr(edges, seeds("a", "b"), PARAMS)
    assert scores["x"] > scores["y"]


def test_is_deterministic_and_order_independent():
    edges = hub_edges()
    first = ppr(edges, seeds("a"), PARAMS)
    second = ppr(list(reversed(edges)), seeds("a"), PARAMS)
    assert first == second


def test_no_edges_or_no_seeds_yields_nothing():
    assert ppr([], seeds("a"), PARAMS) == {}
    assert ppr(hub_edges(), [], PARAMS) == {}


def test_cycles_terminate():
    edges = [Edge("a", "references", "b"), Edge("b", "references", "a")]
    scores = ppr(edges, seeds("a"), PARAMS)
    assert all(v == pytest.approx(v) for v in scores.values())  # finite, no blow-up
    assert scores


def test_iterations_are_fixed_not_convergence_based():
    """Fewer iterations must reach less far — proof the count is load-bearing."""
    shallow = ppr(hub_edges(), seeds("a"), GraphParams(iterations=1))
    deep = ppr(hub_edges(), seeds("a"), GraphParams(iterations=3))
    assert deep.get("c", 0) > shallow.get("c", 0)


# -- selection -------------------------------------------------------------


def test_expanded_excludes_seeds_and_applies_the_threshold():
    picked = _expanded(hub_edges(), seeds("a"), PARAMS)
    assert all(doc_id != "a" for doc_id, _ in picked)
    assert all(score >= PARAMS.min_score for _, score in picked)


def test_expanded_is_capped():
    edges = [Edge("a", "references", f"n{i}") for i in range(50)]
    assert len(_expanded(edges, seeds("a"), GraphParams(max_expanded=10))) == 10


def test_expanded_sorts_by_score_then_id():
    picked = _expanded(hub_edges(), seeds("a"), PARAMS)
    assert picked == sorted(picked, key=lambda kv: (-kv[1], kv[0]))


def test_threshold_can_exclude_everything():
    assert _expanded(hub_edges(), seeds("a"), GraphParams(min_score=0.99)) == []


# -- config ----------------------------------------------------------------


def test_graph_constants_match_the_handoff():
    p = GraphParams()
    assert (p.damping, p.iterations, p.max_expanded, p.min_score) == (0.85, 3, 10, 0.01)
    assert (p.extracted_weight, p.inferred_weight, p.hop_decay) == (1.0, 0.6, 0.8)


def test_graph_config_is_validated(tmp_path):
    (tmp_path / "fux.toml").write_text(
        '[sources]\ndocs = ["d"]\n[engine.graph]\ndamping = 2.0\n', encoding="utf-8"
    )
    with pytest.raises(FuxError, match=r"\[engine.graph\] damping"):
        load(tmp_path)

    (tmp_path / "fux.toml").write_text(
        '[sources]\ndocs = ["d"]\n[engine.graph]\niterations = 0\n', encoding="utf-8"
    )
    with pytest.raises(FuxError, match=r"\[engine.graph\] iterations"):
        load(tmp_path)


def test_in_rrf_is_toggleable(tmp_path):
    (tmp_path / "fux.toml").write_text(
        '[sources]\ndocs = ["d"]\n[engine.graph]\nin_rrf = false\n', encoding="utf-8"
    )
    assert load(tmp_path).graph.in_rrf is False


# -- integration -----------------------------------------------------------


def linked(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "hub.md").write_text(
        "---\ntitle: Hub\n---\n# Hub\n\nOnboarding overview. See [detail](detail.md).\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "detail.md").write_text(
        "---\ntitle: Detail\n---\n# Detail\n\nSpecific rollback procedures live here.\n",
        encoding="utf-8",
    )
    (tmp_path / "fux.toml").write_text('[sources]\ndocs = ["docs"]\n', encoding="utf-8")
    return tmp_path


def test_expansion_labels_nodes_with_their_ppr_score(tmp_path, monkeypatch):
    linked(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    graph = retrieve(load(tmp_path), "onboarding overview", k=1, expand_hops=1)
    expanded = [n for n in graph.nodes if n.via == "expanded"]
    assert expanded, "a linked neighbour must be reachable"
    assert all(n.score > 0 for n in expanded), "expanded nodes carry their ppr mass"


def test_lexical_only_never_fuses_the_graph(tmp_path, monkeypatch, capsys):
    linked(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    run(tmp_path, monkeypatch, "ask", "onboarding", "--json", "--lexical-only")
    payload = json.loads(capsys.readouterr().out)
    assert payload["engine"] == "bm25f"
    assert all("hybrid" not in r for r in payload["results"])


def test_in_rrf_false_leaves_passages_unfused(tmp_path, monkeypatch, capsys):
    linked(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    run(tmp_path, monkeypatch, "ask", "onboarding overview", "--json")
    with_graph = json.loads(capsys.readouterr().out)["results"]

    (tmp_path / "fux.toml").write_text(
        '[sources]\ndocs = ["docs"]\n[engine.graph]\nin_rrf = false\n', encoding="utf-8"
    )
    run(tmp_path, monkeypatch, "ask", "onboarding overview", "--json")
    without = json.loads(capsys.readouterr().out)["results"]
    assert not any("graph_rank" in (r.get("hybrid") or {}) for r in without)
    # the flag is the M8 instrument for handoff open question 2
    assert isinstance(with_graph, list) and isinstance(without, list)


def test_explain_stays_one_node_deep(tmp_path, monkeypatch):
    """Graph fusion must not attribute a neighbour's passage to this document."""
    linked(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    graph = retrieve(load(tmp_path), NodeRef("docs/hub.md"), k=5)
    assert all(p.file == "docs/hub.md" for p in graph.passages)


def test_expansion_is_deterministic_end_to_end(tmp_path, monkeypatch, capsys):
    linked(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    run(tmp_path, monkeypatch, "ask", "onboarding overview", "--json")
    first = capsys.readouterr().out
    run(tmp_path, monkeypatch, "ask", "onboarding overview", "--json")
    assert capsys.readouterr().out == first
