"""ADR-CONFIDENCE — the four signals, the four bands, and what must never move.

The easy tests here are the ones that assert a band comes out. **The ones that
matter are the four below the fold:**

- the band is a function of the signals and nothing else, so it cannot be
  reached by a score or an ordering;
- `--fast` and `--scan` produce the *same* block, or the differential law has a
  hole in it that says "confident" on one path and "weak" on the other;
- `missing` carries the word the user typed, not the stem the index is keyed by;
- `answerable` is `False` on the empty branch, which is the one an agent most
  needs to be stopped by.

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
    says *answer and name the gap*, `weak` says *do not answer*. Reporting the
    nameable defect is more useful than reporting the unnameable one.
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
        "band", "answerable", "coverage", "doc_coverage", "separation",
        "separation_floor", "doc_coverage_floor",
        "support", "verified", "missing",
    }
    # The floors are published for the OPPOSITE reason to `band`: not so a
    # consumer can re-derive the verdict, but so it can see the verdict is not
    # comparable across repos that tuned differently (ADR-CONFIDENCE 13).
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
        "meta": "plain",
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
    """ADR-CONFIDENCE decision 11 — and the half of it that is easy to lose.

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
    retention policy, `payments` in the postmortem, `api` in the mesh ADR — four
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
# ADR-CONFIDENCE decision 13 REVERSED decision 7, which had refused these as
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
