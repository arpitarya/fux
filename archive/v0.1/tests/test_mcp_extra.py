"""Expanded MCP surface — query/trace/new tools ($0, plan §17.5)."""
from __future__ import annotations

from fux import build, mcpserver
from conftest import write_rule

RULE = """---
id: day-pnl
domain: portfolio
type: formula
status: active
created: 2026-06-01
updated: 2026-06-01
code_refs:
  - src/agg.py#L1-L2
---
**Rule:** Today's P&L. **Why:** relative to yesterday.
"""


def _seed(project):
    (project / "src" / "agg.py").write_text("def day_pnl(h):\n    return sum(h)\n")
    write_rule(project, "day-pnl", RULE)
    build.run(project)


def test_tools_list_includes_new_tools():
    tools = {t["name"] for t in mcpserver.TOOLS}
    assert {"fux_query", "fux_trace", "fux_new"} <= tools


def test_query_traverses_to_governed_file(project):
    _seed(project)
    text = mcpserver._call("fux_query", {"query": "day pnl", "depth": 1})
    assert "day-pnl" in text and "agg.py" in text


def test_new_creates_a_draft_stub(project):
    out = mcpserver._call("fux_new", {"type": "rule", "id": "broker-quirk"})
    assert "draft" in out.lower()
    created = project / ".fux" / "rules" / "broker-quirk.md"
    assert created.exists() and "status: draft" in created.read_text()


def test_query_without_graph_is_graceful(project):
    write_rule(project, "day-pnl", RULE)        # no build → no graph.json
    text = mcpserver._call("fux_query", {"query": "day pnl"})
    assert "fux build" in text
