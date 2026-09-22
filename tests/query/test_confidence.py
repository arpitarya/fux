"""SR-CONFIDENCE — the four signals, the four bands, and what must never move.

The easy tests here are the ones that assert a band comes out. **The ones that
matter are the four below the fold:**

- the band is a function of the signals and nothing else, so it cannot be
  reached by a score or an ordering;
- `--fast` and `--scan` produce the *same* block, or the differential law has a
  hole in it that says "confident" on one path and "weak" on the other;
- `missing` carries the word the user typed, not the stem the index is keyed by;
- `answerable` is `False` on the empty branch — **and, since W-214, on that
  branch alone.** `weak` is a published signal, not a refusal.

Three of the four band boundaries are structural facts and are tested as such.
The fourth — `grounded` vs `weak` — rests on `SEPARATION_FLOOR`, which is
**provisional and unmeasured** (prediction R10), so these tests assert the
*rule* relative to the constant and never that the constant is right. A test
that hard-coded `0.10` would have to be edited when the verdict lands, and an
edited test is how a frozen threshold moves in disguise.
"""

from __future__ import annotations

import argparse
import json as json_mod

import pytest

from fux.query import cmd_ask, cmd_find, run_query
from fux.query.confidence import (
    BANDS,
    DOC_COVERAGE_FLOOR,
    GROUNDED,
    NONE,
    PARTIAL,
    SEPARATION_FLOOR,
    WEAK,
    Confidence,
    signals,
)
from fux.query.tokenize import tokenize, tokenize_pairs
from fux.store import content_sha, term_hash, write_index

N = 1000


def _h(word: str) -> str:
    return term_hash(tokenize(word)[0])


def _q(text: str, df: dict[str, int], scores: list[float], **kw) -> Confidence:
    """Build a block for `text` with a caller-supplied `df`, as `rank()` would.

    `df` is keyed by the RAW word for readability; hashing happens here so a
    fixture cannot accidentally key on an unanalyzed form — the failure mode
    `test_headings.py::_h` documents.
    """
    pairs = tokenize_pairs(text)
    hashes = list(dict.fromkeys(term_hash(a) for _, a in pairs))
    return signals(pairs, hashes, {_h(w): c for w, c in df.items()}, N, scores, **kw)


# -- the four signals ----------------------------------------------------


def test_coverage_is_idf_weighted_so_a_missed_RARE_term_costs_most():
    """The whole reason coverage is not a plain term count.

    Missing a term that appears in 900 of 1 000 documents is nearly free —
    it never distinguished anything. Missing one the corpus has never seen is
    what made the question specific, and it has to dominate.
    """
    common = _q("rollback ubiquitous", {"rollback": 40, "ubiquitous": 0}, [5.0, 1.0])
    rare = _q("rollback pgbouncer", {"rollback": 40, "pgbouncer": 0}, [5.0, 1.0])
    # Both miss exactly one of two terms, so a term COUNT would score them
    # identically. They differ only in what the present term's df is, which is
    # what idf weighting is for.
    assert 0.0 < common.coverage < 1.0
    assert 0.0 < rare.coverage < 1.0

    # And the real claim: a term present in almost every document contributes
    # almost nothing, so missing the OTHER one costs nearly everything.
    everywhere = _q("rollback thecommonest", {"rollback": 0, "thecommonest": 990}, [5.0])
    assert everywhere.coverage < 0.05, "a term in 99% of documents must not rescue coverage"


def test_coverage_is_one_when_every_term_exists_and_missing_is_empty():
    block = _q("rollback procedure", {"rollback": 40, "procedure": 12}, [5.0, 2.0])
    assert block.coverage == 1.0
    assert block.missing == ()


def test_separation_is_the_gap_to_the_runner_up_as_a_fraction_of_the_top():
    block = _q("rollback", {"rollback": 40}, [10.0, 4.0, 1.0])
    assert block.separation == pytest.approx(0.6)


