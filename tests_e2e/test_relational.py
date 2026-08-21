"""Relational eval: the graph lane's surfaces, measured through the real CLI.

Retrieval metrics are blind to `explain`, `graph` and `path` — they score
passages, and these verbs return relationships. This is the instrument for
those, ported from `archive/v0.26/tests_e2e/test_relational.py` with its
corpus and its cases.

The port's one adaptation — the edge vocabulary, `references`/`cites` → `ref`
— is stated in `eval/README-relational.md` rather than left to be discovered.
The archived file is **named, never cited**: this test and its fixture are
live files in this tree, and nothing here reads out of `archive/`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

EVAL_DIR = Path(__file__).parent / "eval"
PAIRS = EVAL_DIR / "relational.jsonl"
CORPUS = EVAL_DIR / "relational"


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "fux.cli", *args],
        cwd=cwd, capture_output=True, text=True, check=True,
    )


def load_pairs(kind: str) -> list[dict]:
    return [
        entry
        for line in PAIRS.read_text(encoding="utf-8").splitlines()
        if line.strip()
        for entry in [json.loads(line)]
        if entry["kind"] == kind
    ]


@pytest.fixture(scope="module")
def linked(tmp_path_factory) -> Path:
    proj = tmp_path_factory.mktemp("relational")
    shutil.copytree(CORPUS / "docs", proj / "docs")
    (proj / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    dirs = proj / ".fux" / "sources" / "dirs"
    dirs.parent.mkdir(parents=True, exist_ok=True)
    dirs.write_text("docs\n", encoding="utf-8")
    _run(proj, "ingest")
    return proj


@pytest.mark.parametrize("case", load_pairs("path"), ids=lambda c: f"{c['from']}->{c['to']}")
def test_expected_paths_are_found(linked, case):
    payload = json.loads(
        _run(linked, "path", case["from"], case["to"], "--json", "--hops", str(case["hops"])).stdout
    )
    assert payload["paths"], f"no route {case['from']} → {case['to']}"
    best = payload["paths"][0]
    assert best["hops"][0]["kind"] == case["expect"]
    assert best["hops"][-1]["dst"] == f"file:{case['to']}"
    assert 0 < best["reliability"] <= 1.0


@pytest.mark.parametrize("case", load_pairs("nopath"), ids=lambda c: f"{c['from']}-x-{c['to']}")
def test_absent_routes_stay_absent(linked, case):
    """Honest emptiness is a behaviour worth pinning, not just a fallback."""
    payload = json.loads(
        _run(linked, "path", case["from"], case["to"], "--json", "--hops", str(case["hops"])).stdout
    )
    assert payload["paths"] == []


@pytest.mark.parametrize("case", load_pairs("neighbour"), ids=lambda c: c["doc"])
def test_explain_lists_the_expected_edges(linked, case):
    """Exactly these — a superset is as wrong as a subset."""
    payload = json.loads(_run(linked, "explain", case["doc"], "--json").stdout)
    assert {e["dst"] for e in payload["edges"]} == set(case["expect"])


@pytest.mark.parametrize("case", load_pairs("graph"), ids=lambda c: c["query"])
def test_graph_surfaces_the_expected_node(linked, case):
    payload = json.loads(_run(linked, "graph", case["query"], "--json").stdout)
    assert case["expect_node"] in {n["path"] for n in payload["nodes"]}


def test_relational_surfaces_are_deterministic(linked):
    """L3 at the surface: same corpus, same bytes, every run."""
    for args in (
        ("path", "docs/adr-storage.md", "docs/rota-oncall.md", "--json", "--hops", "2"),
        ("explain", "docs/adr-storage.md", "--json"),
        ("graph", "storage engine selection", "--json"),
    ):
        first = _run(linked, *args).stdout
        assert _run(linked, *args).stdout == first


def test_reliability_decays_with_distance(linked):
    """A two-hop route must be less reliable than a one-hop one."""
    def best(to: str) -> float:
        payload = json.loads(
            _run(linked, "path", "docs/adr-storage.md", to, "--json", "--hops", "2").stdout
        )
        return payload["paths"][0]["reliability"]

    assert best("docs/rota-oncall.md") < best("docs/runbook-rollback.md")


def test_the_graph_lane_does_not_move_ask(linked):
    """The load-bearing negative for M3.

    M3 adds verbs; it must not touch the ranking `ask` returns. The derived
    graph plane is built by the same `fux build` that builds the accelerator,
    so this is the assertion that catches a graph plane leaking into the
    lexical path.
    """
    for query in ("storage engine selection", "rollback", "catering"):
        scanned = _run(linked, "ask", query, "--json").stdout
        accelerated = _run(linked, "ask", query, "--json", "--fast").stdout
        assert accelerated == scanned


def test_graph_verbs_ask_for_a_build_rather_than_crashing(linked, tmp_path):
    """A repo with a committed index and no derived plane must say so."""
    proj = tmp_path / "unbuilt"
    shutil.copytree(linked, proj, ignore=shutil.ignore_patterns("runtime"))
    shutil.rmtree(proj / ".fux" / "runtime", ignore_errors=True)

    result = subprocess.run(
        [sys.executable, "-m", "fux.cli", "explain", "docs/adr-storage.md"],
        cwd=proj, capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "fux build" in result.stderr
    assert "Traceback" not in result.stderr
