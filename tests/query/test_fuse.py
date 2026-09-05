"""W-109 — `-q` multi-query fusion, in rank space only.

RRF was **deleted** with the dense lane on 2026-08-25 and comes back under a
record ([ADR-PORT-LIST](../../docs/adr/0015_port-list.md) rule 1). These tests
pin the two things that make the revival a different object from the deleted
one: it never touches a score, and its constant is Cormack's rather than one
this repo picked.
"""

from __future__ import annotations

import dataclasses

from fux.query.fuse import K, fuse_results, rrf


@dataclasses.dataclass(frozen=True)
class _R:
    id: str
    loc: str = ""
    score: float = 0.0


def _ids(results):
    return [r.id for r in results]


def test_k_is_cormacks_constant():
    """`60`, from the 2009 paper. **Not a `tune.toml` key**: a knob on a
    published constant measured across TREC collections, tuned on ten
    documents, is how a default gets worse with evidence attached."""
    assert K == 60


def test_a_document_in_both_lists_beats_a_document_first_in_one():
    """The whole point of fusion, and the behaviour that surprises people.

    `b` is second in both arms; `a` is first in one and absent from the other.
    RRF prefers `b` — two pieces of weak agreement over one strong claim — and
    that is the property Cormack measured, not an artefact.
    """
    fused = fuse_results([[_R("a"), _R("b")], [_R("c"), _R("b")]], top=3)
    assert _ids(fused)[0] == "b"


def test_absence_is_silence_and_not_a_penalty():
    """A short list must not punish the documents it omits.

    Scoring absence would make an arm that returned five results damage a
    document more than an arm that returned fifty — a fusion whose outcome
    depends on how deep each arm happened to retrieve.
    """
    scores = rrf([["a", "b"], ["a"]])
    assert scores["a"] == 2 / (K + 1)
    assert scores["b"] == 1 / (K + 2)


def test_ties_break_on_the_id_never_on_arm_order():
    """Same corpus, same queries, same bytes — on every machine.

    `x` and `y` are symmetric across the two arms, so their fused scores are
    equal and only the tie-break separates them.
    """
    forward = fuse_results([[_R("y"), _R("x")], [_R("x"), _R("y")]], top=2)
    reverse = fuse_results([[_R("x"), _R("y")], [_R("y"), _R("x")]], top=2)
    assert _ids(forward) == _ids(reverse) == ["x", "y"]


def test_one_arm_is_returned_untouched():
    """A single `-q` is not a fusion, and must not be scored as one.

    Fusing one list would replace every BM25F score with a reciprocal rank —
    changing what `score` means on a query nobody fused.
    """
    arm = [_R("a", score=7.5), _R("b", score=2.25)]
    assert fuse_results([arm], top=5) == arm


def test_the_result_object_comes_from_the_arm_that_ranked_it_best():
    """`loc`, `title` and the rest must be a real document's, not a merge.

    Only `score` is replaced — the rest of the record is taken from the arm
    that ranked it highest, so a citation a caller acts on came from somewhere.
    """
    fused = fuse_results([[_R("a", loc="second.md")], [_R("a", loc="first.md"), _R("z")]], top=2)
    winner = next(r for r in fused if r.id == "a")
    assert winner.loc == "second.md", "rank 0 in arm one beats rank 0 in arm two only on order"
    assert winner.score == rrf([["a"], ["a", "z"]])["a"]


def test_nothing_is_fused_in_score_space():
    """The deleted lane's defect, asserted as an absence.

    Arm one's scores are enormous and arm two's are tiny. If anything summed
    values rather than ranks, `big` would win; it does not, because nothing
    here ever reads `score` on the way in.
    """
    fused = fuse_results(
        [[_R("big", score=1e9), _R("small", score=1e-9)],
         [_R("small", score=1e-9), _R("big", score=1e9)]],
        top=2,
    )
    assert sorted(_ids(fused)) == ["big", "small"]
    assert all(r.score < 1.0 for r in fused), "a BM25F score leaked into a fused result"