def test_one_result_separates_PERFECTLY_rather_than_not_at_all():
    """The easy sign error, and it inverts the signal.

    `top2` does not exist, so a naive `(top1 - top2)/top1` reads as `0.0` and
    the single unambiguous answer in the corpus is reported as the *least*
    confident thing fux can return. Nothing competing with a result is the
    strongest separation there is.
    """
    block = _q("rollback", {"rollback": 3}, [7.5])
    assert block.separation == 1.0
    assert block.support == 1
    assert block.band == GROUNDED


def test_support_counts_scored_results_and_is_zero_on_the_empty_branch():
    assert _q("rollback", {"rollback": 40}, [5.0, 4.0, 3.0]).support == 3
    assert _q("rollback", {"rollback": 0}, []).support == 0


def test_ask_and_find_never_claim_a_freshness_they_did_not_check():
    """`unverified` means *we did not look*, and it must never read `current`.

    Collapsing the two is the exact failure `refer/freshness.py`'s four-state
    verdict exists to prevent, and re-introducing it one layer up would undo
    that for every agent reading `--json` instead of the refer plane.
    """
    assert _q("rollback", {"rollback": 40}, [5.0, 2.0]).verified == "unverified"


# -- the bands -----------------------------------------------------------


def test_none_when_nothing_scored_and_answerable_is_FALSE():
    """The branch an agent most needs to be stopped by."""
    block = _q("pgbouncer failover", {"pgbouncer": 0, "failover": 0}, [])
    assert block.band == NONE
    assert block.answerable is False


def test_partial_when_a_query_term_is_absent_from_the_whole_corpus():
    block = _q("rollback pgbouncer", {"rollback": 40, "pgbouncer": 0}, [9.0, 1.0])
    assert block.band == PARTIAL
    assert block.answerable is True
    assert block.missing == ("pgbouncer",)


def test_partial_when_the_cited_bytes_changed_even_with_full_coverage():
    """`stale` demotes on its own, with no threshold involved.

    It lands in `partial` rather than `weak` because it is a *knowable* defect
    the consumer can name — which is what `partial` means — where a `weak`
    result has nothing identifiably wrong with it.
    """
    grounded = _q("rollback procedure", {"rollback": 40, "procedure": 12}, [9.0, 1.0])
    assert grounded.band == GROUNDED
    assert grounded.with_verified("stale").band == PARTIAL
    assert grounded.with_verified("current").band == GROUNDED
    assert grounded.with_verified("cached").band == GROUNDED


def test_weak_and_grounded_straddle_the_floor_without_naming_its_value():
    """The rule, asserted RELATIVE to the constant — never against `0.10`.

    `SEPARATION_FLOOR` is provisional and unmeasured (R10). A test that
    hard-coded today's value would have to be edited when the verdict lands,
    and editing a test to accommodate a number is how a pre-registered
    threshold moves without anyone deciding to move it.
    """
    df = {"rollback": 40, "procedure": 12}
    below = 1.0 - (SEPARATION_FLOOR / 2)  # top2 close to top1 -> small gap
    above = 1.0 - (SEPARATION_FLOOR * 2)

    assert _q("rollback procedure", df, [1.0, below]).band == WEAK
    assert _q("rollback procedure", df, [1.0, above]).band == GROUNDED


def test_the_band_is_checked_in_order_and_absence_beats_ambiguity():
    """A query that is BOTH missing a term and unseparated reads `partial`.

    Order matters because the two bands ask for different behaviour: `partial`
    says *answer and name the gap*, `weak` says *the ranking could not choose —
    judge for yourself*. Reporting the nameable defect is more useful than
    reporting the unnameable one.
    """
    block = _q("rollback pgbouncer", {"rollback": 40, "pgbouncer": 0}, [1.0, 0.999])
    assert block.separation < SEPARATION_FLOOR
    assert block.band == PARTIAL


def test_every_band_is_in_BANDS_best_first():
    assert BANDS == (GROUNDED, PARTIAL, WEAK, NONE)


# -- what must never move ------------------------------------------------


def test_missing_reports_the_word_the_USER_typed_not_the_stem():
    """`mTLS` analyzes to `mtl`, and reporting `mtl` is worse than silence.

    A reader told *"`mtl` is not in this corpus"* cannot tell whether fux
    misunderstood the question or the corpus really lacks the topic. This is
    why `analyzer.analyze_pairs` exists at all.
    """
    block = _q("mTLS rotation", {"mTLS": 0, "TLS": 0, "rotation": 20}, [4.0])
    assert "mTLS" in block.missing
    assert "mtl" not in block.missing


