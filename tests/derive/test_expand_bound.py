"""W-109 layer 2 — the pruning bound must survive PER-TERM weights.

`tests/derive/test_weighted_bound.py` is the same defect one level up: a
*document* weight (`archived_weight`) with an unweighted ceiling. This is the
same shape with a *term* weight, and it is worth its own file because the
arithmetic differs — a document weight scales the whole score, a term weight
scales one summand, and the fix is in a different place (`block_bound`'s caller
rather than the ceiling's final multiply).

**Why it can break, and silently.** `_cannot_reach` sums each deferred term's
best block bound and skips the rest when that sum cannot reach `theta`. If the
sum prices an expansion term at its full base contribution while `rank()` scores
it at `0.2` of that, the ceiling is too *high* — which skips too *little*, so
the accelerator is merely slow. The dangerous direction is the other one:
`expand_weight > 1` scores a term **higher** than the ceiling admits, and then
the accelerator skips a block holding a document the scan returns. No exception,
no short read — just a different answer on `--fast`.

Both directions are tested, and `>= 1` is included deliberately: `expand_weight`
is a `tune.toml` key with no upper bound (`_non_negative`), so a consumer can
set it to 5 and there is no code path that stops them.
"""

from __future__ import annotations

import pytest

from fux.derive import accel, build
from fux.query import scan
from fux.query.expand import build as build_expansion
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


def _adversarial_corpus(n_docs: int = 600) -> list[dict]:
    """THREE terms, because two cannot exercise the bound at all.

    🔴 **The first version of this fixture proved nothing, and the reason is
    worth keeping.** With one required term and one expansion term, the
    required term is opened first (rarest-first) and every returnable document
    is already a candidate — so skipping the expansion term's blocks can only
    lose documents that match *no* required term, and `rank()`'s guard drops
    those anyway. Deleting the weight scaling entirely left all 26 assertions
    green. A differential test that cannot fail is worse than none.

    What makes it load-bearing is a **required term on the deferred side**:

    - `alpha` — required, rarest, opened first, fills the candidate set and
      sets a real `theta`.
    - `omega` — the **expansion** term, opened second, and deliberately the
      *strongest* posting in the corpus. Its weighted contribution enters
      `theta`, and it has to dominate an unweighted `theta` or the difference
      between weighted and unweighted never changes a skip decision — which is
      the second way this file passed while proving nothing.
    - `gamma` — required, the most common, **deferred last**, and carried by
      short documents that are genuinely competitive. These are the documents a
      mis-priced ceiling or a mis-weighted `theta` silently loses.

    Both injections are caught: removing the per-term scaling in
    `_cannot_reach`, and dropping `term_weights` from `_kth_score`.
    """
    records = []
    alpha, omega, gamma = term_hash("alpha"), term_hash("omega"), term_hash("gamma")
    for i in range(n_docs):
        terms = {}
        flen = [40 + (i * 17) % 300]
        if i % 90 == 0:                      # rarest: opened first
            terms[alpha] = [7 + i % 5, 1]
        if i % 25 == 0:                      # the expansion term: rare and STRONG
            terms[omega] = [34 + i % 9, 9]
            flen = [50]                      # so it dominates an unweighted theta
        if i % 3 == 0:                       # commonest: deferred last
            terms[gamma] = [14 + i % 5, 4]
            flen = [45]                      # short, so gamma alone competes
        if not terms:
            terms[term_hash(f"filler{i}")] = [2, 0]
        records.append(_rec(f"file:doc{i:04d}.md", f"Doc {i}", flen, terms))
    return records


def _ceiling_corpus(n_docs: int = 600) -> list[dict]:
    """The same three roles, tuned so the CEILING is the load-bearing half.

    🔴 **Two corpora, because one cannot catch both defects.** The shapes pull
    in opposite directions: `theta` bites when the expansion term dominates the
    *opened* side, and the ceiling bites when it sits on the *deferred* side
    beside a required term. A single fixture tuned for one leaves the other
    injection green — verified by injecting each defect against each corpus,
    which is the only way to know a differential test is not decorative.

    Here `omega` is middling rather than dominant, so it is still deferred
    alongside `gamma` when the skip test runs and its bound has to be priced.
    """
    records = []
    alpha, omega, gamma = term_hash("alpha"), term_hash("omega"), term_hash("gamma")
    for i in range(n_docs):
        terms = {}
        flen = [40 + (i * 17) % 300]
        if i % 60 == 0:
            terms[alpha] = [9 + i % 7, 2]
        if i % 7 == 0:
            terms[omega] = [10 + i % 9, 3]
        if i % 3 == 0:
            terms[gamma] = [14 + i % 5, 4]
            flen = [45]
        if not terms:
            terms[term_hash(f"filler{i}")] = [2, 0]
        records.append(_rec(f"file:doc{i:04d}.md", f"Doc {i}", flen, terms))
    return records


CORPORA = {"theta-shaped": _adversarial_corpus, "ceiling-shaped": _ceiling_corpus}


@pytest.fixture(params=sorted(CORPORA), ids=sorted(CORPORA))
def built(tmp_path, request):
    write_index(tmp_path, CORPORA[request.param]())
    build(tmp_path)
    return tmp_path


#: Both sides of 1.0, and values far enough from it to eat a real block's
#: slack. `1.01` would test floating point, not the bound.
WEIGHTS = (0.05, 0.2, 0.5, 1.0, 2.0, 5.0, 40.0, 500.0)
TOPS = (1, 5, 20)


