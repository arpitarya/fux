"""W-76 Phase 2 — recency and supersession, and the law they must not break.

Both priors are multipliers, and W-73 is the reason this file exists rather
than a couple of ordering assertions. A multiplier that reaches the scorer
without reaching the accelerator's pruning bound makes `--fast` and `--scan`
return different documents, silently, only at non-default settings, only on
some corpora. So every ordering test here is run down **both paths**, at
settings far enough from the default to actually bite.

`ADR-T1-ACCELERATOR` veto 5 is the standing rule: any new multiplier goes
through `query/rank.py::Weighting`, which is what `maximum` and the weighted
`theta` read. These two were the first to arrive under it.
"""

from __future__ import annotations

import pytest

from fux.derive import accel, build
from fux.ingest.priors import recency_multiplier, superseded_ids
from fux.query import scan
from fux.query.rank import Weighting
from fux.store import TF_FIELDS, term_hash, write_index

BODY = TF_FIELDS.index("body")
DAY = 86400
NOW = 1_800_000_000


def _rec(doc_id, title, tf, *, superseded=False, mtime=None, edges=()) -> dict:
    body_tf = [0] * len(TF_FIELDS)
    body_tf[BODY] = tf
    flen = [0] * len(TF_FIELDS)
    flen[BODY] = 60
    record = {
        "id": doc_id,
        "src": "git",
        "loc": doc_id.removeprefix("file:"),
        "mode": "extracted",
        "meta": "plain",
        "title": title,
        "phrases": [],
        "terms": {term_hash("rollback"): body_tf},
        "flen": flen,
        "edges": list(edges),
    }
    if superseded:
        record["superseded"] = True
    if mtime is not None:
        record["mtime"] = mtime
    return record


@pytest.fixture
def corpus(tmp_path):
    """The retired document is the BETTER lexical match.

    Deliberately: if the live document already won on the text, a demotion
    could not be observed and every assertion below would pass without the
    feature existing.
    """
    write_index(
        tmp_path,
        [
            _rec("file:old.md", "Retired decision", 30, superseded=True, mtime=NOW - 400 * DAY),
            _rec("file:new.md", "Live decision", 6, mtime=NOW),
        ],
    )
    build(tmp_path)
    return tmp_path


def _ids(results):
    return [r.id for r in results]


def _both_paths(root, weighting, top=5):
    """Rank down the scan and the accelerator; assert they agree; return one."""
    expected = scan.ask(root, "rollback", top=top, weighting=weighting)
    for skipping in (False, True):
        got = accel.ask(root, "rollback", top=top, weighting=weighting, skipping=skipping)
        assert [(r.id, round(r.score, 9)) for r in got] == [
            (r.id, round(r.score, 9)) for r in expected
        ], f"paths diverged at {weighting} (skipping={skipping})"
    return expected


def test_the_defaults_change_nothing(corpus):
    """Both priors ship off. A corpus that configures nothing must be untouched."""
    plain = _both_paths(corpus, Weighting())
    assert _ids(plain) == ["file:old.md", "file:new.md"], (
        "fixture: the retired document must win on text alone, or nothing below is under test"
    )


def test_supersession_demotes_and_both_paths_agree(corpus):
    results = _both_paths(corpus, Weighting(superseded_weight=0.1))
    assert _ids(results) == ["file:new.md", "file:old.md"], (
        "a retired decision outranked the live one that replaced it"
    )


def test_recency_demotes_and_both_paths_agree(corpus):
    results = _both_paths(corpus, Weighting(recency_half_life_days=30.0, newest_mtime=NOW))
    assert _ids(results) == ["file:new.md", "file:old.md"]


def test_the_two_priors_compose(corpus):
    both = _both_paths(
        corpus,
        Weighting(superseded_weight=0.5, recency_half_life_days=90.0, newest_mtime=NOW),
    )
    assert _ids(both) == ["file:new.md", "file:old.md"]


def test_maximum_is_the_PRODUCT_of_the_independent_suprema():
    """`archived` and `superseded` are independent flags.

    A document can be both, and is then scaled twice. Taking the larger of the
    two suprema instead of their product would under-estimate the ceiling —
    which is the error direction that loses documents, and the exact shape of
    the W-73 defect.
    """
    w = Weighting(archived_weight=3.0, superseded_weight=5.0)
    assert w.maximum == 15.0

    # Recency contributes exactly 1.0 because it is bounded to (0, 1].
    assert Weighting(recency_half_life_days=7.0, newest_mtime=NOW).maximum == 1.0


def test_recency_is_bounded_to_zero_one():
    """The bound `Weighting.maximum` relies on.

    An unbounded recency prior would make the supremum unbounded and the block
    bound useless — a ceiling of infinity skips nothing.
    """
    assert recency_multiplier(NOW, NOW, 30.0) == 1.0
    assert 0.0 < recency_multiplier(NOW - 3650 * DAY, NOW, 30.0) <= 1.0
    assert recency_multiplier(NOW - 30 * DAY, NOW, 30.0) == pytest.approx(0.5)
    # A document newer than "newest" cannot exceed 1.0 (clock skew, a future
    # commit date) — `age_days` is clamped at zero.
    assert recency_multiplier(NOW + 100 * DAY, NOW, 30.0) == 1.0
    # Off by default, and off means exactly 1.0 rather than approximately.
    assert recency_multiplier(NOW - 999 * DAY, NOW, 0.0) == 1.0
    assert recency_multiplier(None, NOW, 30.0) == 1.0


def test_supersession_is_declared_never_inferred():
    """`superseded_ids` reads edges; it does not guess from titles or numbering."""
    records = [
        _rec("file:a.md", "A", 1, edges=[{"kind": "supersedes", "dst": "file:b.md", "grade": 10}]),
        _rec("file:b.md", "B", 1),
        _rec("file:c.md", "C v2", 1),  # a name that LOOKS like a successor
    ]
    assert superseded_ids(records) == {"file:b.md"}, "only the declared edge may count"


def test_a_supersedes_edge_to_an_unknown_document_is_dropped():
    """A dangling declaration must not mark anything."""
    records = [
        _rec("file:a.md", "A", 1, edges=[{"kind": "supersedes", "dst": "file:gone.md", "grade": 10}]),
    ]
    assert superseded_ids(records) == set()


def test_a_document_cannot_supersede_itself():
    records = [
        _rec("file:a.md", "A", 1, edges=[{"kind": "supersedes", "dst": "file:a.md", "grade": 10}]),
    ]
    assert superseded_ids(records) == set()