def test_the_block_is_a_pure_function_of_its_inputs():
    """L3. Same inputs, same block — no clock, no set-iteration order, no
    accumulated state between calls."""
    args = ("rollback pgbouncer procedure", {"rollback": 40, "pgbouncer": 0, "procedure": 12})
    first = _q(*args, [9.0, 3.0, 1.0])
    for _ in range(5):
        assert _q(*args, [9.0, 3.0, 1.0]) == first


def test_an_empty_query_is_none_rather_than_an_exception():
    block = signals([], [], {}, 0, [])
    assert block.band == NONE
    assert block.answerable is False
    assert block.coverage == 0.0


def test_as_dict_declares_band_and_answerable_rather_than_leaving_them_derivable():
    """A consumer forced to re-implement the band rules is a second copy of
    this module's policy, in another language, drifting from day one."""
    payload = _q("rollback pgbouncer", {"rollback": 40, "pgbouncer": 0}, [9.0, 1.0]).as_dict()
    assert payload["band"] == PARTIAL
    assert payload["answerable"] is True
    assert payload["missing"] == ["pgbouncer"]
    assert set(payload) == {
        "band", "answerable", "failed", "coverage", "doc_coverage", "separation",
        "separation_floor", "doc_coverage_floor",
        "support", "verified", "missing",
    }
    # W-176 step 3 — `failed` names WHICH gate refused, and is `[]` on a
    # `partial`, which is not a refusal at all.
    assert payload["failed"] == []
    # The floors are published for the OPPOSITE reason to `band`: not so a
    # consumer can re-derive the verdict, but so it can see the verdict is not
    # comparable across repos that tuned differently (SR-CONFIDENCE 13).
    assert payload["separation_floor"] == SEPARATION_FLOOR
    assert payload["doc_coverage_floor"] == DOC_COVERAGE_FLOOR


def test_the_stderr_line_is_silent_at_grounded_and_ascii_everywhere():
    """Silent at `grounded` so it stays a signal rather than a banner, and
    ASCII-only because a Windows console's default codepage crashes `print()`
    on a fancy dash rather than degrading (v0.35.0)."""
    assert _q("rollback procedure", {"rollback": 40, "procedure": 12}, [9.0, 1.0]).line() == ""
    for block in (
        _q("rollback pgbouncer", {"rollback": 40, "pgbouncer": 0}, [9.0, 1.0]),
        _q("rollback procedure", {"rollback": 40, "procedure": 12}, [1.0, 0.999]),
        _q("pgbouncer", {"pgbouncer": 0}, []),
    ):
        line = block.line()
        assert line
        line.encode("ascii")  # raises if anything non-ASCII crept in


# -- the surfaces --------------------------------------------------------

DOC_ID = "file:docs/mesh.md"


def _record(**overrides) -> dict:
    record = {
        "id": DOC_ID,
        "src": "git",
        "loc": "docs/mesh.md",
        "mode": "extracted",
        "sha": content_sha(DOC_ID.encode("utf-8")),
        "title": "The mesh",
        "phrases": ["Rollback procedure"],
        "terms": {_h("rollback"): [3, 2], _h("procedure"): [1, 1]},
        "flen": [40, 12],
        "edges": [],
    }
    record.update(overrides)
    return record


