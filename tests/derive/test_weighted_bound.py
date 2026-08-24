"""W-73 layer 2: the pruning bound must survive a NON-DEFAULT score weight.

Layer 1 is the algebra in `query/rank.py::Weighting`. Layer 3 is
`tools/differential/run.py --weights`, which sweeps the weight over the whole
query set. **This layer is the one that fails loudly on the exact
configuration a uniform sweep will essentially never generate**: the largest
configured weight sitting on the *lowest-impact* document in a block.

Why that case and not a random one. The bound is
`w(d) * S(d) <= maximum * ceiling`, and `ceiling` is a maximum some posting
actually attains, so it is tight. A document whose own contribution is far
below its block's `mx` has slack; promoting it consumes that slack. Only when
the promoted document is the *weakest* in its block does the unweighted
ceiling fall below the weighted score it must dominate — which is the
divergence, and it is silent: no exception, no short read, just a document
the scan returns and the accelerator does not.

Both directions are tested because both diverge, for different reasons:

- `w > 1` — a promoted document is skipped on a ceiling that never knew about
  the promotion.
- `w < 1` — demoting the current top-k lowers the real threshold, so a
  document pruned on the old `theta` should now enter.
"""

from __future__ import annotations

import pytest

from fux.derive import accel, build
from fux.query import scan
from fux.store import term_hash, write_index


def _rec(doc_id, title, flen, terms, *, archived=False) -> dict:
    record = {
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
    if archived:
        record["archived"] = True
    return record


def _adversarial_corpus(n_docs: int = 600) -> list[dict]:
    """One archived weakling per block, buried under strong non-archived docs.

    Three properties the corpus must have, each of which a naive fixture gets
    wrong:

    1. **The shared term must have real `idf`.** A term present in *every*
       document has `idf` ~ 0, so every score is ~0 and no finite weight
       reorders anything — the test then passes while testing nothing.
       `alpha` is therefore in half the corpus.
    2. **The archived documents must be the weakest posting in their block** —
       minimum tf, maximum `wlen` — because the block bound is tight and it is
       exactly that slack the weight has to eat before the bound breaks.
    3. **Something else must set a high `theta`.** `beta` is rare and strong,
       so the candidate set fills with live documents and the threshold the
       archived documents have to clear is a real one.

    tf vectors are `[body, heading]` (v2 order — `store.TF_FIELDS`); each
    `flen` is a single body-token count, so `derive_wlen(flen) == flen[0]`.
    """
    records = []
    alpha, beta = term_hash("alpha"), term_hash("beta")
    for i in range(n_docs):
        if i % 25 == 0:
            # Archived: has `alpha` at the floor, and is very long.
            records.append(
                _rec(f"file:retired/doc{i:04d}.md", f"Retired {i}", [3000], {alpha: [1, 0]}, archived=True)
            )
            continue
        terms = {}
        if i % 2 == 1:
            terms[alpha] = [8 + i % 13, 1 + i % 4]
        if i % 10 == 3:
            terms[beta] = [5, 2]
        if not terms:
            terms[term_hash(f"filler{i}")] = [2, 0]
        records.append(_rec(f"file:live/doc{i:04d}.md", f"Live {i}", [80 + (i * 13) % 220], terms))
    return records


@pytest.fixture
def built(tmp_path):
    write_index(tmp_path, _adversarial_corpus())
    build(tmp_path)
    return tmp_path


ARCHIVED_DIRS = frozenset({"retired"})

#: Spanning both directions and both sides of 1.0, plus values large enough to
#: overcome the slack a real corpus leaves. A weight of 1.01 does not test the
#: bound; it tests floating point.
WEIGHTS = (0.1, 0.25, 0.5, 0.9, 1.0, 1.5, 4.0, 25.0, 500.0)
TOPS = (1, 5, 20, 50)


def _payload(results):
    return [(r.id, round(r.score, 9), r.archived) for r in results]


@pytest.mark.parametrize("weight", WEIGHTS)
@pytest.mark.parametrize("top", TOPS)
def test_accelerator_equals_scan_at_any_weight(built, weight, top):
    """The differential law, stated at the weight rather than at the default.

    This is the assertion W-44's row claimed was already true — *"the
    differential law carries it down both the scan and accelerator paths for
    free"* — which held at `1.0` and at no other value.
    """
    expected = _payload(
        scan.ask(built, "alpha beta", top=top, archived_weight=weight, archived_dirs=ARCHIVED_DIRS)
    )
    for skipping in (False, True):
        got = _payload(
            accel.ask(
                built,
                "alpha beta",
                top=top,
                skipping=skipping,
                archived_weight=weight,
                archived_dirs=ARCHIVED_DIRS,
            )
        )
        assert got == expected, f"weight={weight} top={top} skipping={skipping}"


def test_promotion_actually_reorders_this_corpus():
    """The fixture must be able to fail — a test that cannot diverge is green
    for the wrong reason.

    Asserts the weight genuinely moves an archived document into the top-k
    here. Without this, `test_accelerator_equals_scan_at_any_weight` could pass
    on a corpus where the weight never mattered, which is exactly how the
    original defect survived thousands of comparisons.
    """
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_index(root, _adversarial_corpus())
        build(root)
        at_default = scan.ask(root, "alpha beta", top=20, archived_weight=1.0, archived_dirs=ARCHIVED_DIRS)
        promoted = scan.ask(root, "alpha beta", top=20, archived_weight=500.0, archived_dirs=ARCHIVED_DIRS)
        assert not any(r.archived for r in at_default), "fixture: archived already in top-20 at default"
        assert any(r.archived for r in promoted), "fixture: weight never reorders — nothing is under test"


def test_skipping_is_still_load_bearing_at_a_weight(built):
    """Skipping must remain lossless *and* still skip.

    A fix that restores correctness by never skipping is not a fix — it
    silently converts the accelerator into the scan. Asserts the skip path is
    actually taken by checking it reads fewer blocks than the no-skip path.
    """
    from fux.derive.accel import Runtime, accel_candidates
    from fux.query.rank import Weighting
    from fux.query.scan import query_term_hashes

    runtime = Runtime(built)
    hashes = query_term_hashes("alpha beta")
    w = Weighting(archived_weight=0.5, archived_dirs=ARCHIVED_DIRS)
    with_skip, _, _ = accel_candidates(runtime, hashes, 5, skipping=True, weighting=w)
    without, _, _ = accel_candidates(runtime, hashes, 5, skipping=False, weighting=w)
    assert len(with_skip) < len(without), "skipping never fired — the bound is not load-bearing"


def test_maximum_is_the_configuration_not_the_candidates():
    """`Weighting.maximum` must include `1.0`, always.

    A demoting configuration (`w < 1`) has a supremum of `1.0`, not of `w`:
    every non-archived document is scaled by `1.0`. Taking the configured
    weight alone would shrink the ceiling below the scores it must dominate,
    and the demotion direction is the one that looks harmless.
    """
    from fux.query.rank import Weighting

    assert Weighting(archived_weight=0.25).maximum == 1.0
    assert Weighting(archived_weight=4.0).maximum == 4.0
    assert Weighting().trivial is True
    assert Weighting(archived_weight=0.25).trivial is False
