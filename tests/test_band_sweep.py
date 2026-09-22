"""W-213's instrument — the replay reproduces the engine, and the bar is SR-RS's.

**Three properties, and each guards a different way a threshold sweep goes
wrong.**

1. 🔴 **The replay is the ENGINE's band rule, not a copy of it.** `band_sweep`
   reconstructs `fux.query.confidence.Confidence` from a captured block and
   varies one field. If it reimplemented the rule instead, the tool and the
   engine could disagree while both looked correct — and the disagreement would
   be read as a result, which is the restatement
   [SR-LAW-0](../records/0002_LAW-0-authority.md) decision 1 forbids by its own
   test.
2. **The cost model is SR-WORK-QUALITY decision 6's and is not chosen here.**
   `+1` correct, `0` declined, `−2` wrong, at the published `t = 0.75` → `c = 2`.
   A sweep that could pick its own weight would be choosing its answer.
3. 🔴 **The paired bar is NOT IN THIS TOOL.** It is
   [`verdict.py`](../tools/quality-controls/verdict.py)'s, the one seam that
   adjudicates a paired result — *"so no control can hard-code a bar again"*,
   after three instruments landed on 2026-09-12 each about to write `net >= 6`.
   [SR-RS](../records/0133_predictions.md) decision 19's real bar **rises with
   the flips**: a net of 8 on 30 discordant pairs clears 6 and fails the table.
   The tests below assert the delegation **and** the two properties the
   delegation must preserve.

⚠ **Nothing here runs `fux` and nothing here reads a corpus.** The capture is a
subprocess loop; what is worth testing is the arithmetic that turns it into a
decision.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "quality-controls"))

import band_sweep as bs  # noqa: E402

from fux.query.confidence import Confidence, SEPARATION_FLOOR  # noqa: E402


def block(separation: float, **over) -> dict:
    """A confidence block exactly as `Confidence.as_dict()` emits one."""
    base = Confidence(
        coverage=over.pop("coverage", 1.0),
        separation=separation,
        support=over.pop("support", 10),
        verified=over.pop("verified", "unverified"),
        missing=tuple(over.pop("missing", ())),
        doc_coverage=over.pop("doc_coverage", 1.0),
        doc_coverage_floor=over.pop("doc_coverage_floor", 0.0),
    )
    assert not over, over
    return base.as_dict()


# --- 1. the replay is the engine --------------------------------------------

def test_the_incumbent_floor_replays_to_what_the_engine_said():
    """The self-check the sweep runs on every row, asserted directly: rebuilding
    the block at the floor it was judged under must return the same verdict.

    ⚠ **On the BAND, since W-214.** `answerable` stopped being a function of
    the band the sweep varies (Arpit, 2026-09-22 — `weak` is a signal), so a
    capture taken after that ruling would fail an `answerable` comparison for a
    reason that is not an instrument fault. The band means the same thing on
    both sides of the ruling, which is why it is the thing compared.
    """
    for separation in (0.0, 0.05, 0.0999, 0.1, 0.1001, 0.5, 1.0):
        emitted = block(separation)
        assert bs.replay(emitted, SEPARATION_FLOOR).band == emitted["band"]


def test_the_incumbent_in_the_grid_is_the_engine_default():
    """🔴 If the engine's default moves and this constant does not, every
    comparison in the sweep is against a floor nothing ships."""
    assert bs.INCUMBENT == SEPARATION_FLOOR
    assert bs.INCUMBENT in bs.GRID


def test_lowering_the_floor_can_only_turn_abstentions_into_answers():
    """The mechanism, stated as a monotonicity: the `separation` clause is a
    one-sided threshold, so no question moves the other way."""
    emitted = block(0.06)
    assert bs.withheld_under_the_separation_gate(bs.replay(emitted, 0.10)) is True
    assert bs.withheld_under_the_separation_gate(bs.replay(emitted, 0.05)) is False
    assert bs.withheld_under_the_separation_gate(bs.replay(emitted, 0.00)) is False


def test_the_withholding_rule_is_the_PRE_W214_one_and_says_so():
    """🔴 **The one place this tool does not defer to the engine, pinned.**

    W-213's result is what retired the rule it measured: Arpit ruled on
    2026-09-22 (W-214) that `weak` is a signal, so the engine's `answerable` is
    `band != none` now. Reading `conf.answerable` here would report every row
    as answered and every sweep as a no-op — a filed instrument quietly
    measuring nothing.

    So the pre-W-214 rule lives in one named function, and this test is what
    stops it being "simplified" back to the engine's property by someone who
    notices the duplication without noticing the date.
    """
    weak = bs.replay(block(0.06), 0.10)
    assert weak.band == "weak"
    assert weak.answerable is True, "the ENGINE answers — W-214"
    assert bs.withheld_under_the_separation_gate(weak) is True, "the 2026-09-22 rule"


def test_a_partial_band_is_untouched_by_the_floor():
    """⚠ `partial` was never withheld and the separation clause never runs for
    it — a missing term is a NAMEABLE defect. A sweep that moved these would be
    attributing to the floor what `missing` decided."""
    emitted = block(0.0, missing=("mesh",))
    assert emitted["band"] == "partial"
    for floor in bs.GRID:
        assert bs.withheld_under_the_separation_gate(bs.replay(emitted, floor)) is False


def test_nothing_scored_stays_unanswerable_at_every_floor():
    """The one refusal that survives W-214, and it is the engine's own."""
    emitted = block(0.0, support=0)
    assert emitted["band"] == "none"
    for floor in bs.GRID:
        assert bs.withheld_under_the_separation_gate(bs.replay(emitted, floor)) is True
        assert bs.replay(emitted, floor).answerable is False


