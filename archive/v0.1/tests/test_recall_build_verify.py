"""Recall ranking, build outputs + governs edges, verify pass/fail (plan §7/§10)."""
from __future__ import annotations

import json

from fux import build, recall, verify
from conftest import write_rule

DAY_PNL = """---
id: day-pnl
domain: portfolio
type: formula
status: active
created: 2026-06-01
updated: 2026-06-01
code_refs:
  - src/agg.py#L1-L2
check: "abs(sum(h['pnl'] for h in holdings) - total) < 0.01"
---
**Rule:** Today's P&L uses current INR value, not invested cost.
"""
OTHER = """---
id: greeting
type: rule
status: active
created: 2026-06-01
updated: 2026-06-01
---
**Rule:** unrelated cheerful note.
"""


def _seed(project):
    (project / "src" / "agg.py").write_text("def day_pnl(h):\n    return sum(h)\n", encoding="utf-8")
    write_rule(project, "day-pnl", DAY_PNL)
    write_rule(project, "greeting", OTHER)


def test_recall_ranks_relevant_rule_first(project):
    _seed(project)
    ranked = recall.run(project, "how is day P&L on my portfolio computed")
    assert ranked and ranked[0][0].id == "day-pnl"


def test_build_emits_views_and_governs_edge(project):
    _seed(project)
    build.run(project)
    out = project / ".fux" / "out"
    assert (out / "INDEX.md").exists()
    graph = json.loads((out / "graph.json").read_text())
    governs = [e for e in graph["edges"] if e["type"] == "governs"]
    assert any(e["source"] == "rule:day-pnl" and e["target"] == "src/agg.py" for e in governs)
    # AST extracted the function node from the Python source.
    assert any(n["id"] == "src/agg.py::day_pnl" for n in graph["nodes"])


def test_verify_pass_and_fail(project):
    _seed(project)
    vdir = project / ".fux" / "verify"
    vdir.mkdir(parents=True)
    (vdir / "day-pnl.json").write_text(json.dumps({"holdings": [{"pnl": 2000}], "total": 2000}))
    assert [v for v in verify.run(project) if v.rule_id == "day-pnl"][0].status == "pass"
    (vdir / "day-pnl.json").write_text(json.dumps({"holdings": [{"pnl": 1}], "total": 2000}))
    assert [v for v in verify.run(project) if v.rule_id == "day-pnl"][0].status == "fail"
