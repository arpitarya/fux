"""The retrieval kernel and its verb projections.

The load-bearing property: every verb is a *view* of one `retrieve()` call.
Where a test asserts that two verbs agree, it is guarding against the second
code path this design exists to prevent.
"""

from __future__ import annotations

import json

import pytest

from fux.config import load
from fux.errors import FuxError
from fux.kernel import GRADE_WEIGHT, HOP_DECAY, NodeRef, Edge, Path, paths_between, retrieve

from test_ingest import make_project, run


def linked_project(tmp_path):
    make_project(tmp_path)
    docs = tmp_path / "docs"
    (docs / "guide.md").write_text(
        "---\ntitle: The Guide\ntags: [howto]\n---\n"
        "# Guide\n\nOnboarding: install the widget service, then read the [runbook](runbook.md).\n"
        "## Citations\n\n- [spec](spec.md)\n",
        encoding="utf-8",
    )
    (docs / "runbook.md").write_text(
        "---\ntitle: Runbook\n---\n# Runbook\n\nRollback the widget within ten minutes.\n"
        "See the [spec](spec.md).\n",
        encoding="utf-8",
    )
    (docs / "spec.md").write_text(
        "---\ntitle: Spec\n---\n# Spec\n\nThe widget service specification.\n",
        encoding="utf-8",
    )
    (docs / "orphan.md").write_text(
        "---\ntitle: Orphan\n---\n# Orphan\n\nNothing links here or from here.\n",
        encoding="utf-8",
    )
    return tmp_path


def ingested(tmp_path, monkeypatch):
    linked_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    return load(tmp_path)


# -- the kernel ------------------------------------------------------------


def test_text_seed_produces_passages_seeds_and_nodes(tmp_path, monkeypatch):
    config = ingested(tmp_path, monkeypatch)
    graph = retrieve(config, "widget service", k=5)
    assert graph.passages
    assert graph.seeds
    assert {n.doc_id for n in graph.nodes} >= {s.doc_id for s in graph.seeds}


def test_seed_docs_are_ranked_by_best_passage(tmp_path, monkeypatch):
    config = ingested(tmp_path, monkeypatch)
    graph = retrieve(config, "widget", k=20)
    scores = [s.score for s in graph.seeds]
    assert scores == sorted(scores, reverse=True)
    assert len({s.doc_id for s in graph.seeds}) == len(graph.seeds)  # one row per doc


def test_node_seed_uses_the_documents_own_terms(tmp_path, monkeypatch):
    """`explain` is `ask` seeded by a node — not a second retrieval path."""
    config = ingested(tmp_path, monkeypatch)
    graph = retrieve(config, NodeRef("docs/spec.md"), k=5)
    assert all(p.file == "docs/spec.md" for p in graph.passages)
    assert graph.passages, "a node seed must surface its own passages"


def test_node_seed_for_a_missing_doc_is_a_clean_error(tmp_path, monkeypatch):
    config = ingested(tmp_path, monkeypatch)
    with pytest.raises(FuxError, match="no document"):
        retrieve(config, NodeRef("docs/nope.md"), k=5)


def test_lexical_only_bypasses_dense(tmp_path, monkeypatch):
    config = ingested(tmp_path, monkeypatch)
    graph = retrieve(config, "widget service", k=5, lexical_only=True)
    assert graph.engine == "bm25f"
    assert all(p.hybrid is None for p in graph.passages)


def test_edges_are_restricted_to_the_neighbourhood(tmp_path, monkeypatch):
    config = ingested(tmp_path, monkeypatch)
    graph = retrieve(config, "orphan", k=1)
    seed_ids = {s.doc_id for s in graph.seeds}
    for edge in graph.edges:
        assert edge.src in seed_ids or edge.dst in seed_ids


def test_expansion_reaches_one_hop_neighbours(tmp_path, monkeypatch):
    """A seed's neighbours join the node set even when they never scored.

    Seeded on a term unique to one document, so the neighbours can only have
    arrived by traversal — and they are labelled `expanded`, since a document
    that scored on its own would be a seed.
    """
    config = ingested(tmp_path, monkeypatch)
    graph = retrieve(config, "onboarding", k=1, expand_hops=1)
    assert "docs/guide.md" in {s.doc_id for s in graph.seeds}
    expanded = {n.doc_id for n in graph.nodes if n.via == "expanded"}
    assert {"docs/runbook.md", "docs/spec.md", "tag:howto"} <= expanded


def test_a_document_that_scored_is_a_seed_not_an_expansion(tmp_path, monkeypatch):
    config = ingested(tmp_path, monkeypatch)
    graph = retrieve(config, "widget", k=20, expand_hops=1)
    seed_ids = {s.doc_id for s in graph.seeds}
    for node in graph.nodes:
        assert (node.via == "seed") == (node.doc_id in seed_ids)


def test_zero_hops_expands_nothing(tmp_path, monkeypatch):
    config = ingested(tmp_path, monkeypatch)
    graph = retrieve(config, "widget", k=3, expand_hops=0)
    assert all(n.via == "seed" for n in graph.nodes)
    assert graph.paths == []


def test_retrieval_is_deterministic(tmp_path, monkeypatch):
    config = ingested(tmp_path, monkeypatch)
    first = retrieve(config, "widget service", k=5)
    second = retrieve(config, "widget service", k=5)
    assert [(p.file, p.ordinal, p.score) for p in first.passages] == [
        (p.file, p.ordinal, p.score) for p in second.passages
    ]
    assert [(e.src, e.kind, e.dst) for e in first.edges] == [
        (e.src, e.kind, e.dst) for e in second.edges
    ]


