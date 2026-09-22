"""W-212 — a hand-off carries SR-WORK-QUALITY's four gates, or it says it does not.

🔴 **This is a gate because it is the SECOND time a golden run was filed without
an input one of its own metrics acts on.** W-191 built a link feature and
measured it on a corpus with **0 `ref` edges**; W-204 phase D scored **11 716
rows** and could not compute
[SR-WORK-QUALITY](../records/0056_WORK-quality.md) decision 1's funnel, because
`reachable` and `in window` live in `ask --json --why`'s `derivation.gates` and
prompt 5 never passed `--why`. The counts were derived and discarded 11 716
times. [SR-WORK-SESSION](../records/0060_WORK-session.md) decision 13: a failure
class the WORKLOG records twice becomes a mechanical check in the same change as
the second occurrence.

**The two properties, and the second is the one that bites.**

1. A hand-off row built from a `--why` payload carries the five fields.
2. 🔴 **A row with no gates is `null`, never zeros.** `reachable: 0` is a claim —
   *this query reached no document* — and an arm that was never asked for its
   gates would file it for every question. A funnel of four zeros is
   indistinguishable from a total retrieval collapse, and it would be filed as
   one.

⚠ **The contract is spelled in four places and this test is what keeps them one
spelling:** the engine's own `Gates` dataclass, `golden_run.GATE_FIELDS`,
`rung_outputs.GATE_FIELDS` and `phase_d.GATE_FIELDS`. A rename in the engine that
reached none of the other three would produce hand-offs whose `gates` were
present, complete and entirely `None`.
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "quality-controls"))

import golden_run  # noqa: E402
import phase_d  # noqa: E402
import rung_outputs  # noqa: E402

from fux.query.provenance import Gates  # noqa: E402


WHY_PAYLOAD = {
    "results": [{"loc": "seed/01-sop.md"}, {"loc": "seed/02-thresholds.yaml"}],
    "confidence": {"band": "grounded", "answerable": True},
    "derivation": {
        "query": "dairy excursion",
        "path": "scan",
        "gates": {"reachable": 412, "in_window": 20, "placed": 5,
                  "answered": 1, "cut_score": 1.2044},
        # The per-term rows are deliberately NOT captured: the funnel needs five
        # integers and a hand-off that carried every document's attribution
        # would be orders of magnitude larger for nothing the metric reads.
        "documents": [{"id": "file:seed/01-sop.md", "matched": [], "missing": []}],
    },
}

NO_WHY_PAYLOAD = {
    "results": [{"loc": "seed/01-sop.md"}],
    "confidence": {"band": "weak", "answerable": False},
}


# --- the contract has one spelling ------------------------------------------

def test_the_engine_and_the_three_tools_name_the_same_five_fields():
    """A rename in `provenance.Gates` that reached none of the tools would give
    every row a complete, entirely-null `gates` block — present, and empty."""
    engine = tuple(f.name for f in dataclasses.fields(Gates))
    assert engine == golden_run.GATE_FIELDS
    assert golden_run.GATE_FIELDS == rung_outputs.GATE_FIELDS == phase_d.GATE_FIELDS


# --- 1. the row carries the five fields -------------------------------------

@pytest.fixture
def handoff(monkeypatch) -> dict:
    """One hand-off row, with `fux` stubbed. No corpus, no subprocess."""

    def fake_call(tree, *args, fux=None):
        if args[0] == "ask":
            assert "--why" in args, "the run must ask for the gates it files"
            return WHY_PAYLOAD, 4.0
        return {"answer": {"title": "t", "phrases": ["p"]}, "citation": {"loc": "seed/01-sop.md:L1-L2"}}, 5.0

    monkeypatch.setattr(golden_run, "call", fake_call)
    _, row = golden_run.one(Path("."), "rung-seed", "abc1234",
                            {"id": "s1-q001", "question": "dairy excursion"})
    return row


def test_the_handoff_carries_every_gate(handoff):
    assert set(handoff["gates"]) == set(golden_run.GATE_FIELDS)
    assert handoff["gates"] == {"reachable": 412, "in_window": 20, "placed": 5,
                                "answered": 1, "cut_score": 1.2044}


def test_the_handoff_does_not_carry_the_rest_of_the_derivation(handoff):
    """Five integers, not the per-term rows — W-212's own definition of done."""
    assert "derivation" not in handoff
    assert "documents" not in handoff["gates"]