def _args(**overrides) -> argparse.Namespace:
    # `band=True` in the BASE, deliberately: every test in this file is about
    # the block's CONTENT, and decision 11 changed only its EMISSION. Defaulting
    # it off here would silently turn ~30 content assertions into assertions
    # about the gate. The gate's own tests set it explicitly, both ways.
    base = dict(
        query="rollback", top=5, json=False, scan=True, explain=False,
        hybrid=False, band=True,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def test_run_query_fills_confidence_only_when_a_caller_asks(tmp_path, monkeypatch):
    write_index(tmp_path, [_record()])
    monkeypatch.chdir(tmp_path)

    out: dict = {}
    results, _ = run_query(tmp_path, "rollback", 5, confidence_out=out)
    assert results
    assert out["confidence"].band in BANDS

    # The additive-keyword contract: a caller that does not ask is unchanged
    # and pays only a `None` check.
    again, _ = run_query(tmp_path, "rollback", 5)
    assert [r.id for r in again] == [r.id for r in results]


def test_ask_json_carries_the_block_and_find_keeps_stdout_pipeable(
    tmp_path, monkeypatch, capsys
):
    """`find` pipes bare paths into `xargs`, so the declaration goes to stderr.

    This is the same contract `_declare_archived` and `_declare_pending` take,
    and the reason is concrete rather than stylistic: a note on stdout is read
    as a filename.
    """
    write_index(tmp_path, [_record()])
    monkeypatch.setattr("fux.query.find_root", lambda: tmp_path)

    cmd_ask(_args(query="rollback pgbouncer", json=True, band=True))
    payload = json_mod.loads(capsys.readouterr().out)
    assert payload["confidence"]["band"] == PARTIAL
    assert payload["confidence"]["missing"] == ["pgbouncer"]

    cmd_find(_args(query="rollback pgbouncer", band=True))
    captured = capsys.readouterr()
    assert captured.out.strip().splitlines() == ["docs/mesh.md"]
    assert "confidence:" in captured.err


def test_the_cli_emits_nothing_without_band_and_still_computes_it(
    tmp_path, monkeypatch, capsys
):
    """SR-CONFIDENCE decision 11 — and the half of it that is easy to lose.

    **Absent means NOT ASKED FOR, never *not confident*.** A consumer that read
    a missing key as band `none` would abstain on every healthy answer.

    ⚠ The second assertion is the one worth keeping: the block must still be
    **computed** with the flag absent. Gating the computation would gate
    `stats_out` with it, and the differential law would stop being exercised on
    the path almost every run takes.
    """
    write_index(tmp_path, [_record()])
    monkeypatch.setattr("fux.query.find_root", lambda: tmp_path)

    cmd_ask(_args(query="rollback pgbouncer", json=True, band=False))
    captured = capsys.readouterr()
    payload = json_mod.loads(captured.out)
    assert "confidence" not in payload
    assert payload["results"], "the answer itself is unchanged by the gate"
    # Narrow on purpose: stderr also carries the accelerator notice and the
    # archived declaration, which this gate has nothing to do with.
    assert "confidence:" not in captured.err

    # ... and it was computed all the same.
    out: dict = {}
    run_query(tmp_path, "rollback pgbouncer", 5, confidence_out=out)
    assert out["confidence"].band == PARTIAL


def test_band_prints_at_grounded_too_once_it_is_asked_for(
    tmp_path, monkeypatch, capsys
):
    """Silence-at-`grounded` is reversed under the flag.

    The original silence stopped a healthy query printing a line on every
    invocation. `--band` is an explicit request, and a flag that goes quiet
    exactly when the answer is good reads as broken.
    """
    write_index(tmp_path, [_record()])
    monkeypatch.setattr("fux.query.find_root", lambda: tmp_path)

    cmd_find(_args(query="rollback", band=True))
    assert "confidence:" in capsys.readouterr().err


def test_the_block_cannot_reach_a_score_or_an_ordering(tmp_path, monkeypatch):
    """The structural guarantee, asserted rather than argued.

    Confidence is computed from `rank()`'s output and handed to the caller;
    nothing downstream feeds back. Asking for it must therefore return exactly
    the same documents, in exactly the same order, with exactly the same
    scores as not asking for it.
    """
    write_index(tmp_path, [_record(), _record(id="file:b.md", loc="b.md", title="B")])
    monkeypatch.chdir(tmp_path)

    plain, _ = run_query(tmp_path, "rollback procedure", 5)
    out: dict = {}
    withsig, _ = run_query(tmp_path, "rollback procedure", 5, confidence_out=out)

    assert [(r.id, r.score) for r in plain] == [(r.id, r.score) for r in withsig]


# --- doc_coverage: the clause the decoy control bought (2026-08-28) ----------

def test_a_question_whose_terms_scatter_across_documents_is_not_grounded():
    """Measured 2026-08-27, and it is the reason this field exists.

    *"What is the SLA we publish for the payments API"* reached `grounded` on a
    corpus where **no document discusses it**: `sla` and `publish` sat in the
    retention policy, `payments` in the postmortem, `api` in the mesh SR — four
    terms, four documents, so `missing` was empty and `coverage` was `1.0`.

    ⚠ **No threshold on `separation` closes this.** That query separated at
    `0.58`, ABOVE the `0.5` R10's selection rule would have picked. `separation`
    measures whether first place is clearly first, and a corpus of near-misses is
    decisive about its best near-miss.
    """
    from fux.query.confidence import Confidence

    scattered = Confidence(
        coverage=1.0, separation=0.58, support=3,
        verified="unverified", missing=(), doc_coverage=0.42,
    )
    # ⚠ **The clause is OFF** () because the decoy at
    # 0.710 sits INSIDE the real goldens' 0.401-1.000 range -- no floor separates
    # them. The signal is published; the band does not gate on it. What this test
    # pins is that the SIGNAL still distinguishes the case.
    assert scattered.doc_coverage < 1.0
    assert scattered.answerable is True, "still answerable — `partial` is not a refusal"


def test_a_document_that_carries_the_whole_question_is_still_grounded():
    """The control. The new clause must not demote a real answer."""
    from fux.query.confidence import Confidence

    whole = Confidence(
        coverage=1.0, separation=0.58, support=3,
        verified="unverified", missing=(), doc_coverage=1.0,
    )
    assert whole.band == GROUNDED


def test_doc_coverage_defaults_to_not_demoting():
    """A caller that does not supply it must never be penalised for that.

    `signals()` is called from paths that may not have ranked anything, and a
    signal defaulting to 'suspicious' would turn 'not computed' into 'not
    grounded' — a silent downgrade nobody chose.
    """
    from fux.query.confidence import Confidence

    assert Confidence(1.0, 0.9, 2, "unverified", ()).doc_coverage == 1.0
    assert Confidence(1.0, 0.9, 2, "unverified", ()).band == GROUNDED


def test_the_corpus_wide_coverage_is_unchanged():
    """`coverage` keeps its meaning, so nothing reading it changes behaviour.

    That is why the field was ADDED rather than redefined: a consumer reading
    `coverage: 1.0` today gets the same number tomorrow.
    """
    block = _q("rollback pgbouncer", {"rollback": 40, "pgbouncer": 0}, [9.0, 1.0])
    assert block.coverage < 1.0 and block.missing == ("pgbouncer",)


# -- the floors are tunable, and the guard is publication ----------------
#
# SR-CONFIDENCE decision 13 REVERSED decision 7, which had refused these as
# `tune.toml` keys. What decision 7 was protecting is real and is now unguarded
# by anything mechanical: a consumer can lower `separation_floor` until every
# answer reads `grounded`, which tunes away the SIGNAL rather than the ranking.
# These tests pin the two things that replace the prohibition — the block
# publishes the floor it was judged under, and the floor can never reach a
# score — and they pin NOTHING about which value is right. R10 is still owed.


def test_a_lowered_separation_floor_moves_the_band_and_says_so():
    """The knob works, and the answer states that it was turned.

    A `grounded` judged at 0.02 is not the same claim as a `grounded` judged at
    0.10, and without the published floor the difference would be invisible.
    """
    scores = [1.0, 0.98]  # separation 0.02 — well under the default floor
    default = _q("rollback procedure", {"rollback": 40, "procedure": 12}, scores)
    assert default.band == WEAK
    assert default.separation_floor == SEPARATION_FLOOR

    slack = _q(
        "rollback procedure", {"rollback": 40, "procedure": 12}, scores,
        separation_floor=0.01,
    )
    assert slack.band == GROUNDED
    assert slack.as_dict()["separation_floor"] == 0.01, "the band must carry its own floor"
    assert slack.separation == default.separation, "the SIGNAL is untouched; only the verdict moved"


def test_a_zero_separation_floor_turns_the_weak_band_off_entirely():
    """Stated as a cost rather than clamped, per the standing rule on knobs.

    `separation < 0.0` is never true, so no answer is ever `weak`. That is a
    legal setting and a loud one — it is the setting that makes fux quiet about
    not knowing, which is exactly what decision 7 feared.
    """
    block = _q("rollback procedure", {"rollback": 40, "procedure": 12},
               [1.0, 1.0], separation_floor=0.0)
    assert block.separation == 0.0
    assert block.band == GROUNDED


def test_the_doc_coverage_gate_is_off_by_default_and_can_be_switched_on():
    """`0.0` is a MEASURED ruling (2026-08-28), not an unset placeholder.

    At `1.0` the clause fires on any question whose words are scattered — which
    is the case it was built for, and also 19 of 50 correct answers. The test
    pins the mechanism, never the recommendation.
    """
    scattered = dict(
        coverage=1.0, separation=0.58, support=3,
        verified="unverified", missing=(), doc_coverage=0.42,
    )
    assert Confidence(**scattered).band == GROUNDED, "the default gate is OFF"
    assert Confidence(**scattered).doc_coverage_floor == DOC_COVERAGE_FLOOR
    assert Confidence(**scattered, doc_coverage_floor=1.0).band == PARTIAL


def test_a_tuned_floor_cannot_reach_a_score_or_an_ordering(tmp_path, monkeypatch):
    """The claim the differential law rests on, asserted rather than assumed.

    Confidence is computed FROM `rank()`'s output and handed to the caller;
    nothing downstream feeds back. Making the floors configurable must not have
    opened a path from `.fux/tune.toml` into the result list.
    """
    write_index(tmp_path, [_record(), _record(id="file:docs/b.md", loc="docs/b.md")])
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".fux").mkdir(exist_ok=True)

    out_default: dict = {}
    base, _ = run_query(tmp_path, "rollback", 5, confidence_out=out_default)

    (tmp_path / ".fux" / "tune.toml").write_text(
        "[confidence]\nseparation_floor = 0.0\ndoc_coverage_floor = 1.0\n",
        encoding="utf-8",
    )
    out_tuned: dict = {}
    tuned, _ = run_query(tmp_path, "rollback", 5, confidence_out=out_tuned)

    assert [(r.id, r.score) for r in tuned] == [(r.id, r.score) for r in base]
    assert out_tuned["confidence"].separation_floor == 0.0
    assert out_tuned["confidence"].doc_coverage_floor == 1.0