def _payload(results):
    return [(r.id, round(r.score, 9)) for r in results]


QUERY = "alpha gamma"


def _expansion(weight: float):
    return build_expansion(
        scan.query_term_hashes(QUERY), scan.query_term_hashes("omega"), weight
    )


@pytest.mark.parametrize("weight", WEIGHTS)
@pytest.mark.parametrize("top", TOPS)
def test_accelerator_equals_scan_at_any_expand_weight(built, weight, top):
    """The differential law, stated at the expansion weight rather than at 0."""
    expansion = _expansion(weight)
    expected = _payload(scan.ask(built, QUERY, top=top, expansion=expansion))
    for skipping in (False, True):
        got = _payload(accel.ask(built, QUERY, top=top, skipping=skipping, expansion=expansion))
        assert got == expected, f"expand_weight={weight} top={top} skipping={skipping}"


def test_skipping_is_still_load_bearing(built):
    """A bound so loose that nothing is ever skipped would pass every
    assertion above while proving nothing about the bound.

    Assert the accelerator *does* skip: with skipping on, the candidate set is
    strictly smaller than with it off, at the default weight.
    """
    from fux.derive.accel import Runtime, accel_candidates

    runtime = Runtime(built)
    expansion = _expansion(0.2)
    hashes = list(expansion.hashes)
    with_skip, _, _ = accel_candidates(runtime, hashes, 5, skipping=True, expansion=expansion)
    without, _, _ = accel_candidates(runtime, hashes, 5, skipping=False, expansion=expansion)
    assert len(with_skip) < len(without), (
        "nothing was skipped, so this file's other assertions cannot fail — "
        "the fixture no longer exercises the bound"
    )


def test_the_weight_actually_reorders_this_corpus(built):
    """The fixture must be able to diverge, or every test here is vacuous."""
    low = [r.id for r in scan.ask(built, QUERY, top=5, expansion=_expansion(0.05))]
    high = [r.id for r in scan.ask(built, QUERY, top=5, expansion=_expansion(40.0))]
    assert low != high, "no weight in range reorders this corpus"


# -- the third defect, pinned directly ---------------------------------------


def test_theta_is_computed_at_the_expansion_weights():
    """`_kth_score` must price expansion terms at their weight.

    ⚠ **Asserted directly rather than differentially, and the reason is
    recorded because it is a real limit.** Deleting `term_weights` from
    `_kth_score` leaves **both** corpora above green: at `expand_weight < 1` an
    unweighted `theta` is too *high*, which skips too much — and once the guard
    excludes expansion-only candidates, neither corpus's top `k` is carried by
    documents that hold the expansion term at all, so the two thetas coincide.
    **A defect no fixture caught is still a defect**, so it is pinned on the
    function with inputs built for it instead of hunted through a corpus.

    Every candidate here holds the expansion term, which is the case a corpus
    has to stumble into and a unit test can simply state.
    """
    from fux.derive.accel import _kth_score
    from fux.query.rank import Corpus

    alpha, omega = term_hash("alpha"), term_hash("omega")
    expansion = build_expansion([alpha], [omega], 0.05)

    hits = {i: {alpha: [3, 1], omega: [30, 8]} for i in range(10)}
    docs = [{"id": f"file:d{i}.md", "flen": [60]} for i in range(10)]
    corpus = Corpus(n=400, total_wlen=400 * 90.0, newest_mtime=0)
    common = dict(
        hits=hits, docs=docs, opened_order=[alpha, omega],
        df={alpha: 20, omega: 40}, corpus=corpus, top=5, avg_wlen=corpus.avg_wlen,
    )

    weighted = _kth_score(**common, expansion=expansion)
    unweighted = _kth_score(**common, expansion=None)
    assert weighted is not None and unweighted is not None
    assert weighted < unweighted, (
        "theta was not discounted by the expansion weight — an unweighted "
        "threshold at expand_weight < 1 is too high and skips too much"
    )


def test_theta_excludes_candidates_the_guard_will_drop():
    """The defect the differential arms DID catch, stated as the property.

    A candidate matching only expansion terms is discarded by `rank()`, so
    letting it set `theta` raises the threshold on the strength of a document
    nobody will be shown.
    """
    from fux.derive.accel import _kth_score
    from fux.query.rank import Corpus

    alpha, omega = term_hash("alpha"), term_hash("omega")
    expansion = build_expansion([alpha], [omega], 1.0)

    real = {i: {alpha: [3, 1]} for i in range(5)}
    # Five documents that are dense in the expansion term and match nothing
    # the user asked for. `rank()` drops every one of them.
    ghosts = {100 + i: {omega: [60, 20]} for i in range(5)}
    docs = [{"id": f"file:d{i}.md", "flen": [60]} for i in range(200)]
    corpus = Corpus(n=400, total_wlen=400 * 90.0, newest_mtime=0)
    common = dict(
        docs=docs, opened_order=[alpha, omega],
        df={alpha: 20, omega: 40}, corpus=corpus, top=5, avg_wlen=corpus.avg_wlen,
    )

    with_ghosts = _kth_score(hits={**real, **ghosts}, **common, expansion=expansion)
    without = _kth_score(hits=real, **common, expansion=expansion)
    assert with_ghosts == without, (
        "an expansion-only candidate set theta — the accelerator will skip "
        "blocks on the strength of a document rank() discards"
    )