def test_empty_corpus_yields_an_empty_graph(tmp_path, monkeypatch):
    (tmp_path / "fux.toml").write_text("[sources]\ndocs = []\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    run(tmp_path, monkeypatch, "ingest")
    from fux.index import sqlstore, store

    store.save(tmp_path, {}, edges=[])
    graph = retrieve(load(tmp_path), "anything", k=5)
    assert graph.passages == [] and graph.nodes == [] and graph.paths == []


# -- paths and reliability -------------------------------------------------


def test_path_reliability_uses_grade_and_decay():
    from fux.kernel import _paths

    edges = [Edge("a", "references", "b", "EXTRACTED"), Edge("b", "cites", "c", "INFERRED")]
    paths = _paths(edges, {"a"}, hops=2)
    direct = next(p for p in paths if p.end == "b")
    assert direct.reliability == pytest.approx(GRADE_WEIGHT["EXTRACTED"])
    two_hop = next(p for p in paths if p.end == "c")
    expected = GRADE_WEIGHT["EXTRACTED"] * GRADE_WEIGHT["INFERRED"] * HOP_DECAY
    assert two_hop.reliability == pytest.approx(expected, rel=1e-9)


def test_inferred_chains_never_outrank_a_recorded_fact():
    from fux.kernel import _paths

    edges = [
        Edge("a", "references", "direct", "EXTRACTED"),
        Edge("a", "about", "x", "INFERRED"),
        Edge("x", "about", "far", "INFERRED"),
    ]
    paths = _paths(edges, {"a"}, hops=2)
    best = paths[0]
    assert best.end == "direct"


def test_paths_do_not_cycle():
    from fux.kernel import _paths

    edges = [Edge("a", "references", "b"), Edge("b", "references", "a")]
    for path in _paths(edges, {"a"}, hops=3):
        ends = [h.dst for h in path.hops]
        assert len(ends) == len(set(ends))
        assert "a" not in ends  # never loops back to its own start


def test_paths_between_filters_to_landing_trails():
    from fux.kernel import ResultGraph

    p1 = Path(hops=(Edge("a", "references", "b"),), reliability=1.0)
    p2 = Path(hops=(Edge("a", "references", "c"),), reliability=1.0)
    graph = ResultGraph(paths=[p1, p2])
    assert paths_between(graph, "a", "b") == [p1]
    assert paths_between(graph, "a", "zzz") == []


# -- verb projections agree with the kernel --------------------------------


def test_explain_json_matches_the_kernel(tmp_path, monkeypatch, capsys):
    ingested(tmp_path, monkeypatch)
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "explain", "docs/guide.md", "--json") == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["node"]["path"] == "docs/guide.md"
    assert payload["outline"]
    kinds = {(e["kind"], e["dst"]) for e in payload["edges"]}
    assert ("references", "docs/runbook.md") in kinds
    assert ("cites", "docs/spec.md") in kinds
    assert all(p["path"] == "docs/guide.md" for p in payload["passages"])


def test_explain_on_a_missing_doc_exits_one(tmp_path, monkeypatch, capsys):
    ingested(tmp_path, monkeypatch)
    assert run(tmp_path, monkeypatch, "explain", "docs/nope.md") == 1
    assert "no document" in capsys.readouterr().err


def test_graph_json_lists_nodes_and_edges(tmp_path, monkeypatch, capsys):
    ingested(tmp_path, monkeypatch)
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "graph", "widget service", "--json") == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["nodes"]
    assert {n["via"] for n in payload["nodes"]} <= {"seed", "expanded"}
    for edge in payload["edges"]:
        assert edge["grade"] == "EXTRACTED"


def test_graph_on_no_match_is_honest(tmp_path, monkeypatch, capsys):
    ingested(tmp_path, monkeypatch)
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "graph", "zzzznotintheconsole") == 0
    assert "No confident matches." in capsys.readouterr().out


def test_path_reports_a_real_route(tmp_path, monkeypatch, capsys):
    ingested(tmp_path, monkeypatch)
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "path", "docs/guide.md", "docs/runbook.md") == 0
    out = capsys.readouterr().out
    assert "1 path" in out and "references" in out and "[EXTRACTED]" in out


def test_path_with_no_route_says_so(tmp_path, monkeypatch, capsys):
    ingested(tmp_path, monkeypatch)
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "path", "docs/guide.md", "docs/orphan.md") == 0
    assert "no recorded path" in capsys.readouterr().out


def test_zero_hop_path_is_handled(tmp_path, monkeypatch, capsys):
    ingested(tmp_path, monkeypatch)
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "path", "docs/guide.md", "docs/guide.md") == 0
    assert "same document (0 hops)" in capsys.readouterr().out


def test_two_hop_path_needs_the_flag(tmp_path, monkeypatch, capsys):
    """guide → runbook → (nothing new); guide cites spec directly, so use hops."""
    ingested(tmp_path, monkeypatch)
    capsys.readouterr()
    run(tmp_path, monkeypatch, "path", "docs/guide.md", "docs/spec.md", "--json", "--hops", "2")
    payload = json.loads(capsys.readouterr().out)
    assert payload["paths"], "a two-hop route must be reachable with --hops 2"
    assert payload["paths"] == sorted(
        payload["paths"], key=lambda p: -p["reliability"]
    )