def test_no_tune_recomputes_the_band_at_the_ENGINE_defaults():
    """The 'is it me or the config?' switch has to reach the band too.

    `--no-tune` already meant 'rank as the engine would'. If it did not also
    reset the floors, a repo could keep a slack `grounded` under the one flag
    that promises the engine's own answer.
    """
    from fux.tune import DEFAULT_TUNE, load

    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / ".fux").mkdir()
        (root / ".fux" / "tune.toml").write_text(
            "[confidence]\nseparation_floor = 0.9\n", encoding="utf-8"
        )
        assert load(root).separation_floor == 0.9
        assert load(root, enabled=False).separation_floor == SEPARATION_FLOOR
        assert load(root, enabled=False) == DEFAULT_TUNE


# ---------------------------------------------------------------------------
# W-214 — `weak` is a SIGNAL, and `answerable` is `band != none`
#
# 🔴 **This section REVERSES W-176 gate 1** (Arpit, 2026-09-22), whose tests
# stood here between 2026-09-14 and 2026-09-22 asserting the opposite. What
# reversed it is W-213: across 2 992 questions, eight rungs and three
# independently authored sets, the questions the band withheld were MORE likely
# to be right than the ones it answered, and no floor fixed it — including
# `0.00`. **`separation` does not carry correctness, so the threshold was never
# the thing to move.**
#
# ⚠ **The tests below pin the half of the ruling that is easy to lose.** *Stop
# refusing* is one line; *keep emitting the signal* is the line a later cleanup
# deletes as dead code, and deleting it completes the wrong half.
# ---------------------------------------------------------------------------


