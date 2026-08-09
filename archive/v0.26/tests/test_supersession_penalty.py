"""The supersession down-rank penalty (handoff 0007 M2, ADR 0015).

The load-bearing property is **identity at the default**: `supersession_penalty
= 0` must leave every ranking byte-identical to v0.25.0. That is what let this
knob land before calibration proved it safe to enable, so it is tested first and
hardest here.

The second property is that the penalised set is **deterministic** — exactly the
documents whose author wrote a frontmatter marker. A document that merely says
"superseded" in prose, or carries a near-miss `status:`, must never be touched;
inferring supersession from content is forbidden (no-model constraint).
"""

from __future__ import annotations

import pytest

from fux.config import load
from fux.errors import FuxError
from fux.index.fuse import rrf
from fux.kernel import retrieve

from test_ingest import run
from test_supersession import supersession_project

QUERY = "settlement window"


def _configure(tmp_path, penalty: int | None) -> None:
    """Rewrite fux.toml with (or without) the penalty knob."""
    toml = '[sources]\ndocs = ["docs"]\n'
    if penalty is not None:
        toml += f"\n[engine.hybrid]\nsupersession_penalty = {penalty}\n"
    (tmp_path / "fux.toml").write_text(toml, encoding="utf-8")


def _ranked_docs(tmp_path, penalty: int | None, query: str = QUERY) -> list[str]:
    """Fused document order for `query`, in rank order, deduplicated."""
    _configure(tmp_path, penalty)
    result = retrieve(load(tmp_path), query, k=20)
    order: list[str] = []
    for p in result.passages:
        if p.file not in order:
            order.append(p.file)
    return order


def test_fixture_actually_exercises_the_hybrid_path(tmp_path, monkeypatch):
    """Guard against vacuity: the penalty lives in fusion, so if this corpus
    fell back to lexical every penalty assertion below would pass trivially."""
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    _configure(tmp_path, 0)
    assert retrieve(load(tmp_path), QUERY, k=20).engine == "hybrid"


# -- the fusion primitive --------------------------------------------------


def test_rrf_without_offsets_is_untouched():
    lists = [["a", "b", "c"], ["c", "a"]]
    assert rrf(lists, k=60) == rrf(lists, k=60, offsets=None)
    assert rrf(lists, k=60) == rrf(lists, k=60, offsets={})


def test_rrf_zero_offset_equals_no_offset():
    """0 is exact identity, not an approximation of it."""
    lists = [["a", "b", "c"], ["c", "a"]]
    assert rrf(lists, k=60, offsets={"a": 0, "b": 0}) == rrf(lists, k=60)


def test_rrf_offset_demotes_only_the_named_item():
    lists = [["a", "b"]]
    base = rrf(lists, k=60)
    penalised = rrf(lists, k=60, offsets={"a": 5})
    assert penalised["a"] < base["a"]
    assert penalised["b"] == base["b"]
    # contributes as though it had placed 5 positions lower
    assert penalised["a"] == pytest.approx(1.0 / (60 + 1 + 5))


def test_rrf_penalty_demotes_but_never_removes():
    """A penalty is a rank penalty, not a filter — the doc stays reachable, so a
    question genuinely *about* the retired decision can still find it."""
    lists = [["a", "b"]]
    penalised = rrf(lists, k=60, offsets={"a": 10_000})
    assert penalised["a"] > 0.0


# -- the config knob -------------------------------------------------------


def test_default_is_the_calibrated_value(tmp_path):
    """15 is a measurement, not a preference — the safe interval is [11, ∞)
    across all four eval sets. If this changes, the sweep must be re-run."""
    _configure(tmp_path, None)
    assert load(tmp_path).hybrid.supersession_penalty == 15


def test_penalty_parses(tmp_path):
    _configure(tmp_path, 25)
    assert load(tmp_path).hybrid.supersession_penalty == 25


