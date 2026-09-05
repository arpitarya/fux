"""W-111 — the declared tie-break, and `find`'s three precision controls.

**4.38 % of top-5 orderings were decided by a document's NAME.** That was
deterministic and meaningless: *the same arbitrary answer everywhere*. The
tie-break now reads signals someone declared — `superseded`, recency,
`[priority]` — and only where the rounded scores are equal, so no score moves
and no document passes one that outscores it.

The `find` filters are the other half: precision controls for a pipe, each of
which **removes** results the ranking already produced and retrieves nothing.
"""

from __future__ import annotations

import pytest

from fux.derive import accel, build
from fux.query import scan
from fux.query.rank import Weighting
from fux.store import term_hash, write_index


def _rec(doc_id, title, flen, terms, **extra) -> dict:
    record = {
        "id": doc_id, "src": "git", "loc": doc_id.removeprefix("file:"),
        "mode": "extracted", "meta": "plain", "title": title,
        "phrases": [], "terms": terms, "flen": flen, "edges": [],
    }
    record.update(extra)
    return record


ALPHA = term_hash("alpha")


def _tied_corpus(**per_doc) -> list[dict]:
    """Four documents with **identical** term counts and lengths.

    Identical inputs mean identical scores, so nothing but the tie-break can
    separate them — which is what makes each assertion below about the
    tie-break rather than about the scorer.
    """
    return [
        _rec(f"file:{name}.md", name.title(), [50], {ALPHA: [4, 1]}, **per_doc.get(name, {}))
        for name in ("b_doc", "a_doc", "c_doc", "d_doc")
    ]


def _ids(results):
    return [r.id for r in results]


# -- the order, one signal at a time ------------------------------------------


def test_with_no_signals_the_tie_breaks_on_id(tmp_path):
    """The old behaviour, kept as the FINAL tie-break so the order stays total
    and machine-independent."""
    write_index(tmp_path, _tied_corpus())
    got = _ids(scan.ask(tmp_path, "alpha", top=4))
    assert got == sorted(got)


def test_a_live_document_outranks_a_superseded_one_at_the_same_score(tmp_path):
    write_index(tmp_path, _tied_corpus(a_doc={"superseded": True}))
    got = _ids(scan.ask(tmp_path, "alpha", top=4))
    assert got[-1] == "file:a_doc.md", "the superseded document should sort last among equals"
    assert got[0] == "file:b_doc.md", "and `id` should still order the rest"


def test_recency_breaks_a_tie_when_the_recency_WEIGHT_is_off(tmp_path):
    """Recency is a **fact** (`mtime`) as well as a weight, and the fact is
    readable when the weight is off — which is the shipped default
    (`recency_half_life_days = 0.0`). That asymmetry is what makes it usable as
    a tie-break without turning a ranking prior on."""
    write_index(tmp_path, _tied_corpus(d_doc={"mtime": 2000}, a_doc={"mtime": 1000}))
    got = _ids(scan.ask(tmp_path, "alpha", top=4))
    assert got[0] == "file:d_doc.md", "the newest of four equal scores should lead"
    assert got[1] == "file:a_doc.md", "then the next newest, before the undated ones"


def test_priority_cannot_reach_the_tie_break_and_the_reason_is_recorded(tmp_path):
    """🔴 **`-priority` in the ratified order is UNREACHABLE, and this test says
    so rather than pretending otherwise.**

    Arpit ratified `superseded -> recency -> priority -> id` on 2026-09-05, and
    the slot is implemented. But `[priority]` is not a fact beside a weight the
    way `superseded` and `mtime` are — **`priority_for` IS the weight**, and
    `Weighting.of` multiplies the score by it. So two documents with different
    priorities have different *scores* and never reach the tie-break, and two
    with the same priority are not separated by it.

    The slot is kept because it is what was ratified, it costs nothing, and it
    is already correct if `[priority]` ever becomes a declaration that does not
    multiply. **ADR-RANKING records this; the code does not pretend.**
    """
    write_index(tmp_path, _tied_corpus())
    weighting = Weighting(priority=(("c_doc.md", 5.0),))
    got = scan.ask(tmp_path, "alpha", top=4, weighting=weighting)
    assert got[0].id == "file:c_doc.md"
    assert got[0].score > got[1].score, (
        "priority separated these by SCORE, not by the tie-break — if this ever "
        "fails, `[priority]` has stopped multiplying and the tie-break slot has "
        "become reachable"
    )
    assert got[0].tie is False