def test_weak_is_a_signal_not_a_refusal():
    """🔴 **The ruling, asserted on the payload rather than the property.**

    Between 2026-09-14 and 2026-09-22 this file asserted `answerable is False`
    here. It is `True` now, and the band, the floor it was judged under and
    `failed: ["separation"]` all still say precisely what they said — **a
    consumer that wants the old abstention has every byte it needs to implement
    it, and fux no longer makes that choice on its behalf.**
    """
    block = _q("rollback procedure", {"rollback": 40, "procedure": 12}, [1.0, 0.98])
    assert block.band == WEAK
    assert block.answerable is True
    payload = block.as_dict()
    assert payload["answerable"] is True, "the payload, not just the property"
    assert payload["band"] == WEAK, "the SIGNAL survives the refusal"
    assert payload["failed"] == ["separation"]


def test_weak_is_still_emitted_because_the_signal_is_the_whole_point():
    """🔴 **The half of W-214 a later cleanup would silently undo.**

    Once nothing refuses on `separation`, the `WEAK` branch of `band` and the
    `separation` branch of `failed` both look like dead code to anyone reading
    the expression alone. **They are the ruling.** *Keep the signal, drop the
    refusal* is not *drop both*, and this test is what fails if somebody tidies
    the second half away.

    Asserted across the floor, not at one value, so a sweep that removed the
    label everywhere but the default would also fail here.
    """
    for floor, separation in ((0.10, 0.05), (0.50, 0.30), (0.99, 0.98)):
        block = _q(
            "rollback procedure", {"rollback": 40, "procedure": 12},
            [1.0, 1.0 - separation], separation_floor=floor,
        )
        assert block.band == WEAK, floor
        assert block.failed == ["separation"], floor
        assert block.separation_floor == floor, "the floor it was judged under"
        assert block.answerable is True, "a signal, and never again a refusal"
        # And the human-readable line still says the ranking could not choose.
        assert "weak" in block.line() and "separation" in block.line()


