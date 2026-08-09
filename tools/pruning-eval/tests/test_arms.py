"""Harness self-checks — the ones that decide whether any number is believable.

Two invariants carry the experiment:

1. the baseline arm is **exactly** what the archived `Searcher` builds, so
   "we changed only the index" is a fact rather than an intention; and
2. pruning with `k=∞` is a **no-op**, so any difference between arms is
   attributable to pruning and nothing else.

Both are asserted against the archived engine's own code path, not against a
recorded expectation.
"""

from __future__ import annotations

from fux.config import BM25FParams
from fux.index.bm25f import Searcher, tokenize

from pruning import arms, metrics
from pruning.kl_select import build_collection_model

PARAMS = BM25FParams()

FILES = {
    "docs/guide.md": {
        "title": "Deployment Guide",
        "chunks": [
            {"heading": "Install", "text": "install the widget service with the installer",
             "start": 1, "end": 4},
            {"heading": "Deploy", "text": "roll back a failed release within five minutes",
             "start": 5, "end": 9},
        ],
    },
    "docs/runbook.md": {
        "title": "Runbook",
        "chunks": [
            {"heading": "Rollback", "text": "the rollback procedure reverts the release",
             "start": 1, "end": 6},
        ],
    },
    "notes/zeta.md": {
        "title": "Zeta",
        "chunks": [{"heading": "Notes", "text": "unrelated prose about widgets",
                    "start": 1, "end": 2}],
    },
}

QUERIES = ["rollback release", "install the widget service", "widgets", "five minutes"]


def _reference() -> Searcher:
    return Searcher(FILES, PARAMS)


def test_baseline_arm_matches_the_archived_searcher_exactly():
    ref = _reference()
    arm, stats = arms.build_arm(FILES, PARAMS)

    assert len(arm.chunks) == len(ref.chunks)
    assert [c["file"] for c in arm.chunks] == [c["file"] for c in ref.chunks]
    assert [c["wlen"] for c in arm.chunks] == [c["wlen"] for c in ref.chunks]
    assert arm.avg_wlen == ref.avg_wlen
    assert dict(arm.postings) == dict(ref.postings)
    assert stats.chunks == len(ref.chunks)

    for q in QUERIES:
        assert metrics.rank_documents(arm, q) == metrics.rank_documents(ref, q)


def test_k_infinity_pruning_is_a_no_op():
    doc_tf = arms.document_term_frequencies(FILES)
    model = arms.collection_model_for(doc_tf)
    kept = arms.kept_terms_by_doc(doc_tf, model, None)

    ref = _reference()
    arm, _ = arms.build_arm(FILES, PARAMS, kept=kept)

    assert dict(arm.postings) == dict(ref.postings)
    assert arm.avg_wlen == ref.avg_wlen
    for q in QUERIES:
        assert metrics.rank_documents(arm, q) == metrics.rank_documents(ref, q)


def test_identical_arms_are_byte_reproducible():
    """Two independent builds of the same arm must be indistinguishable."""
    a, _ = arms.build_arm(FILES, PARAMS)
    b, _ = arms.build_arm(FILES, PARAMS)
    for q in QUERIES:
        assert metrics.rank_documents(a, q) == metrics.rank_documents(b, q)
    assert dict(a.postings) == dict(b.postings)


def test_pruning_recomputes_df_and_lengths_rather_than_borrowing_them():
    """The correctness point the whole experiment turns on.

    With `stats=None` the archived scorer derives `df` from posting-list length
    and `avg_wlen` from the lengths it holds — so a pruned arm reports *pruned*
    statistics, which is the production definition. The `diag` arm proves the
    two really differ, otherwise the distinction would be untestable.
    """
    doc_tf = arms.document_term_frequencies(FILES)
    model = arms.collection_model_for(doc_tf)
    kept = arms.kept_terms_by_doc(doc_tf, model, 3)

    ref = _reference()
    pruned, _ = arms.build_arm(FILES, PARAMS, kept=kept)
    assert pruned.stats is None
    assert pruned.avg_wlen < ref.avg_wlen  # lengths shrank with the postings

    dropped = [t for t in ref.postings if t not in pruned.postings]
    assert dropped, "k=3 on this corpus must drop something, or the test is vacuous"

    # The statistic the scorer actually consumes must have moved. `df` over the
    # pruned index counts only documents in which the term *survived*.
    assert arms.baseline_df(pruned) != arms.baseline_df(ref)
    assert sum(len(p) for p in pruned.postings.values()) < \
        sum(len(p) for p in ref.postings.values())

    diag, _ = arms.build_arm(
        FILES, PARAMS, kept=kept,
        stats=arms.BorrowedStats(len(ref.chunks), ref.avg_wlen, arms.baseline_df(ref)),
    )
    assert diag.stats is not None
    assert diag.stats.df_of(dropped[0]) == len(ref.postings[dropped[0]])
    # Same postings, different statistics → different scores. If these matched,
    # the diagnostic arm would be measuring nothing.
    q = "rollback release"
    assert metrics.rank_documents(diag, q) != metrics.rank_documents(pruned, q) or \
        [s for _, s in metrics.rank_documents(diag, q)] != \
        [s for _, s in metrics.rank_documents(pruned, q)]