# --- 2. absent is null, never zero ------------------------------------------

def test_a_run_without_why_files_null_gates_and_not_zeros(monkeypatch):
    """🔴 `fux-engine 1.0.0`'s `ask` has no `--why` — measured against the arm
    venv W-204 phase B ran — so this is the shape a three-engine re-run files for
    its v1 arm, on every question."""

    def fake_call(tree, *args, fux=None):
        if args[0] == "ask":
            assert "--why" not in args
            return NO_WHY_PAYLOAD, 4.0
        return {}, 5.0

    monkeypatch.setattr(golden_run, "call", fake_call)
    _, row = golden_run.one(Path("."), "rung-seed", "abc1234",
                            {"id": "s1-q001", "question": "dairy excursion"},
                            why=False)
    assert row["gates"] is None


def test_gates_of_a_payload_with_no_derivation_is_none():
    assert golden_run._gates(NO_WHY_PAYLOAD) is None
    assert golden_run._gates(None) is None
    assert golden_run._gates({"derivation": {"gates": "not a dict"}}) is None


# --- the per-rung document ---------------------------------------------------

def test_the_document_prints_the_funnel_when_it_exists():
    line = rung_outputs._funnel({"gates": WHY_PAYLOAD["derivation"]["gates"]})
    assert "reachable 412" in line and "in window 20" in line
    assert "placed 5" in line and "answered 1" in line
    assert "1.2044" in line


def test_the_document_says_not_captured_and_prints_no_zero():
    for row in ({}, {"gates": None},
                {"gates": dict.fromkeys(golden_run.GATE_FIELDS)}):
        line = rung_outputs._funnel(row)
        assert "not captured" in line
        assert "0" not in line.replace("`ask --why`", "")


def test_the_rung_document_banners_a_rung_with_no_gates():
    bare = {"id": "s1-q001", "question": "q", "ranked": [], "band": "weak",
            "answerable": False, "rung": "rung-seed", "engine_commit": "abc"}
    doc = rung_outputs.render("rung-seed", {1: [bare]}, fmt="fux.index.v4")
    assert "carry no funnel gates" in doc
    assert "cannot be computed for this rung" in doc


# --- phase D -----------------------------------------------------------------

def test_phase_d_computes_the_funnel_from_the_rows():
    gates = WHY_PAYLOAD["derivation"]["gates"]
    out = phase_d.funnel([{"gates": dict(gates)}, {"gates": dict(gates)}])
    assert out["computed"] is True
    assert out["reachable"] == 824 and out["in_window"] == 40
    assert out["placed"] == 10 and out["answered"] == 2
    assert out["cut_score_median"] == pytest.approx(1.2044)


def test_phase_d_refuses_to_report_a_funnel_of_zeros():
    """🔴 The property W-204 phase D's report had to state in prose instead."""
    out = phase_d.funnel([{"gates": None}, {}])
    assert out["computed"] is False
    assert out["rows_with_gates"] == 0 and out["n"] == 2
    assert "Absent is NOT zero" in out["reason"]
    assert all(field not in out for field in ("reachable", "in_window", "placed", "answered"))


def test_partial_coverage_is_reported_rather_than_averaged_away():
    out = phase_d.funnel([{"gates": dict(WHY_PAYLOAD["derivation"]["gates"])}, {"gates": None}])
    assert out["computed"] is True
    assert out["rows_with_gates"] == 1 and out["n"] == 2


def test_the_proxy_utility_names_itself_a_proxy():
    """Decision 6's `c = 2` is applied to `hit@5`, and the basis travels with it
    so no reader can take it for the judged utility decision 9 protects."""
    group = [{"said_unanswerable": False, "hit@5": True},
             {"said_unanswerable": False, "hit@5": False},
             {"said_unanswerable": True, "hit@5": False}]
    out = phase_d.utility_c2_retrieval_proxy(group)
    assert out["c"] == 2.0
    assert (out["correct"], out["wrong"], out["declined"]) == (1, 1, 1)
    assert out["utility"] == pytest.approx(-1.0)
    assert "NOT SR-WORK-QUALITY decision 6's utility" in out["basis"]