# --- 2. the cost model is decision 6's --------------------------------------

def test_the_published_cost_model():
    assert bs.COST_C == 2.0, "SR-WORK-QUALITY decision 6: t = 0.75 -> c = 2"
    assert bs.utility(answered=True, quoted=True) == 1.0
    assert bs.utility(answered=True, quoted=False) == -2.0
    assert bs.utility(answered=False, quoted=True) == 0.0
    assert bs.utility(answered=False, quoted=False) == 0.0


def test_abstention_is_never_worse_than_a_wrong_answer_and_never_better_than_a_right_one():
    """The ordering is the whole point of pricing an error: a sweep whose
    endpoint ranked declining above answering correctly would have a trivial
    optimum in the other direction."""
    assert bs.utility(True, False) < bs.utility(False, False) < bs.utility(True, True)


# --- 3. the bar is SR-RS decision 19's --------------------------------------

def test_the_sweep_adjudicates_through_verdict_and_not_through_its_own_if():
    """🔴 The property the quality-controls README states in terms: *the one
    place a paired result is adjudicated, so no control can hard-code a bar
    again*. If this tool grows its own comparison, this test goes red."""
    import verdict

    assert bs.rule is verdict.rule
    assert bs.ALPHA == verdict.ALPHA == 0.05
    assert bs.FLOOR_OF_ALL_FLOORS == 6
    # ⚠ Comments may DISCUSS the floor — this file's whole point is that the
    # floor lives elsewhere, and saying so is how the next reader learns it.
    # What is refused is the floor being APPLIED here, so comment lines are
    # stripped before the check rather than the check being softened.
    code = [line for line in
            (ROOT / "tools" / "quality-controls" / "band_sweep.py")
            .read_text(encoding="utf-8").splitlines()
            if not line.lstrip().startswith("#")]
    for line in code:
        assert ">= 6" not in line and ">= FLOOR" not in line, (
            f"band_sweep.py re-applies the floor itself — verdict.py is the seam: {line!r}"
        )


@pytest.mark.parametrize("net", [1, 2, 3, 4, 5])
def test_a_net_below_six_clears_at_no_discordant_count(net):
    """🔴 The floor of all floors, exhausted rather than asserted — the sentence
    that decides more filed claims than the table does. Asserted through the
    adjudicator the sweep actually calls."""
    for c in range(0, 51):
        outcome = bs.rule(c + net, c)["outcome"]
        assert outcome in ("inconclusive", "no detected change"), \
            f"net {net} cleared at b={c + net}, c={c}"


def test_the_bar_rises_with_the_flips():
    """The failure `verdict.py` was built for: a net of 8 passes *net >= 6* and
    **fails** decision 19's table at 30 discordant pairs."""
    assert bs.rule(19, 11)["net"] == 8 and bs.rule(19, 11)["discordant"] == 30
    assert bs.rule(19, 11)["outcome"] == "no detected change"
    assert bs.rule(19, 11)["net_needed"] == 12


@pytest.mark.parametrize("discordant,net", [(6, 6), (8, 8), (12, 8), (15, 9), (20, 10), (30, 12), (50, 16)])
def test_decision_19s_table_reproduces(discordant, net):
    """Each row of SR-RS decision 19: that net clears at that count, and the
    next smaller net at the same count does not."""
    b = (discordant + net) // 2
    c = discordant - b
    assert b - c == net and b + c == discordant
    assert bs.rule(b, c)["net_needed"] == net
    assert bs.rule(b, c)["outcome"] == "b"
    assert bs.rule(b - 1, c + 1)["outcome"] == "no detected change"


def test_a_regression_is_adjudicated_exactly_as_an_improvement_is():
    """🔴 The bar is on the magnitude, never the direction. A pre-registration
    states both directions, and an instrument that could only detect the one it
    hoped for would be the moving threshold decision 10b forbids."""
    assert bs.rule(9, 1, better="candidate-better", worse="incumbent-better")["outcome"] \
        == "candidate-better"
    assert bs.rule(1, 9, better="candidate-better", worse="incumbent-better")["outcome"] \
        == "incumbent-better"


def test_the_outcome_label_names_neither_direction_of_the_grid():
    """🔴 The grid runs both ways around the incumbent, so a label like
    `lower-floor-better` reads BACKWARDS on every candidate above it. The sweep
    labels the arm, never the direction."""
    code = [line for line in
            (ROOT / "tools" / "quality-controls" / "band_sweep.py")
            .read_text(encoding="utf-8").splitlines()
            if not line.lstrip().startswith("#")]
    assert any('better="candidate-better"' in line for line in code)
    # The comment above the call may NAME the rejected label — that is how the
    # next reader learns why it is rejected. No line of code may USE it.
    assert not any("lower-floor-better" in line for line in code)


def test_no_flips_is_inconclusive_and_never_no_change():
    """SR-RS decision 22d — a null measured where nothing could move is the
    absence of a measurement, not a result."""
    assert bs.rule(0, 0)["outcome"] == "inconclusive"
