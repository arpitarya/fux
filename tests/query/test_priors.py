"""W-76 Phase 2's priors — all three now REMOVED — and the law they left behind.

🔴 **`superseded_weight`, `archived_weight` and `recency_half_life_days` were
all removed on 2026-09-13** (W-151, W-152; SR-TUNE decision 15), on
VERDICT-W143's finding that no single global value clears the bar for any of
them. Each shipped as a no-op, so nothing ranked differently. **The FACTS they
read are all still committed and all still tested** — `superseded_ids` below,
`archived` in `test_scan.py`, and the declared tie-break in
`test_ties_and_filters.py`.

**What survives is the LAW, and this file is where it is asserted.** A prior is
a multiplier, and W-73 is the reason: a multiplier that reaches the scorer
without reaching the accelerator's pruning bound makes `--fast` and `--scan`
return different documents, silently, only at non-default settings, only on some
corpora. So every ordering test here runs down **both paths**, at settings far
enough from the default to actually bite. `[priority]` is the one multiplier
left and it carries that duty now.

`SR-T1-ACCELERATOR` veto 5 is the standing rule: **any multiplier that arrives
next** goes through `query/rank.py::Weighting`, which is what `maximum` and the
weighted `theta` read.
"""

from __future__ import annotations

import pytest

from fux.derive import accel, build
from fux.ingest.priors import superseded_ids
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
    """Nothing configured means nothing scaled, down both paths."""
    plain = _both_paths(corpus, Weighting())
    assert _ids(plain) == ["file:old.md", "file:new.md"], (
        "fixture: the retired document must win on text alone, or nothing below is under test"
    )


def test_no_document_prior_can_be_configured_any_more(corpus):
    """🔴 The W-151/W-152 removals, asserted rather than assumed.

    `Weighting` has no field for any of the three, so a caller cannot demote a
    retired, superseded or old document by configuration at all — and the
    retired document keeps the lead its better text earns it. A live document
    wins only at an **equal** score, through the declared tie-break, which is a
    different mechanism tested in `test_ties_and_filters.py`.
    """
    for gone in ("superseded_weight", "archived_weight", "recency_half_life_days"):
        with pytest.raises(TypeError):
            Weighting(**{gone: 0.1})
    assert _ids(_both_paths(corpus, Weighting())) == ["file:old.md", "file:new.md"]


def test_priority_demotes_and_both_paths_agree(corpus):
    """The one surviving multiplier still carries W-73's duty on both paths."""
    results = _both_paths(corpus, Weighting(priority=(("old.md", 0.1),)))
    assert _ids(results) == ["file:new.md", "file:old.md"]


def test_the_ceiling_is_never_lowered_by_a_configuration_of_DEMOTIONS():
    """🔴 `max(1.0, ...)`, and it is the half that looks unnecessary.

    An unlisted document is scaled by `1.0`, so `1.0` is always attainable.
    Taking the configured weight alone would make the ceiling too small whenever
    every configured weight is `< 1` — the demotion direction, which is the one
    that looks safe and is the W-73 defect's exact shape.
    """
    assert Weighting(priority=(("old.md", 0.1),)).maximum == 1.0
    assert Weighting(priority=(("old.md", 5.0),)).maximum == 5.0
    assert Weighting().maximum == 1.0


def test_the_ceiling_is_the_LARGEST_configured_weight_not_the_first():
    """Two prioritised sources: the supremum is over the configuration, never
    over the candidates in hand — an unseen document may carry a weight no
    candidate does, and that is precisely the case the bound must survive."""
    w = Weighting(priority=(("vendor/", 2.0), ("docs/", 7.0)))
    assert w.maximum == 7.0


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
