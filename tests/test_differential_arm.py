"""The differential arm's own comparison rules, checked rather than asserted.

**Two premises stated in prose failed on the same day (2026-09-16), both of them
about what the arm compares and neither checked by anything.** This file is the
gate [SR-WORK-SESSION](../records/0060_WORK-session.md) decision 13 asks for when
a failure class is recorded twice.

1. `compose.mjs` and [SR-NODE-SEARCH](../records/0153_node-search.md) decision 17
   said Python always has a fresh graph plane *"on every corpus the differential
   arm runs on"*. `node-arm.yml` built no plane, so the arm ran red at 44 of 202
   and the workflow blamed a Node transcription defect. Closed by a build step.
2. `compare_verb` said `explain`, `graph` and `path` *"carry no score to
   tolerance"* — and every node of a `graph` payload carries a `score`. So it
   compared the graph lane to the score's LAST BIT while `_fields` beside it
   applied [SR-RANKING](../records/0111_ranking.md) decision 8a. That is what
   this file holds.

⚠ **The point is not that `round(…, 9)` is generous.** Decision 8a is Arpit's
ruling of 2026-09-06 and the arm already obeyed it in the ranking lane; the
defect was one lane being stricter than the engine's stated contract **by
accident**, which is how a green arm and a red arm can both be meaningless. What
the tests below pin is the half 8a licenses nothing about: **order, key names and
structure stay byte-equal**, and a difference above the contract still fails.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "differential"))

node_arm = pytest.importorskip("node_arm", reason="the differential harness is not importable here")
at_round9 = node_arm._scores_at_round9


#: The exact payload pair that went red in CI on 2026-09-16 — `graph
#: 'pii redaction'`, ubuntu-latest · node 20, run 35072100440. Same nodes, same
#: order, one `log` ulp apart. Kept verbatim so a future change to the rule has
#: to argue with the measurement rather than with a paraphrase of it.
CI_PYTHON = {"nodes": [
    {"id": "file:records/0148_pii.md", "path": "records/0148_pii.md",
     "role": "seed", "score": 12.264341482181356},
    {"id": "file:archive/open/W-102-enrich-pii.md", "path": "archive/open/W-102-enrich-pii.md",
     "role": "seed", "score": 11.780650569089822},
    {"id": "file:CHANGELOG.md", "path": "CHANGELOG.md",
     "role": "seed", "score": 11.56971104617382},
]}
CI_NODE = {"nodes": [
    {"id": "file:records/0148_pii.md", "path": "records/0148_pii.md",
     "role": "seed", "score": 12.264341482181356},
    {"id": "file:archive/open/W-102-enrich-pii.md", "path": "archive/open/W-102-enrich-pii.md",
     "role": "seed", "score": 11.780650569089824},   # <- the only difference
    {"id": "file:CHANGELOG.md", "path": "CHANGELOG.md",
     "role": "seed", "score": 11.56971104617382},
]}


def test_the_ci_divergence_is_inside_the_ruled_contract():
    """The measured failure, and the reason it is not a defect."""
    assert CI_PYTHON != CI_NODE, "fixture: the raw payloads must differ"
    assert at_round9(CI_PYTHON) == at_round9(CI_NODE)


def test_the_ci_divergence_is_orders_below_what_would_void_8a():
    """Decision 8a: *a divergence above ~1e-9 relative on any platform pair
    voids it*. This one is ~2e-16, which is the claim that licenses the rule."""
    py = CI_PYTHON["nodes"][1]["score"]
    nd = CI_NODE["nodes"][1]["score"]
    assert abs(py - nd) / abs(py) < 1e-12


def test_order_is_not_licensed_and_still_fails():
    """8a: *This licenses nothing about the ORDER, which stays byte-equal.*"""
    swapped = {"nodes": list(reversed(CI_PYTHON["nodes"]))}
    assert at_round9(CI_PYTHON) != at_round9(swapped)


def test_a_renamed_key_is_still_caught():
    """Whole-payload comparison exists so the two cannot drift on key names."""
    assert at_round9({"score": 1.0, "id": "a"}) != at_round9({"score": 1.0, "ident": "a"})


def test_a_difference_above_the_contract_still_fails():
    """`round(…, 9)` is a resolution, not an amnesty."""
    assert at_round9({"score": 1.000000001}) != at_round9({"score": 1.000000009})


def test_nothing_but_a_score_moves():
    """Only the value under a `score` key is rounded — never a float elsewhere,
    and never an int, which `round` would silently return unchanged anyway but
    which a future edit could turn into a float."""
    payload = {"score": 1.2345678901234, "weight": 1.2345678901234,
               "hops": 3, "label": "seed", "kids": [{"score": 2.9999999999}]}
    got = at_round9(payload)
    assert got["weight"] == 1.2345678901234, "a non-score float must not move"
    assert got["hops"] == 3
    assert got["label"] == "seed"
    assert got["score"] == round(1.2345678901234, 9)
    assert got["kids"][0]["score"] == round(2.9999999999, 9)


def test_compare_verb_actually_routes_through_the_rule():
    """The structural half: a future edit that drops the call from
    `compare_verb` puts the graph lane back on the score's last bit, and every
    test above would still pass."""
    import inspect

    src = inspect.getsource(node_arm.Arm.compare_verb)
    assert src.count("_scores_at_round9") == 2, (
        "compare_verb must pass BOTH readers' payloads through the SR-RANKING 8a "
        "rounding — comparing one rounded against one raw is worse than comparing "
        "neither, because it fails asymmetrically"
    )


# -- sharding (2026-09-29, the CI rewrite) -----------------------------------
#
# CI spreads one arm across several runners with `--shard K/N`. The property
# that makes that safe is that the N shards together are the unsharded run:
# nothing dropped, nothing doubled. A shard that silently ran nothing would be
# a green arm that checked nothing, so a malformed spec must refuse.


@pytest.mark.parametrize("n", [1, 2, 3, 4, 7])
def test_shards_partition_the_job_list_exactly(n):
    jobs = [("find", f"q{i}", top) for i in range(29) for top in (1, 5, 20)]
    shards = [jobs[k - 1::n] for k in range(1, n + 1)]
    flat = [j for s in shards for j in s]
    assert sorted(flat) == sorted(jobs)
    assert len(flat) == len(jobs)


@pytest.mark.parametrize("spec", ["0/3", "4/3", "x/3", "3", "1/0", ""])
def test_a_malformed_shard_refuses(spec):
    import argparse

    ap = argparse.ArgumentParser()
    with pytest.raises(SystemExit):
        node_arm._parse_shard(ap, spec)


def test_a_wellformed_shard_parses():
    import argparse

    assert node_arm._parse_shard(argparse.ArgumentParser(), "2/4") == (2, 4)
    assert node_arm._parse_shard(argparse.ArgumentParser(), None) is None


# -- W-259: the arm never lets Node read graph.json ---------------------------
#
# Fork A (Arpit, 2026-10-04): the Node reader reads `.fux/runtime/graph.json`
# when it is fresh. The arm runs where the plane IS fresh (`graph_lane_ready`
# demands it), so a Node child that took the read would compare Python's plane
# with itself and pass — N2 proving nothing, silently. Two halves, because
# either alone has a hole: the structural check catches a NEW spawn site that
# forgot `env=`, the runtime check catches a site whose `env` lacks the switch.
# The Node side — that the switch really skips the read in every verb — is
# `node/test/graph-read.test.mjs`.

import ast  # noqa: E402
import subprocess  # noqa: E402

DIFF = ROOT / "tools" / "differential"
SWITCH = node_arm.GRAPH_REBUILD_ENV


@pytest.mark.parametrize("arm", ["node_arm.py", "graph_arm.py"])
def test_every_spawn_in_the_arm_names_its_env(arm):
    """No child inherits the parent's environment by default — each says what it gets."""
    tree = ast.parse((DIFF / arm).read_text(encoding="utf-8"))
    runs = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        and n.func.attr == "run" and getattr(n.func.value, "id", None) == "subprocess"
    ]
    assert runs, f"{arm}: no subprocess.run found — the check is looking at the wrong file"
    bare = [n.lineno for n in runs if not any(k.arg == "env" for k in n.keywords)]
    assert not bare, f"{arm}: subprocess.run without env= at lines {bare} (W-259)"


