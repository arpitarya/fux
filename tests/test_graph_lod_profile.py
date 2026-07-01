"""Q1 (viewer LOD + ego-graph + build profiler + --no-xref).

Guards, in order: the default graph.json is byte-identical across hash seeds (the
determinism fix for the unsorted set-iteration in the generic extractor); the new
opt-in `--no-xref` mode drops *only* `references` edges; `--profile` reports every
build phase; and the viewer template carries the LOD threshold + ego-graph affordances.
The default build output must stay byte-identical to today — new modes are opt-in.
"""
from __future__ import annotations

import json
import subprocess
import sys

from fux import build, cli, graphhtml


def _multi_call_project(project):
    """A brace-language (JS) file whose function calls three helpers in non-sorted
    order — the case the generic extractor iterated as a set (hash-order churn) —
    plus a module-scope Python caller that yields loose cross-file `references`."""
    (project / "src" / "helpers.js").write_text(
        "function zeta(){return 1}\nfunction alpha(){return 2}\nfunction mu(){return 3}\n"
        "function run(){ zeta(); mu(); alpha(); }\n", encoding="utf-8")
    (project / "src" / "defs.py").write_text(
        "def zeta():\n    return 1\n\ndef alpha():\n    return 2\n\ndef mu():\n    return 3\n",
        encoding="utf-8")
    (project / "src" / "caller.py").write_text("zeta()\nalpha()\nmu()\n", encoding="utf-8")
    return project


def _graph(project):
    return json.loads((project / ".fux" / "out" / "graph.json").read_text())


def test_default_build_byte_identical_across_hash_seeds(project):
    """The default graph.json must be reproducible regardless of PYTHONHASHSEED —
    two builds in fresh interpreters with different seeds produce identical bytes."""
    _multi_call_project(project)

    def build_bytes(seed: str) -> bytes:
        env = {"PYTHONHASHSEED": seed, "PATH": __import__("os").environ.get("PATH", ""),
               "HOME": __import__("os").environ.get("HOME", "")}
        subprocess.run([sys.executable, "-m", "fux", "build"], cwd=project,
                       check=True, env=env, capture_output=True)
        return (project / ".fux" / "out" / "graph.json").read_bytes()

    assert build_bytes("1") == build_bytes("2") == build_bytes("13")


def test_intra_file_calls_emitted_in_sorted_order(project):
    """Direct guard on the generic-extractor sort fix: intra-file `calls` edges come
    out in canonical (sorted target) order, not set-iteration order."""
    _multi_call_project(project)
    build.run(project)
    calls = [e["target"].split("::", 1)[1] for e in _graph(project)["edges"]
             if e["type"] == "calls" and e["source"] == "src/helpers.js::run"]
    assert set(calls) == {"alpha", "mu", "zeta"}, calls
    assert calls == sorted(calls), f"intra-file calls not canonically sorted: {calls}"


def test_no_xref_drops_only_references(project):
    """`--no-xref` is a strict edge-subtraction: every `references` edge gone, every
    other edge identical. (Community/centrality legitimately re-derive from the
    smaller edge set — that is expected and not asserted here.)"""
    _multi_call_project(project)
    build.run(project)
    full = _graph(project)
    build.run(project, no_xref=True)
    nox = _graph(project)

    assert any(e["type"] == "references" for e in full["edges"])   # fixture has some
    assert not any(e["type"] == "references" for e in nox["edges"])
    keep = lambda g: {(e["source"], e["target"], e["type"])
                      for e in g["edges"] if e["type"] != "references"}
    assert keep(full) == keep(nox)
    assert [n["id"] for n in full["nodes"]] == [n["id"] for n in nox["nodes"]]


def test_default_build_unchanged_by_new_flags(project):
    """The new flags are additive: a plain build and a build with the profiler on
    (no --no-xref) write byte-identical graph.json — timings never touch the graph."""
    _multi_call_project(project)
    build.run(project)
    plain = (project / ".fux" / "out" / "graph.json").read_bytes()
    build.run(project, profile=True)
    profiled = (project / ".fux" / "out" / "graph.json").read_bytes()
    assert plain == profiled


def test_profile_reports_every_phase(project, capsys):
    _multi_call_project(project)
    assert cli.main(["build", "--profile"]) == 0
    out = capsys.readouterr().out
    for phase in ("extraction", "cross-file calls", "_xref", "community",
                  "pagerank", "serialize", "total"):
        assert phase in out, f"missing phase '{phase}' in --profile output:\n{out}"


def test_viewer_carries_lod_threshold_and_ego_affordances():
    g = {"nodes": [{"id": "a", "label": "a", "type": "code-file", "community": 0}],
         "edges": [], "meta": {}}
    html = graphhtml.render(g, lod_threshold=1800)
    assert "__LOD__" not in html
    assert "const LOD_THRESHOLD = 1800;" in html
    # ego-graph (selectable 1–2 hop) + community-collapse LOD affordances present.
    for marker in ("egoSet", "egoHops", "startCollapsed", "expandCommunity",
                   "communityAtScreen", 'id="bfocus"', 'data-hop="2"'):
        assert marker in html, f"missing viewer marker: {marker}"
