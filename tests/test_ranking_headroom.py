"""`ranking_headroom.py` — is a verdict arithmetically possible before it is attempted?

**Why this instrument exists, stated as the three runs that needed it.**

- **B1** measured `hit@5` at **240/240 in both arms at every tier** and filed a
  null: *"`pb` and `pc` are structurally zero and the null was determined by the
  corpus"*.
- **W-168 step 2** found improvement headroom of **3–4 of 33 against a floor of
  6** — *"step 2 cannot be given a verdict on this corpus whatever questions are
  written"*.
- **W-191** measured a link feature on a corpus with **0 `ref` edges**.

🔴 **In all three the arithmetic was available before the run**, and in all
three it was computed afterwards. [SR-RS](../records/0133_predictions.md)
decision 22 already required the disclosure; what was missing was somewhere to
get it from without running the arms first.

**The two properties under test:**

1. **The pool counts only what a RANKING change could win** — answerable
   questions whose primary is not already inside `k`. An unanswerable question
   is not headroom for a field weight; counting it would inflate the pool with
   questions no weight can win.
2. 🔴 **The bar comes from `resolution.smallest_detectable`, never from a
   literal here.** Decision 19's net RISES with the discordant count, and an
   instrument carrying its own copy of the table is the restatement
   [SR-LAW-0](../records/0002_LAW-0-authority.md) decision 1 forbids.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "quality-controls"))

import ranking_headroom as rh  # noqa: E402
from resolution import smallest_detectable  # noqa: E402


def _rows(hits: list[bool], rung="rung-01000", set_name="set-1") -> list[dict]:
    return [{"id": f"q{i:03d}", "rung": rung, "set": set_name, "hit@5": h}
            for i, h in enumerate(hits)]


def _key(ids, answerable=True) -> dict:
    return {i: {"id": i, "answerable": answerable} for i in ids}


# --- 1. the pool is what a ranking change can win ----------------------------

def test_the_pool_is_the_answerable_misses():
    rows = _rows([True, True, False, False, False])
    out = rh.headroom(rows, _key([r["id"] for r in rows]))
    assert len(out) == 1
    assert out[0]["n"] == 5 and out[0]["hit@5"] == 2 and out[0]["pool"] == 3


def test_an_unanswerable_question_is_not_headroom_for_a_ranking_change():
    """🔴 The right outcome on an unanswerable question is an abstention, which
    no field weight produces. Counting it would inflate the pool with questions
    the feature cannot win — and inflating the pool RAISES the bar, so this
    mistake is not even conservative."""
    rows = _rows([True, False, False])
    key = _key([r["id"] for r in rows])
    key["q002"]["answerable"] = False
    out = rh.headroom(rows, key)
    assert out[0]["n"] == 2, "the unanswerable row is out of the denominator too"
    assert out[0]["pool"] == 1


def test_a_question_with_no_expected_row_is_skipped_not_guessed():
    rows = _rows([False, False])
    out = rh.headroom(rows, _key(["q000"]))
    assert out[0]["n"] == 1 and out[0]["pool"] == 1


def test_rung_and_set_are_never_pooled():
    """The sets have different authors and the gap between them is the
    measurement; a headroom figure spanning them erases it."""
    rows = _rows([False, False], set_name="set-1") + _rows([True, True], set_name="set-2")
    out = rh.headroom(rows, _key([r["id"] for r in rows]))
    assert {(o["set"], o["pool"]) for o in out} == {("set-1", 2), ("set-2", 0)}


# --- 2. the bar is decision 19's, fetched and not copied ---------------------

@pytest.mark.parametrize("pool", [1, 2, 3, 4, 5, 6, 7, 12, 20, 30, 50])
def test_the_needed_net_is_resolutions_and_not_a_literal(pool):
    # ⚠ `pool == 0` is not parametrized here because an all-miss row list of
    # length 0 produces no bucket at all. The saturated case — a bucket that
    # EXISTS and whose pool is empty — is `test_a_saturated_bucket_...` below,
    # and it is the one that actually happened (B1).
    rows = _rows([False] * pool)
    out = rh.headroom(rows, _key([r["id"] for r in rows]))
    assert out[0]["net_needed"] == smallest_detectable(pool, rh.ALPHA)


def test_a_pool_too_small_for_any_net_cannot_produce_a_verdict():
    """🔴 W-168 step 2's shape: 3–4 questions of headroom against a floor of 6.
    Nets of 1–5 clear alpha at no discordant count, so a pool of 5 is a data
    defect (SR-RS 23b) and never a null."""
    for pool in (1, 2, 3, 4, 5):
        rows = _rows([False] * pool)
        out = rh.headroom(rows, _key([r["id"] for r in rows]))
        assert out[0]["verdict_possible"] is False
        assert out[0]["min_fix"] is None


def test_a_total_sweep_of_six_is_the_smallest_pool_that_can_ever_decide():
    rows = _rows([False] * 6)
    out = rh.headroom(rows, _key([r["id"] for r in rows]))
    assert out[0]["verdict_possible"] is True
    assert out[0]["min_fix"] == 6, "every one of the six, and no regressions"


def test_min_fix_assumes_zero_regressions_and_says_so():
    """⚠ With b wins and c losses, discordant = b + c and net = b - c, so the
    quoted `min_fix` is only reachable when c == 0. It is a ceiling on optimism
    — the docstring says so, and this pins the arithmetic behind it."""
    rows = _rows([False] * 12)
    out = rh.headroom(rows, _key([r["id"] for r in rows]))
    assert out[0]["min_fix"] == smallest_detectable(12, rh.ALPHA) == 8


def test_a_saturated_bucket_reports_an_empty_pool():
    """B1's shape — 240/240 in both arms. The instrument's whole job is to say
    this before the arms run rather than after."""
    rows = _rows([True] * 20)
    out = rh.headroom(rows, _key([r["id"] for r in rows]))
    assert out[0]["pool"] == 0
    assert out[0]["verdict_possible"] is False
    assert out[0]["net_needed"] is None


def test_it_applies_no_bar_of_its_own():
    """SR-RS decision 10b — a floor lives in a frozen pre-registration, never in
    an instrument. Nothing here decides pass or fail."""
    source = (ROOT / "tools" / "quality-controls" / "ranking_headroom.py").read_text(encoding="utf-8")
    code = [l for l in source.splitlines() if not l.lstrip().startswith("#")]
    for token in ("PASS", "FAIL", "clears_floor"):
        assert not any(token in l for l in code), f"{token} appears in the instrument"