def test_prune_coverage_reports_no_op_documents_honestly():
    doc_tf = arms.document_term_frequencies(FILES)
    pruned_docs, total = arms.prune_coverage(doc_tf, 10_000)
    assert (pruned_docs, total) == (0, len(FILES))
    pruned_docs, total = arms.prune_coverage(doc_tf, 1)
    assert pruned_docs == len(FILES)
    assert arms.prune_coverage(doc_tf, None) == (0, len(FILES))


def test_document_term_frequencies_count_path_tokens_once():
    doc_tf = arms.document_term_frequencies(FILES)
    # `docs` occurs only as a path token, and guide.md has two chunks — so a
    # count of 1 is the proof that path tokens are not counted per chunk.
    assert doc_tf["docs/guide.md"]["docs"] == 1
    # `guide` = 1 path token + the title once per chunk (the title is part of
    # the heading field), which is the archived Searcher's own accounting.
    assert doc_tf["docs/guide.md"]["guide"] == 3
    # Body and heading terms accumulate across chunks.
    assert doc_tf["docs/runbook.md"]["rollback"] >= 2


def test_collection_model_is_built_from_unpruned_documents():
    doc_tf = arms.document_term_frequencies(FILES)
    model = arms.collection_model_for(doc_tf)
    direct = build_collection_model([doc_tf[k] for k in sorted(doc_tf)])
    assert model.total_tokens == direct.total_tokens
    assert model.cf("release") == direct.cf("release")


class _FakeIndex:
    """A postings map is all `rare_term_slice` reads — no need for a real arm."""

    def __init__(self, df: dict[str, int]):
        self.postings = {t: [None] * n for t, n in df.items()}


def test_rare_term_slice_is_the_bottom_tercile_by_minimum_df():
    index = _FakeIndex({"common": 900, "mid": 50, "rare": 2, "rarest": 1})
    queries = ["common mid", "common rarest", "common rare", "mid"]
    keys, degenerate = metrics.rare_term_slice(queries, index, tokenize)
    assert not degenerate
    assert len(keys) == 2  # ceil(4/3)
    # Ranked by minimum term df ascending: rarest(1) then rare(2).
    assert keys == ["common rarest", "common rare"]


def test_rare_term_slice_flags_a_degenerate_slice_rather_than_passing_it():
    index = _FakeIndex({"a": 3, "b": 3})
    keys, degenerate = metrics.rare_term_slice(["a", "b", "a b"], index, tokenize)
    assert degenerate
    assert len(keys) == 1


def test_rare_term_slice_is_deterministic_under_query_reordering():
    index = _FakeIndex({"common": 900, "mid": 50, "rare": 2, "rarest": 1})
    queries = ["common mid", "common rarest", "common rare", "mid"]
    first, _ = metrics.rare_term_slice(queries, index, tokenize)
    second, _ = metrics.rare_term_slice(list(reversed(queries)), index, tokenize)
    assert first == second


def test_metric_definitions_match_the_pre_registration():
    assert metrics.score_queries([1, 3, 6, None]) == {
        "hit@5": round(2 / 4, 6),
        "P@10": round((3 / 10) / 4, 6),
        "MRR": round((1 + 1 / 3 + 1 / 6) / 4, 6),
        "n": 4,
    }
    # Beyond the declared MRR depth the reciprocal rank is zero, not 1/rank.
    assert metrics.score_queries([metrics.MRR_DEPTH + 1])["MRR"] == 0.0