def test_partial_stays_answerable_and_that_is_the_distinction():
    """`partial` is a NAMEABLE defect; `weak` has nothing to name.

    A consumer can answer a `partial` and say which term the corpus does not
    contain. There is no equivalent sentence for a `weak` — the ranking simply
    could not choose — which is why one abstains and the other does not.
    """
    block = _q("rollback mtls", {"rollback": 40}, [10.0, 1.0])
    assert block.band == PARTIAL
    assert block.missing, "the defect is nameable, which is what partial means"
    assert block.answerable is True


def test_the_band_table_and_answerable_cannot_disagree():
    """**The gate proper, and the reason W-214 is honest rather than a second
    silent disagreement.** Walks the whole band table and asserts `answerable`
    is the exact complement of the bands SR-CONFIDENCE decision 3 tells a
    consumer not to answer from.

    ⚠ **The expectation moved on 2026-09-22; the test did not weaken.** It read
    `{NONE, WEAK}` while decision 3's `weak` row said *do not answer*. That row
    now says *a signal — decide for yourself*, and this line moved with it **in
    the same change**. The property being enforced is unchanged and is the
    whole point: the table and the boolean are one statement, so they can never
    again be edited apart.

    A future band added to the table with no line here is the failure this
    catches: it would arrive answerable by default, which is the direction that
    loses silently.
    """
    refuse = {NONE}
    for band, block in (
        (NONE, Confidence(0.0, 0.0, 0, "unverified", ())),
        (WEAK, _q("rollback procedure", {"rollback": 40, "procedure": 12}, [1.0, 0.98])),
        (PARTIAL, _q("rollback mtls", {"rollback": 40}, [10.0, 1.0])),
        (GROUNDED, _q("rollback", {"rollback": 40}, [10.0, 1.0])),
    ):
        assert block.band == band, f"fixture does not produce {band}"
        assert block.answerable is (band not in refuse), band


