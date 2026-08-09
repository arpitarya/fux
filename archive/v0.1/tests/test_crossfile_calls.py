"""Cross-*file* call edges (symbol → symbol) for Python and brace languages."""
from __future__ import annotations

import json

from fux import build


def _calls(project):
    build.run(project)
    g = json.loads((project / ".fux" / "out" / "graph.json").read_text())
    return {(e["source"], e["target"]) for e in g["edges"] if e["type"] == "calls"}, g


def test_python_cross_file_call_edge(project):
    (project / "src" / "b.py").write_text("def helper():\n    return 1\n")
    (project / "src" / "a.py").write_text("def main():\n    return helper()\n")
    calls, _ = _calls(project)
    assert ("src/a.py::main", "src/b.py::helper") in calls


def test_ts_cross_file_call_edge(project):
    (project / "src" / "b.ts").write_text("export function helper(){ return 1; }\n")
    (project / "src" / "a.ts").write_text("function main(){ return helper(); }\n")
    calls, _ = _calls(project)
    assert ("src/a.ts::main", "src/b.ts::helper") in calls


def test_crossfile_calls_suppress_redundant_references(project):
    (project / "src" / "b.py").write_text("def helper():\n    return 1\n")
    (project / "src" / "a.py").write_text("def main():\n    return helper()\n")
    _, g = _calls(project)
    refs = {(e["source"], e["target"]) for e in g["edges"] if e["type"] == "references"}
    # The precise symbol→symbol call replaces the loose file→symbol reference.
    assert ("src/a.py", "src/b.py::helper") not in refs
