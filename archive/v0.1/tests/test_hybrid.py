"""RRF hybrid retrieval — fusion mechanics + graph-proximity boost ($0)."""
from __future__ import annotations

from pathlib import Path

from fux import build, hybrid, recall
from fux.model import Rule
from conftest import write_rule

GOV = """---
id: day-pnl
domain: portfolio
type: formula
status: active
created: 2026-06-01
updated: 2026-06-01
code_refs:
  - src/agg.py#L1-L2
related: [inr-normalization]
---
**Rule:** Today's P&L on current INR value. **Why:** relative to yesterday close.
"""
NORM = """---
id: inr-normalization
domain: portfolio
type: rule
status: active
created: 2026-06-01
updated: 2026-06-01
code_refs:
  - src/agg.py#L3-L4
---
**Rule:** Convert foreign holdings to rupees before summing. **Why:** one currency.
"""


def test_rrf_fuses_multiple_rankings():
    scores = hybrid._rrf([["a", "b", "c"], ["b", "a"]])
    # `a` and `b` both appear high in two lists; both beat the singleton `c`.
    assert scores["b"] > scores["c"] and scores["a"] > scores["c"]


def test_hybrid_ranks_relevant_rule_first(project):
    (project / "src" / "agg.py").write_text("def day_pnl(h):\n    return _inr(h)\n"
                                            "def _inr(h):\n    return h\n")
    write_rule(project, "day-pnl", GOV)
    write_rule(project, "inr-normalization", NORM)
    build.run(project)
    ranked = recall.run(project, "how is day P&L computed", top=3, hybrid=True)
    assert ranked and ranked[0][0].id == "day-pnl"


def test_graph_ranking_empty_without_graph(project):
    # No build yet → no graph.json → graph signal degrades gracefully to [].
    assert hybrid._graph_ranking(project, ["day-pnl"]) == []


def test_graph_anchors_fall_back_to_semantic_when_lexical_empty(project, monkeypatch):
    # The paraphrase case hybrid exists for: zero lexical hits. The graph leg must
    # still seed — from the semantic top — instead of going dark.
    rule = Rule(id="inr-normalization", type="rule", fm={}, body="",
                path=Path("x"), layer="project")
    captured: dict[str, list[str]] = {}
    monkeypatch.setattr(hybrid.recall, "rank", lambda *a, **k: [])      # empty lexical
    monkeypatch.setattr(hybrid, "_semantic_ranking", lambda q, rs: ["inr-normalization"])
    monkeypatch.setattr(hybrid, "_graph_ranking",
                        lambda root, anchors: captured.setdefault("anchors", anchors) and [])
    hybrid.fuse(project, "anything", [rule])
    assert captured["anchors"] == ["inr-normalization"]
