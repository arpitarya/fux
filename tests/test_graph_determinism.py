"""Reproducible builds: `_xref` iterates a set (`call_names`), so without an
explicit sort the `references` edge order — and thus graph.json — churns across
builds under hash randomization, making committed views noisy. The fix sorts the
iteration; this guards it by asserting the emitted order is canonical (sorted)."""
from __future__ import annotations

import json

from fux import build


def _refs_from(project, src_file):
    g = json.loads((project / ".fux" / "out" / "graph.json").read_text())
    return [e for e in g["edges"]
            if e["type"] == "references" and e["source"] == src_file]


def test_reference_edges_emitted_in_sorted_target_order(project):
    # caller.py references three symbols defined elsewhere, at module scope (so they
    # are loose file→symbol `references`, the edges built by `_xref`).
    (project / "src" / "defs.py").write_text(
        "def zeta():\n    return 1\n\ndef alpha():\n    return 2\n\ndef mu():\n    return 3\n")
    (project / "src" / "caller.py").write_text("zeta()\nalpha()\nmu()\n")
    build.run(project)

    refs = _refs_from(project, "src/caller.py")
    names = [e["target"].split("::", 1)[1] for e in refs]
    assert set(names) >= {"alpha", "mu", "zeta"}, names
    # canonical order — independent of set-iteration / PYTHONHASHSEED.
    assert names == sorted(names), f"reference edges not in sorted order: {names}"
