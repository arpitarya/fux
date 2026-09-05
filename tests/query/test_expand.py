"""W-109 — `--expand`: the byte-identity guarantee and the hallucination guard.

Two properties, and the second one is the reason this feature is allowed to
exist at all:

1. **No expansion changes nothing.** Not approximately: the same floats, on
   both candidate paths, because `score_record` performs no multiply when
   `Expansion.trivial`.
2. 🔴 **A document matching only expansion terms is never returned.** The
   caller supplying `--expand` is usually a model, and returning a document
   that matches *nothing the user asked* — scored entirely on words the model
   invented — is a hallucinated citation with a fresh `sha` beside it.

The accelerator's block bound under per-term weights is
`tests/derive/test_expand_bound.py`; it is the W-73 class of defect and it gets
its own adversarial corpus.
"""

from __future__ import annotations

import pytest

from fux.derive import accel, build
from fux.query import scan
from fux.query.expand import Expansion, build as build_expansion
from fux.store import term_hash, write_index


def _rec(doc_id: str, title: str, flen, terms) -> dict:
    return {
        "id": doc_id,
        "src": "git",
        "loc": doc_id.removeprefix("file:"),
        "mode": "extracted",
        "meta": "plain",
        "title": title,
        "phrases": [],
        "terms": terms,
        "flen": flen,
        "edges": [],
    }


#: `alpha` is the *query*'s word; `omega` is the *expansion*'s. `only-omega`
#: exists to be excluded — it is the document a model's invented vocabulary
#: would otherwise drag into an answer.
ALPHA, OMEGA, FILLER = term_hash("alpha"), term_hash("omega"), term_hash("filler")


def _corpus() -> list[dict]:
    return [
        _rec("file:both.md", "Both", [90], {ALPHA: [4, 1], OMEGA: [6, 2]}),
        _rec("file:alpha-only.md", "Alpha only", [90], {ALPHA: [4, 1], FILLER: [3, 0]}),
        # 🔴 The document under test: it answers nothing the user asked.
        _rec("file:omega-only.md", "Omega only", [40], {OMEGA: [20, 8]}),
        *[_rec(f"file:pad{i}.md", f"Pad {i}", [120], {FILLER: [2, 0]}) for i in range(40)],
    ]


@pytest.fixture
def built(tmp_path):
    write_index(tmp_path, _corpus())
    build(tmp_path)
    return tmp_path


def _payload(results):
    return [(r.id, repr(r.score)) for r in results]


def _expansion(query: str, expansion: str, weight: float) -> Expansion:
    return build_expansion(
        scan.query_term_hashes(query), scan.query_term_hashes(expansion), weight
    )


# -- 1. the identity ---------------------------------------------------------


def test_no_expansion_is_byte_identical(built):
    """`Expansion.none` must not perturb a single float.

    `repr` on the score, not `==` on a rounded value: the differential law is
    a byte claim, and a feature that shifted the last bit of every score while
    the parameter was unused would break it silently on the day someone diffed
    two versions.
    """
    base = _payload(scan.ask(built, "alpha", top=10))
    none = _payload(scan.ask(built, "alpha", top=10, expansion=Expansion.none(scan.query_term_hashes("alpha"))))
    assert none == base

    # And an expansion whose weight is off is the identity too — the
    # off-switch has to be reachable by configuration, not only by omission.
    off = _payload(scan.ask(built, "alpha", top=10, expansion=_expansion("alpha", "omega", 0.0)))
    assert off == base


def test_an_expansion_that_repeats_the_query_changes_nothing(built):
    """A term the user already typed stays at 1.0.

    Otherwise a caller could quietly demote their own query by mentioning one
    of its own words in the expansion — a foot-gun with no upside.
    """
    base = _payload(scan.ask(built, "alpha", top=10))
    same = _payload(scan.ask(built, "alpha", top=10, expansion=_expansion("alpha", "alpha", 0.2)))
    assert same == base


# -- 2. the hallucination guard ----------------------------------------------


def test_a_document_matching_only_expansion_terms_is_never_returned(built):
    """🔴 The guard, on the reference path."""
    expansion = _expansion("alpha", "omega", 0.2)
    ids = [r.id for r in scan.ask(built, "alpha", top=50, expansion=expansion)]
    assert "file:omega-only.md" not in ids
    assert "file:both.md" in ids and "file:alpha-only.md" in ids


def test_the_guard_holds_on_the_accelerator_too(built):
    """The same guard, on the path a filter in `cmd_ask` would have missed."""
    expansion = _expansion("alpha", "omega", 0.2)
    for skipping in (False, True):
        ids = [r.id for r in accel.ask(built, "alpha", top=50, skipping=skipping, expansion=expansion)]
        assert "file:omega-only.md" not in ids


def test_the_guard_holds_at_a_weight_that_would_otherwise_win(built):
    """The excluded document is dense in the expansion term and short.

    At a high enough weight it would rank **first** if it were admitted at all,
    which is what makes this a guard rather than a technicality.
    """
    expansion = _expansion("alpha", "omega", 50.0)
    ids = [r.id for r in scan.ask(built, "alpha", top=50, expansion=expansion)]
    assert "file:omega-only.md" not in ids
    assert ids[0] == "file:both.md", "the expansion should still lift a document that answers the query"


# -- 3. the expansion does something -----------------------------------------


def test_an_expansion_lifts_a_document_that_matches_it(built):
    """The fixture must be able to move, or the tests above pass vacuously."""
    plain = [r.id for r in scan.ask(built, "alpha", top=10)]
    assert plain[0] == "file:alpha-only.md", "precondition: without the expansion, alpha-only wins"

    expanded = [r.id for r in scan.ask(built, "alpha", top=10, expansion=_expansion("alpha", "omega", 0.2))]
    assert expanded[0] == "file:both.md", "the expansion term must be able to reorder"


def test_the_weight_is_monotone(built):
    """More weight, more lift — the knob has to mean something."""
    scores = []
    for weight in (0.05, 0.2, 1.0, 5.0):
        results = scan.ask(built, "alpha", top=10, expansion=_expansion("alpha", "omega", weight))
        scores.append(next(r.score for r in results if r.id == "file:both.md"))
    assert scores == sorted(scores), scores


# -- 4. the object itself ----------------------------------------------------


def test_expansion_none_requires_everything():
    e = Expansion.none(["a", "b"])
    assert e.trivial and e.required == {"a", "b"} and e.weights == {}
    assert e.matches({"a": [1]}) and not e.matches({"z": [1]})


def test_build_keeps_original_terms_first():
    """Hash order is the score summation order, and the summation order is a
    float fact — the original terms lead so an expansion cannot reorder the
    arithmetic of the query it supplements."""
    e = build_expansion(["a", "b"], ["c", "a"], 0.2)
    assert e.hashes == ("a", "b", "c")
    assert e.weights == {"c": 0.2}
    assert e.required == {"a", "b"}