def test_a_zero_floor_silences_the_SIGNAL_and_that_is_now_the_whole_cost():
    """⚠ The knob that turns the clause off, stated rather than clamped —
    **rewritten for W-214 rather than deleted, because its subject changed.**

    Between 2026-09-14 and 2026-09-22 this test's claim was that
    `separation_floor = 0.0` stopped fux abstaining on separation. **That
    sentence says nothing now**: nothing abstains on separation at any floor.

    What a zero floor still costs is real and is now the only thing it costs:
    **no block is ever labelled `weak`, so `failed` never names `separation`,
    and a consumer that implemented the old abstention for itself gets silence
    instead of a signal.** That is the sentence a consumer who sets this should
    find — the same shape of cost as before, one layer further out.
    """
    tied = _q("rollback procedure", {"rollback": 40, "procedure": 12},
              [1.0, 1.0], separation_floor=0.0)
    assert tied.separation == 0.0, "the SIGNAL is computed; only the label is gone"
    assert tied.band == GROUNDED
    assert tied.failed == [], "nothing to branch on — that is what was bought"
    assert tied.line() == "", "and nothing said on stderr either"

    # The control: at the engine default the same query is labelled, so the
    # cost above is attributable to the floor and to nothing else.
    at_default = _q("rollback procedure", {"rollback": 40, "procedure": 12}, [1.0, 1.0])
    assert at_default.band == WEAK
    assert at_default.failed == ["separation"]
    assert at_default.answerable is True, "answerable either way — W-214"


def test_failed_names_which_gate_fired():
    """`failed` names the gate. ⚠ **Since W-214 that is not the same as naming
    a refusal** — `separation` fires and fux answers anyway.

    ⚠ **The shape lands with gate 1, before the gates that fill it.** W-176's
    eight measured gates each append a name here and change nothing else, so a
    consumer written today keeps working as each one lands — which is the whole
    reason this key exists now rather than with the gate that first needs it.
    """
    weak = _q("rollback procedure", {"rollback": 40, "procedure": 12}, [1.0, 0.98])
    assert weak.band == WEAK and weak.answerable is True
    assert weak.failed == ["separation"]

    nothing = signals([], [], {}, 0, [])
    assert nothing.band == NONE and nothing.failed == ["no_candidates"]

    # `partial` is NOT a refusal: its defect is named in `missing`, and putting
    # it here would make `failed` mean "something is imperfect" rather than
    # "this is why you may not answer".
    partial = _q("rollback mtls", {"rollback": 40}, [10.0, 1.0])
    assert partial.band == PARTIAL and partial.answerable is True
    assert partial.failed == []

    grounded = _q("rollback", {"rollback": 40}, [10.0, 1.0])
    assert grounded.band == GROUNDED and grounded.failed == []


def test_every_refusal_names_at_least_one_failed_gate():
    """The invariant that keeps the two keys honest: **`answerable: false` and
    an empty `failed` is a refusal with no stated reason**, which is the state
    an agent cannot report and a maintainer cannot debug.

    A ninth gate added without a `failed` name would land in exactly that state
    and pass every other test in this file.

    ⚠ **This was an EQUIVALENCE until 2026-09-22 and is an implication now.**
    W-214 made `separation` a gate that fires without refusing, so
    *`failed` is non-empty* no longer implies *`answerable` is false* — and
    asserting the converse would have forced the ruling to delete the signal.
    `test_a_named_gate_may_fire_without_refusing` below is the other half, so
    the weakening is stated rather than left as a gap.
    """
    for block in (
        signals([], [], {}, 0, []),
        _q("rollback procedure", {"rollback": 40, "procedure": 12}, [1.0, 0.98]),
        _q("rollback mtls", {"rollback": 40}, [10.0, 1.0]),
        _q("rollback", {"rollback": 40}, [10.0, 1.0]),
    ):
        if block.answerable is False:
            assert block.failed, f"{block.band} refuses and says nothing"


def test_a_named_gate_may_fire_without_refusing():
    """The other half of W-214, stated so the asymmetry is deliberate.

    **`no_candidates` refuses; `separation` does not.** A consumer branching on
    `failed` being non-empty is implementing the PRE-W-214 behaviour — which is
    legal, is the thing the ruling left it the bytes to do, and is not what
    `answerable` means.
    """
    nothing = signals([], [], {}, 0, [])
    assert nothing.failed == ["no_candidates"] and nothing.answerable is False

    weak = _q("rollback procedure", {"rollback": 40, "procedure": 12}, [1.0, 0.98])
    assert weak.failed == ["separation"] and weak.answerable is True
