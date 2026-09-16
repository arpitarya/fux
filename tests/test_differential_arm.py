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
