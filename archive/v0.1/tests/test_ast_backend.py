"""Optional tree-sitter backend + extractor provenance (plan §19a).

The heuristic-fallback parity is covered by test_astextract.py (it runs whichever
backend is active). Here we assert the *provenance* contract that keeps Fux
reproducible across machines, and — when the [ast] extra is installed — that the
tree-sitter path emits the same node/edge schema as the heuristic.
"""
from __future__ import annotations

import json

import pytest

from fux import astextract, check, paths

_HAS_TS = astextract._ts_parser("javascript") is not None
needs_ts = pytest.mark.skipif(not _HAS_TS, reason="[ast] extra not installed")


def test_fingerprint_shape():
    fp = astextract.backend_fingerprint()
    assert fp["non_python"] in ("heuristic", "tree-sitter")
    if fp["non_python"] == "tree-sitter":
        assert "tree_sitter" in fp and "grammars" in fp


def test_extractor_drift_finding(project):
    """A graph.json built with a different extractor surfaces a non-blocking
    advisory — divergence is auditable, never silent."""
    out = paths.Footprint(project).out
    out.mkdir(parents=True, exist_ok=True)
    bogus = {"non_python": "tree-sitter", "tree_sitter": "9.9.9",
             "grammars": "tree-sitter-language-pack==0.0.0"}
    (out / "graph.json").write_text(
        json.dumps({"nodes": [], "edges": [], "meta": {"extractor": bogus}}),
        encoding="utf-8")
    findings = check.run(project)
    drift = [f for f in findings if f.kind == "extractor-drift"]
    # Drift fires only if the current fingerprint differs from the bogus one
    # (it always does: real versions never equal 9.9.9).
    assert len(drift) == 1
    assert "reconcile" in drift[0].message


def test_no_drift_when_extractor_matches(project):
    out = paths.Footprint(project).out
    out.mkdir(parents=True, exist_ok=True)
    (out / "graph.json").write_text(
        json.dumps({"nodes": [], "edges": [],
                    "meta": {"extractor": astextract.backend_fingerprint()}}),
        encoding="utf-8")
    assert not [f for f in check.run(project) if f.kind == "extractor-drift"]


def test_graph_meta_carries_extractor(project):
    from fux import config, graph, loader
    cfg = config.load(paths.Footprint(project).config)
    g = graph.build(project, loader.resolve(project, cfg), cfg)
    assert g["meta"]["extractor"]["non_python"] in ("heuristic", "tree-sitter")


@needs_ts
def test_treesitter_js_schema_parity():
    src = ("function helper(x) { return x + 1; }\n"
           "export function main() { return helper(2); }\n"
           "class Foo { bar() { return helper(9); } }\n")
    nodes, edges = astextract.extract_text(src, ".js", "app.js")
    for n in nodes:                                   # same dict shape as _generic
        assert set(n) >= {"id", "label", "type", "file", "line"}
        assert n["type"] in ("function", "class")
    labels = {n["label"]: n["type"] for n in nodes}
    assert labels["Foo"] == "class" and labels["main"] == "function"
    calls = {(e["source"].split("::")[1], e["target"].split("::")[1])
             for e in edges if e["type"] == "calls"}
    assert ("main", "helper") in calls and ("bar", "helper") in calls


@needs_ts
def test_treesitter_go_struct_is_a_class_node():
    """The richer-AST win: Go structs become class nodes the brace heuristic missed."""
    src = ("package m\n"
           "type Server struct { x int }\n"
           "func (s *Server) Run() { helper() }\n"
           "func helper() { return }\n")
    nodes, _ = astextract.extract_text(src, ".go", "m.go")
    labels = {n["label"]: n["type"] for n in nodes}
    assert labels.get("Server") == "class"
    assert labels.get("Run") == "function"
