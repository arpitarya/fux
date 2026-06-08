"""Edge confidence + weight: loose `references` are INFERRED and down-weighted in
clustering/centrality, restoring the signal graphify carried as confidence labels."""
from __future__ import annotations

import json

from fux import community, graph, graphquery


def _build(project):
    # b.helper is called by a.main (precise symbol→symbol call) AND used at module
    # scope in c (a loose file→symbol `references`, since it's outside any function).
    (project / "src" / "b.py").write_text("def helper():\n    return 1\n")
    (project / "src" / "a.py").write_text("def main():\n    return helper()\n")
    (project / "src" / "c.py").write_text("helper()\n")       # module-level use → reference
    from fux import build
    build.run(project)
    return json.loads((project / ".fux" / "out" / "graph.json").read_text())


def test_every_edge_carries_confidence_and_weight(project):
    g = _build(project)
    assert g["edges"], "expected a non-empty graph"
    assert all("confidence" in e and "weight" in e for e in g["edges"])


def test_references_are_inferred_and_downweighted(project):
    g = _build(project)
    refs = [e for e in g["edges"] if e["type"] == "references"]
    calls = [e for e in g["edges"] if e["type"] == "calls"]
    assert refs and all(e["confidence"] == "INFERRED" and e["weight"] < 1.0 for e in refs)
    assert calls and all(e["confidence"] == "EXTRACTED" and e["weight"] == 1.0 for e in calls)


def test_stamp_confidence_by_type():
    edges = [{"source": "rule:r", "target": "src/x.py", "type": "governs"},
             {"source": "f", "target": "g", "type": "calls"},
             {"source": "a.py", "target": "g", "type": "references"},
             {"source": "rule:r", "target": "rule:s", "type": "supersedes"}]  # typed rule edge
    graph._stamp_confidence(edges)
    conf = {e["type"]: (e["confidence"], e["weight"]) for e in edges}
    assert conf["governs"] == ("EXTRACTED", 1.0)
    assert conf["calls"] == ("EXTRACTED", 1.0)
    assert conf["references"] == ("INFERRED", 0.25)
    assert conf["supersedes"] == ("EXTRACTED", 1.0)     # authored edge → default full weight


def test_pagerank_weight_aware_and_still_normalised():
    # A hub reached by one strong `calls` vs many weak `references`: weighting must
    # not break the probability-distribution invariant, and a low-weight edge moves
    # less rank than a full-weight one.
    nodes = [{"id": n} for n in ("hub", "strong", "weak")]
    g = {"nodes": nodes, "meta": {},
         "edges": [{"source": "hub", "target": "strong", "type": "calls", "weight": 1.0},
                   {"source": "hub", "target": "weak", "type": "references", "weight": 0.25}]}
    pr = graphquery.pagerank(g)
    assert abs(sum(pr.values()) - 1.0) < 1e-6
    assert pr["strong"] > pr["weak"]        # full-weight neighbour gains more rank


def test_community_adjacency_accumulates_weight():
    nodes = [{"id": n} for n in ("a", "b")]
    adj = community._adjacency(nodes, [
        {"source": "a", "target": "b", "weight": 0.25},
        {"source": "a", "target": "b", "weight": 1.0}])   # two edges → summed weight
    assert adj["a"]["b"] == 1.25 and adj["b"]["a"] == 1.25


def test_community_vote_follows_the_heavier_neighbourhood():
    # `mid` sees community A through a full-weight edge and B through a weak one;
    # the weighted vote must place it with A. A/B are pinned by their own heavy edge.
    nodes = [{"id": n} for n in ("a1", "a2", "b1", "b2", "mid")]
    edges = [{"source": "a1", "target": "a2", "weight": 1.0},
             {"source": "b1", "target": "b2", "weight": 1.0},
             {"source": "mid", "target": "a1", "weight": 1.0},
             {"source": "mid", "target": "b1", "weight": 0.25}]
    comm = community.detect(nodes, edges)
    assert comm["mid"] == comm["a1"]      # heavier neighbourhood wins
    assert comm["mid"] != comm["b1"]