def test_the_switch_reaches_every_node_child(monkeypatch, tmp_path):
    """Every Node process the arm starts carries `FUX_GRAPH_REBUILD=1`."""
    seen: list[tuple[list[str], dict | None]] = []

    def fake_run(argv, **kw):
        seen.append((list(argv), kw.get("env")))
        return subprocess.CompletedProcess(argv, 0, stdout="{}\n", stderr="")

    monkeypatch.setattr(node_arm.subprocess, "run", fake_run)
    monkeypatch.setattr(node_arm, "bundle_entry", lambda: tmp_path / "fux.mjs")
    arm = node_arm.Arm.__new__(node_arm.Arm)
    arm.root, arm.use_tune, arm.records, arm.max_headings = tmp_path, True, {}, 3

    calls = [{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}]
    for fn in (
        lambda: arm.node("find", "q", 5),
        lambda: arm.node("explain", "a.md", None),
        lambda: arm.compare_mcp(calls),
        lambda: arm.compare_api("q", "file:a.md", "file:b.md"),
        lambda: arm.compare_bundle("ask", "q", 5),
        lambda: arm.compare_bundle_api("q", "file:a.md", "file:b.md"),
        lambda: arm.compare_bundle_mcp(calls),
    ):
        try:
            fn()
        except Exception:  # the fake payloads compare as nothing; only the spawns matter
            pass

    node_children = [(argv, env) for argv, env in seen if argv and argv[0] == "node"]
    assert len(node_children) >= 9, f"too few Node spawns recorded ({len(node_children)}) — vacuous"
    missing = [argv[:3] for argv, env in node_children if (env or {}).get(SWITCH) != "1"]
    assert not missing, f"Node started without {SWITCH}=1: {missing}"


def test_graph_arm_starts_node_with_the_switch(monkeypatch, tmp_path):
    """N2 itself — `graph_arm.py` — on a one-shard corpus, with Node faked."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("_w259_graph_arm", DIFF / "graph_arm.py")
    graph_arm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(graph_arm)

    from fux.store import reader

    index = tmp_path / ".fux" / "index"
    index.mkdir(parents=True)
    shard = reader.iter_shard_paths(ROOT)[0]
    (index / shard.name).write_bytes(shard.read_bytes())

    seen = []

    def fake_run(argv, **kw):
        seen.append((list(argv), kw.get("env")))
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(graph_arm.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["graph_arm.py", str(tmp_path)])
    graph_arm.main()
    assert [argv[0] for argv, _ in seen] == ["node"]
    assert seen[0][1][SWITCH] == "1"
