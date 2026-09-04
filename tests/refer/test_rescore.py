"""Passage scoring — one scorer, and it is the index's."""

from __future__ import annotations

import ast
import inspect
import sys

from fux.refer._chunk import Passage, chunk
from fux.refer._rescore import rescore

# `fux.refer` re-exports the `rescore` *function*, which shadows the submodule
# of the same name on the package, so the module is taken from the registry.
import fux.refer._rescore  # noqa: E402  (imported for the registry entry below)

rescore_mod = sys.modules["fux.refer._rescore"]


def _doc(text: str):
    return [("file:a.md", "a.md", "sha", chunk(text))]


def test_the_passage_that_matches_scores_highest():
    body = lambda w: (w + " ") * 40
    text = f"# Storage\n\n{body('storage')}\n\n## Capacity\n\n{body('capacity throughput')}"
    scored = rescore("capacity throughput", _doc(text))
    assert scored[0].passage.heading == "Capacity"


def test_a_nonmatching_passage_scores_zero():
    body = lambda w: (w + " ") * 40
    text = f"# Storage\n\n{body('storage')}\n\n## Catering\n\n{body('espresso')}"
    scored = rescore("espresso", _doc(text))
    assert scored[0].passage.heading == "Catering"
    assert scored[-1].score == 0.0


def test_results_are_sorted_and_tie_break_on_the_locator():
    body = lambda w: (w + " ") * 40
    text = f"# A\n\n{body('same')}\n\n## B\n\n{body('same')}"
    scored = rescore("same", _doc(text))
    assert [s.score for s in scored] == sorted((s.score for s in scored), reverse=True)
    ties = [s.locator for s in scored if s.score == scored[0].score]
    assert ties == sorted(ties)


def test_the_locator_addresses_the_passage_not_just_the_document():
    scored = rescore("storage", _doc("# Storage\n\n" + ("storage " * 40)))
    # W-76 Phase 5: the locator is a LINE RANGE now, not a passage ordinal.
    # The assertion's intent is unchanged — the locator must address the
    # passage rather than just the document — and a line range addresses it
    # more precisely, which is the whole point of the change.
    assert scored[0].locator == "a.md:L1-L3"


def test_an_empty_query_scores_nothing():
    assert rescore("", _doc("# A\n\n" + ("alpha " * 40))) == []


def test_it_reuses_the_index_scorer_rather_than_defining_a_second():
    """Two scorers is how the index and the refer plane end up disagreeing
    about what 'relevant' means — and the disagreement shows up as an answer
    whose top citation is not from the top document."""
    from fux.query import bm25f

    # Identity, not a string match: this is the actual property — the passage
    # scorer and the index scorer are the same function object.
    assert rescore_mod.score_record is bm25f.score_record

    # And no local reimplementation slipped in beside it.
    tree = ast.parse(inspect.getsource(rescore_mod))
    defined = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert not {"score", "bm25", "idf", "score_record"} & defined, defined


# -- W-108: the proximity multiplier ----------------------------------------


def test_weight_zero_is_byte_identical_to_the_unweighted_score():
    """The byte-identity guarantee `rescore`'s docstring makes.

    `[ranking] rerank_weight` ships at `0.0`, so the default `answer` on an
    unconfigured repo must produce the scores this function produced before
    W-108 existed — not *approximately*, not *to nine places*: the same floats,
    because `_uplift` performs no arithmetic at all below the threshold.
    """
    body = lambda w: (w + " ") * 40
    text = f"# Storage\n\n{body('storage capacity')}\n\n## Catering\n\n{body('capacity espresso')}"
    default = rescore("storage capacity", _doc(text))
    explicit = rescore("storage capacity", _doc(text), weight=0.0)
    assert [s.score for s in default] == [s.score for s in explicit]
    assert [s.locator for s in default] == [s.locator for s in explicit]
    # And the identity is exact, not rounded: these are the same float objects
    # by value, which `==` on the repr would not prove.
    assert [repr(s.score) for s in default] == [repr(s.score) for s in explicit]


def test_a_negative_weight_is_off_rather_than_a_penalty():
    """`<= 0` is off. A knob that starts *demoting* passages below zero is a
    second behaviour hiding behind one number, and `rerank.rerank` reads its
    own weight the same way."""
    body = lambda w: (w + " ") * 40
    text = f"# A\n\n{body('storage capacity')}\n\n## B\n\n{body('capacity')}"
    assert [s.score for s in rescore("storage capacity", _doc(text), weight=-1.0)] == [
        s.score for s in rescore("storage capacity", _doc(text))
    ]


def test_the_passage_that_says_the_query_back_wins_when_the_weight_is_on():
    """The signal BM25 structurally cannot see, isolated.

    Both passages hold the same tokens the same number of times and are the
    same length, so **BM25 scores them exactly equal** (asserted, so this test
    cannot quietly become a length test) and the tie breaks on the locator —
    `Alpha` wins for being higher in the file. Only adjacency separates them:
    `Beta` says *"rollback procedure"*, `Alpha` scatters the two words thirty
    tokens apart. With the weight on, `Beta` wins.
    """
    pad = " ".join(f"pad{i}" for i in range(30))
    text = f"# Alpha\n\nrollback {pad} procedure {pad}\n" + f"\n# Beta\n\n{pad} rollback procedure {pad}\n"
    candidates = [("file:a.md", "a.md", "sha", chunk(text))]

    off = rescore("rollback procedure", candidates)
    assert off[0].score == off[1].score, "the arms must be a BM25 tie, or this tests length"
    assert off[0].passage.heading == "Alpha"

    on = rescore("rollback procedure", candidates, weight=1.0)
    assert on[0].passage.heading == "Beta"


def test_the_multiplier_is_bounded_by_the_weight():
    """A bounded multiplicative uplift, exactly `rerank.rerank`'s shape: a
    perfect proximity match at `weight = w` may at most multiply a score by
    `1 + w`, so a proximity signal can never outrun a real term match by more
    than the caller allowed."""
    body = "the rollback procedure is documented here"
    text = f"# A\n\n{body}\n"
    candidates = [("file:a.md", "a.md", "sha", chunk(text))]
    base = rescore("rollback procedure", candidates)[0].score
    for weight in (0.5, 1.0, 2.0):
        boosted = rescore("rollback procedure", candidates, weight=weight)[0].score
        assert base <= boosted <= base * (1.0 + weight) + 1e-12
