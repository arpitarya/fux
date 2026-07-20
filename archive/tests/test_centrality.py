"""PageRank centrality — deterministic, normalised, finds the hub (plan §17.19b)."""
from __future__ import annotations

from fux import graphquery, report


def _star(spokes: int = 5) -> dict:
    nodes = [{"id": "hub", "label": "hub", "type": "function"}]
    edges = []
    for i in range(spokes):
        nodes.append({"id": f"leaf{i}", "label": f"leaf{i}", "type": "function"})
        edges.append({"source": "hub", "target": f"leaf{i}", "type": "calls"})
    return {"nodes": nodes, "edges": edges,
            "meta": {"code_files": 0, "rules": 0, "communities": 0}}


def test_pagerank_is_normalised_and_deterministic():
    g = _star()
    a = graphquery.pagerank(g)
    b = graphquery.pagerank(g)
    assert a == b                                   # reproducible across runs
    assert abs(sum(a.values()) - 1.0) < 1e-6        # a probability distribution


def test_hub_outranks_leaves():
    pr = graphquery.pagerank(_star())
    assert pr["hub"] == max(pr.values())
    assert all(pr["hub"] > pr[f"leaf{i}"] for i in range(5))


def test_chokepoints_sorted_desc_and_in_report():
    g = _star()
    chokes = graphquery.chokepoints(g, top=3)
    assert chokes[0][0] == "hub"
    assert [s for _, s in chokes] == sorted((s for _, s in chokes), reverse=True)
    assert "Chokepoints (PageRank centrality)" in report.render(g)