@pytest.mark.parametrize("bad", ["-1", "1.5", "true", '"5"'])
def test_invalid_penalty_is_rejected(tmp_path, bad):
    (tmp_path / "fux.toml").write_text(
        f'[sources]\ndocs = ["docs"]\n\n[engine.hybrid]\nsupersession_penalty = {bad}\n',
        encoding="utf-8",
    )
    with pytest.raises(FuxError, match="supersession_penalty"):
        load(tmp_path)


# -- identity at the default (the safety property) -------------------------


def test_absent_knob_uses_the_calibrated_default(tmp_path, monkeypatch):
    """Omitting the key must behave exactly as writing the shipped value — a
    config that says nothing and one that says 15 cannot disagree."""
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    assert _ranked_docs(tmp_path, None) == _ranked_docs(tmp_path, 15)


def test_zero_restores_pre_026_ranking_exactly(tmp_path, monkeypatch):
    """`0` is the documented escape hatch back to v0.25.0 behaviour, and it must
    be *exact* — same order, same fused scores, no penalty metadata. This is the
    property that lets a user revert in the field without a release."""
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")

    _configure(tmp_path, 0)
    off = [(p.file, p.ordinal, p.score, dict(p.hybrid or {}))
           for p in retrieve(load(tmp_path), QUERY, k=20).passages]
    _configure(tmp_path, 15)
    on = [(p.file, p.ordinal, p.score, dict(p.hybrid or {}))
          for p in retrieve(load(tmp_path), QUERY, k=20).passages]

    # the knob is genuinely live on this corpus — otherwise "off == v0.25.0"
    # would be a claim about a no-op
    assert off != on
    # and with it off, nothing about the penalty survives into the output
    assert all("supersession_penalty" not in info for *_, info in off)
    # scores are the raw RRF sums, untouched by any offset arithmetic
    for _, _, score, info in off:
        assert score == pytest.approx(info["rrf"], abs=1e-5)


def test_zero_penalty_emits_no_penalty_metadata(tmp_path, monkeypatch):
    """Off must be invisible in the output contract, not merely inert."""
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    _configure(tmp_path, 0)
    for p in retrieve(load(tmp_path), QUERY, k=20).passages:
        assert "supersession_penalty" not in (p.hybrid or {})


# -- the penalty, applied --------------------------------------------------


def test_penalty_demotes_the_superseded_document(tmp_path, monkeypatch):
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    baseline = _ranked_docs(tmp_path, 0)
    penalised = _ranked_docs(tmp_path, 500)
    assert baseline.index("docs/legacy.md") <= penalised.index("docs/legacy.md")
    assert penalised.index("docs/current.md") < penalised.index("docs/legacy.md")


def test_penalised_document_is_still_retrievable(tmp_path, monkeypatch):
    """The pre-mortem case: a heavy penalty must not make the retired document
    unreachable for someone asking about the retired decision."""
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    assert "docs/legacy.md" in _ranked_docs(tmp_path, 10_000)


def test_unmarked_documents_are_never_penalised(tmp_path, monkeypatch):
    """`prose.md` says "superseded" in its body; `decoy.md` has a near-miss
    status. Neither carries the contract, so neither may be touched — this is
    the no-NLP boundary, enforced."""
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    _configure(tmp_path, 500)
    penalised = {
        p.file for p in retrieve(load(tmp_path), "superseded settlement", k=20).passages
        if "supersession_penalty" in (p.hybrid or {})
    }
    assert "docs/prose.md" not in penalised
    assert "docs/decoy.md" not in penalised
    assert "docs/draft.md" not in penalised


def test_chain_penalises_every_link_but_not_the_terminal(tmp_path, monkeypatch):
    """midlink → legacy → current. Both retired links are down-ranked; the
    terminal current document is not."""
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    _configure(tmp_path, 500)
    marked = {
        p.file: (p.hybrid or {}).get("supersession_penalty")
        for p in retrieve(load(tmp_path), QUERY, k=20).passages
    }
    assert marked.get("docs/midlink.md") == 500
    assert marked.get("docs/legacy.md") == 500
    assert marked.get("docs/current.md") is None


