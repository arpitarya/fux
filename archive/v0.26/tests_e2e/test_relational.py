"""Relational eval: the graph surfaces, measured (handoff 0004 M8).

Retrieval metrics (hit@k, MRR) are blind to `explain`, `graph` and `path` —
they score passages, and these verbs return relationships. `relational.jsonl`
is the instrument for those, run against a small linked corpus because the
main fixture has no links at all.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from conftest import E2E_DIR, run_fux

PAIRS = E2E_DIR / "eval" / "relational.jsonl"
CORPUS = E2E_DIR / "eval" / "relational"


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
    (proj / "fux.toml").write_text('[sources]\ndocs = ["docs"]\n', encoding="utf-8")
    run_fux(proj, "ingest")
    return proj


@pytest.mark.parametrize("case", load_pairs("path"), ids=lambda c: f"{c['from']}->{c['to']}")
def test_expected_paths_are_found(linked, case):
    payload = json.loads(
        run_fux(
            linked, "path", case["from"], case["to"], "--json", "--hops", str(case["hops"])
        ).stdout
    )
    assert payload["paths"], f"no route {case['from']} → {case['to']}"
    best = payload["paths"][0]
    assert best["hops"][0]["kind"] == case["expect"]
    assert best["hops"][-1]["dst"] == case["to"]
    assert 0 < best["reliability"] <= 1.0


@pytest.mark.parametrize("case", load_pairs("nopath"), ids=lambda c: f"{c['from']}-x-{c['to']}")
def test_absent_routes_stay_absent(linked, case):
    """Honest emptiness is a behaviour worth pinning, not just a fallback."""
    payload = json.loads(
        run_fux(
            linked, "path", case["from"], case["to"], "--json", "--hops", str(case["hops"])
        ).stdout
    )
    assert payload["paths"] == []


@pytest.mark.parametrize("case", load_pairs("neighbour"), ids=lambda c: c["doc"])
def test_explain_lists_the_expected_edges(linked, case):
    payload = json.loads(run_fux(linked, "explain", case["doc"], "--json").stdout)
    found = {e["dst"] for e in payload["edges"]}
    assert found == set(case["expect"]), f"edges for {case['doc']}"


@pytest.mark.parametrize("case", load_pairs("graph"), ids=lambda c: c["query"])
def test_graph_surfaces_the_expected_node(linked, case):
    payload = json.loads(run_fux(linked, "graph", case["query"], "--json").stdout)
    assert case["expect_node"] in {n["path"] for n in payload["nodes"]}


def test_relational_surfaces_are_deterministic(linked):
    for args in (
        ("path", "docs/adr-storage.md", "docs/rota-oncall.md", "--json", "--hops", "2"),
        ("explain", "docs/adr-storage.md", "--json"),
        ("graph", "storage engine selection", "--json"),
    ):
        first = run_fux(linked, *args).stdout
        assert run_fux(linked, *args).stdout == first


def test_reliability_decays_with_distance(linked):
    """A two-hop route must be less reliable than a one-hop one."""
    one = json.loads(
        run_fux(
            linked, "path", "docs/adr-storage.md", "docs/runbook-rollback.md",
            "--json", "--hops", "2",
        ).stdout
    )["paths"][0]["reliability"]
    two = json.loads(
        run_fux(
            linked, "path", "docs/adr-storage.md", "docs/rota-oncall.md",
            "--json", "--hops", "2",
        ).stdout
    )["paths"][0]["reliability"]
    assert two < one
