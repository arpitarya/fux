"""Every differential lane compares scores at SR-RANKING decision 8a's resolution.

**Two strikes, so a gate** ([SR-WORK-SESSION](../records/0060_WORK-session.md)
decision 13). The `graph` lane once compared raw floats and was fixed with
`node_arm._scores_at_round9`. On 2026-10-03 the `api` lane failed every OS x Node
cell on a 2-ulp difference in a graph-boosted score, which the ruling accepts:
Python and Node `Math.log` differ in the last bit, and no difference survives
`round(9)`, the sort key's own resolution.

The test drives `Arm.compare_api` with stubbed runtimes, so no index, Node or
corpus is involved. A last-bit difference must not count; a difference visible
at `round(9)` must.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE / "tools" / "differential"))

import node_arm  # noqa: E402


def _payload(score: float) -> dict:
    hit = {"id": "file:a.md", "loc": "a.md", "score": score, "archived": False}
    return {"ask": {"results": [hit]}, "find": [hit]}


def _compare(monkeypatch, py_score: float, node_score: float) -> list[str]:
    def fake_run(argv, **_kw):
        score = node_score if argv[0] == "node" else py_score
        return SimpleNamespace(returncode=0, stdout=json.dumps(_payload(score)) + "\n", stderr="")

    monkeypatch.setattr(node_arm.subprocess, "run", fake_run)
    arm = node_arm.Arm.__new__(node_arm.Arm)
    arm.root = ENGINE
    return arm.compare_api("q", "file:a.md", "file:b.md")


def test_a_last_bit_difference_is_not_a_discordance(monkeypatch):
    # The 2026-10-03 pair, exactly as CI printed it.
    assert _compare(monkeypatch, 6.532633949217505, 6.532633949217503) == []


def test_a_difference_visible_at_round9_still_is(monkeypatch):
    out = _compare(monkeypatch, 6.532633949, 6.532633948)
    assert out and all(line.startswith("api ") for line in out)