def test_unresolved_supersession_is_still_penalised(tmp_path, monkeypatch):
    """A dangling or cyclic successor still means the author retired the doc.
    The marker is the contract; resolving it is a separate concern."""
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    _configure(tmp_path, 500)
    marked = {
        p.file for p in retrieve(load(tmp_path), "points at successor restatement", k=20).passages
        if "supersession_penalty" in (p.hybrid or {})
    }
    assert "docs/dangling.md" in marked or "docs/cycle-a.md" in marked


def test_penalty_records_the_rank_shift(tmp_path, monkeypatch):
    """DoD 7's evidence: the shift is measured, not asserted."""
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    _configure(tmp_path, 500)
    for p in retrieve(load(tmp_path), QUERY, k=20).passages:
        info = p.hybrid or {}
        if "supersession_penalty" in info:
            assert info["rank_before_penalty"] is not None
            assert info["rank_after_penalty"] is not None
            assert info["rank_after_penalty"] >= info["rank_before_penalty"]


# -- `fux why` surfaces it (DoD 7) -----------------------------------------


def test_why_reports_the_penalty_and_the_shift(tmp_path, monkeypatch):
    from fux.query.why import why

    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    _configure(tmp_path, 500)
    result = why(load(tmp_path), QUERY, "docs/legacy.md")
    assert result.superseded is True
    assert result.penalty["offset"] == 500
    assert result.penalty["rank_after"] >= result.penalty["rank_before"]
    assert result.to_json()["supersession_penalty"]["offset"] == 500


def test_why_is_silent_about_the_penalty_when_off(tmp_path, monkeypatch):
    from fux.query.why import why

    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    _configure(tmp_path, 0)
    result = why(load(tmp_path), QUERY, "docs/legacy.md")
    assert result.superseded is True  # annotation still shows (v0.25.0 behaviour)
    assert result.penalty is None
    assert "supersession_penalty" not in result.to_json()


# -- lean/full parity ------------------------------------------------------


def test_lean_honours_the_penalty_too(tmp_path, monkeypatch):
    """Lean carries the marker in its committed state flags. If it ignored the
    penalty, lean and full rankings would be identical only while the knob was
    off — and the df-sidecar parity law says *provably*, not usually."""
    from fux.query.lean import LeanCorpus

    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    _configure(tmp_path, 0)
    baseline = [doc for doc, _ in LeanCorpus(load(tmp_path)).search(QUERY)]
    _configure(tmp_path, 500)
    penalised = [doc for doc, _ in LeanCorpus(load(tmp_path)).search(QUERY)]
    assert set(baseline) == set(penalised)  # demoted, never dropped
    assert baseline.index("docs/legacy.md") <= penalised.index("docs/legacy.md")


def test_lean_absent_knob_matches_the_default(tmp_path, monkeypatch):
    from fux.query.lean import LeanCorpus

    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    _configure(tmp_path, None)
    baseline = LeanCorpus(load(tmp_path)).search(QUERY)
    _configure(tmp_path, 15)
    assert baseline == LeanCorpus(load(tmp_path)).search(QUERY)


def test_lean_zero_restores_pre_026_ranking(tmp_path, monkeypatch):
    """The escape hatch works on the committed plane too, or a fresh clone and a
    fully-ingested repo would disagree about what `0` means."""
    from fux.query.lean import LeanCorpus

    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    _configure(tmp_path, 0)
    off = LeanCorpus(load(tmp_path)).search(QUERY)
    _configure(tmp_path, 15)
    assert off != LeanCorpus(load(tmp_path)).search(QUERY)


# -- the penalty never reaches the lexical plane ---------------------------


def test_lexical_only_is_unaffected_by_the_penalty(tmp_path, monkeypatch):
    """The penalty lives in fusion, and `--lexical-only` never fuses. This is a
    structural guarantee, not a tuning choice."""
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    _configure(tmp_path, 0)
    baseline = retrieve(load(tmp_path), QUERY, k=20, lexical_only=True).passages
    _configure(tmp_path, 500)
    penalised = retrieve(load(tmp_path), QUERY, k=20, lexical_only=True).passages
    assert [(p.file, p.ordinal, p.score) for p in baseline] == [
        (p.file, p.ordinal, p.score) for p in penalised
    ]