def test_superseded_outranks_recency_in_the_order(tmp_path):
    """The newest document in the corpus, but retired: it still sorts last.

    Order matters and this is where it shows — a tie-break that consulted
    recency first would put a retired document at the top for being fresh.
    """
    write_index(tmp_path, _tied_corpus(a_doc={"superseded": True, "mtime": 9999}))
    got = _ids(scan.ask(tmp_path, "alpha", top=4))
    assert got[-1] == "file:a_doc.md"


# -- it changes ONLY ties -----------------------------------------------------


def test_the_tie_break_never_moves_a_document_past_one_that_outscores_it(tmp_path):
    """🔴 The guarantee that keeps W-94's *"doing nothing is legitimate"*
    intact. Every signal here is already a `Weighting` multiplier shipping as a
    no-op; this key reads the same facts and reads them **only** among equals.
    """
    records = _tied_corpus(a_doc={"superseded": True, "mtime": 9999})
    # One document scores strictly higher than the rest.
    records.append(_rec("file:z_doc.md", "Z", [50], {ALPHA: [40, 10]}))
    write_index(tmp_path, records)
    got = scan.ask(tmp_path, "alpha", top=5)
    assert got[0].id == "file:z_doc.md"
    assert got[0].score > got[1].score


def test_the_accelerator_orders_ties_identically(tmp_path):
    """The differential law, on the tie-break specifically. Both paths reach
    `rank()` with the same record dicts, and the key reads only fields both
    generators already carry."""
    write_index(tmp_path, _tied_corpus(a_doc={"superseded": True}, d_doc={"mtime": 2000}))
    build(tmp_path)
    expected = [(r.id, r.tie) for r in scan.ask(tmp_path, "alpha", top=4)]
    for skipping in (False, True):
        got = [(r.id, r.tie) for r in accel.ask(tmp_path, "alpha", top=4, skipping=skipping)]
        assert got == expected, f"skipping={skipping}"


# -- `tie` ---------------------------------------------------------------------


def test_every_tied_result_is_marked(tmp_path):
    write_index(tmp_path, _tied_corpus())
    assert all(r.tie for r in scan.ask(tmp_path, "alpha", top=4))


def test_a_result_tied_with_a_document_BELOW_THE_CUT_is_still_marked(tmp_path):
    """The row most likely to have been a coin-toss is the last one shown, and
    a neighbour comparison on the truncated window would silently un-mark it."""
    write_index(tmp_path, _tied_corpus())
    got = scan.ask(tmp_path, "alpha", top=2)
    assert len(got) == 2 and got[-1].tie, (
        "the last row ties with the third document, which is off the page"
    )


def test_an_untied_result_is_not_marked(tmp_path):
    """`false` has to be a claim, or the flag says nothing."""
    records = _tied_corpus()
    records.append(_rec("file:z_doc.md", "Z", [50], {ALPHA: [40, 10]}))
    write_index(tmp_path, records)
    got = scan.ask(tmp_path, "alpha", top=5)
    assert got[0].id == "file:z_doc.md" and got[0].tie is False
    assert all(r.tie for r in got[1:])


# -- `find`'s filters ---------------------------------------------------------


class _Args:
    def __init__(self, **kw):
        self.query = kw.pop("query", "alpha")
        self.phrase = kw.pop("phrase", None)
        self.under = kw.pop("under", None)
        self.require_all = kw.pop("require_all", False)
        for k, v in kw.items():
            setattr(self, k, v)


def _filter_corpus(root):
    from fux.ingest import run as ingest_run

    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    dirs = root / ".fux" / "sources" / "dirs"
    dirs.parent.mkdir(parents=True, exist_ok=True)
    dirs.write_text("docs\n", encoding="utf-8")
    (root / "docs" / "runbooks").mkdir(parents=True)
    (root / "docs" / "runbooks" / "roll.md").write_text(
        "# Rollback\n\nTo roll back a release, drain the sidecar first.\n", encoding="utf-8")
    (root / "docs" / "notes.md").write_text(
        "# Notes\n\nA release can roll forward, and a rollback is separate. Back it up.\n",
        encoding="utf-8")
    (root / "docs" / "other.md").write_text(
        "# Other\n\nA release note with nothing else in it.\n", encoding="utf-8")
    ingest_run.run(root)
    return root


def test_under_keeps_only_a_path_prefix(tmp_path):
    from fux.query import _filtered, run_query

    root = _filter_corpus(tmp_path)
    results, _ = run_query(root, "release", 10, force_scan=True)
    kept, dropped = _filtered(root, results, _Args(query="release", under="docs/runbooks"))
    assert [r.loc for r in kept] == ["docs/runbooks/roll.md"]
    assert dropped == len(results) - 1


def test_all_requires_every_query_term(tmp_path):
    from fux.query import _filtered, run_query

    root = _filter_corpus(tmp_path)
    q = "release sidecar"
    results, _ = run_query(root, q, 10, force_scan=True)
    assert len(results) > 1, "precondition: more than one document matches SOME term"
    kept, _ = _filtered(root, results, _Args(query=q, require_all=True))
    assert [r.loc for r in kept] == ["docs/runbooks/roll.md"]


def test_phrase_requires_adjacency_and_order(tmp_path):
    """`notes.md` contains both words and never adjacently in that order —
    which is the whole distinction a phrase filter exists to make."""
    from fux.query import _filtered, run_query

    root = _filter_corpus(tmp_path)
    results, _ = run_query(root, "roll back", 10, force_scan=True)
    assert {r.loc for r in results} >= {"docs/runbooks/roll.md", "docs/notes.md"}
    kept, _ = _filtered(root, results, _Args(query="roll back", phrase="roll back"))
    assert [r.loc for r in kept] == ["docs/runbooks/roll.md"]


def test_no_filter_is_the_identity(tmp_path):
    from fux.query import _filtered, run_query

    root = _filter_corpus(tmp_path)
    results, _ = run_query(root, "release", 10, force_scan=True)
    kept, dropped = _filtered(root, results, _Args(query="release"))
    assert kept == list(results) and dropped == 0


def test_a_url_document_is_kept_by_phrase_rather_than_dropped(tmp_path):
    """⚠ Offline it has no text to test, and dropping it would report *"this
    page does not contain the phrase"* on the strength of not having looked."""
    from fux.query import _filtered
    from fux.query.rank import AskResult

    results = [AskResult(id="url:https://x.test/a", title="A", loc="https://x.test/a", score=1.0)]
    kept, dropped = _filtered(tmp_path, results, _Args(query="roll back", phrase="roll back"))
    assert kept == results and dropped == 0


@pytest.mark.parametrize(("phrase", "text", "expected"), [
    ("roll back", "you roll back the release", True),
    ("roll back", "back and roll", False),
    # ⚠ **Stopwords are dropped by the analyzer**, so `roll the back` IS the
    # bigram `roll back` as far as the index is concerned. A phrase filter that
    # disagreed with the analyzer would be a second notion of what a token is.
    ("roll back", "roll the back", True),
    ("rollback", "a rollback happened", True),   # single term: presence
    ("rollback", "nothing here", False),
])
def test_phrase_present_is_ordered_and_immediate(phrase, text, expected):
    from fux.query.analyzer import analyze
    from fux.query.rerank import phrase_present

    assert phrase_present(analyze(phrase), text) is expected
