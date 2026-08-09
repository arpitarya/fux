"""Contract tests for the combined selector (Rules A/B/C).

These travel with the selector into `src/fux/ingest/` — they are its contract,
not the harness's. The two that matter most are Rule C's order-independence
(it is a global sweep, so a set-iteration leak would be invisible until it
changed a committed index) and the budget floor (a share applied to a tiny
document must not round down to nothing).
"""

from __future__ import annotations

import random

import pytest
from fux.config import BM25FParams

from pruning.selector import (
    CollectionModel,
    DocumentModel,
    FieldCounts,
    budget_for,
    build_collection_model,
    heading_spine,
    impacts,
    select_document,
    term_centric_sweep,
)

P = BM25FParams()


def doc(doc_id: str, heading=None, path=None, body=None) -> DocumentModel:
    return DocumentModel(doc_id, FieldCounts(heading or {}, path or {}, body or {}), P)


# A small homogeneous corpus: every document is "about payments", which is the
# condition that broke KL selection in ADR-0002.
CORPUS = [
    doc("webhooks.md", heading={"webhook": 2, "retry": 1}, path={"api": 1},
        body={"webhook": 9, "payments": 4, "retry": 3, "backoff": 2, "jitter": 1}),
    doc("settlement.md", heading={"settlement": 2}, path={"docs": 1},
        body={"settlement": 8, "payments": 5, "ledger": 3, "batch": 2}),
    doc("ledger.md", heading={"ledger": 2}, path={"docs": 1},
        body={"ledger": 9, "payments": 6, "entry": 3, "posting": 2}),
    doc("overview.md", heading={"payments": 3}, path={"docs": 1},
        body={"payments": 12, "webhook": 1, "ledger": 1, "settlement": 1}),
]
MODEL = build_collection_model(CORPUS)


def test_collection_model_is_document_frequency_over_the_unpruned_corpus():
    assert MODEL.n == 4
    assert MODEL.df["payments"] == 4  # in every document
    assert MODEL.df["jitter"] == 1
    assert MODEL.idf("jitter") > MODEL.idf("payments")


def test_rule_a_keeps_every_heading_and_title_term():
    assert heading_spine(CORPUS[0]) == {"webhook", "retry"}
    assert heading_spine(doc("x", heading={})) == set()


def test_budget_is_a_share_with_a_floor_not_a_constant_k():
    big = doc("big", body={f"t{i}": 1 for i in range(1000)})
    small = doc("small", body={"a": 1, "b": 1})
    assert budget_for(big, 0.06, 8) == 60
    assert budget_for(small, 0.06, 8) == 8  # floor wins on a tiny document
    with pytest.raises(ValueError):
        budget_for(big, -0.1, 8)


def test_rule_b_ranks_by_the_scorer_s_own_impact():
    scores = impacts(CORPUS[0], MODEL, P)
    # `webhook` is this document's subject and must outrank the collection-wide
    # `payments` — the exact comparison KL divergence gets backwards.
    assert scores["webhook"] > scores["payments"]


def test_rule_a_rescues_the_subject_term_kl_would_drop():
    """The `webhooks.md` regression, as a test."""
    kept = select_document(CORPUS[0], MODEL, P, share=0.0, floor=1)
    assert "webhook" in kept


def test_spine_larger_than_budget_is_kept_whole_not_truncated():
    d = doc("h", heading={"a": 1, "b": 1, "c": 1, "d": 1}, body={"z": 5})
    kept = select_document(d, MODEL, P, share=0.0, floor=2)
    assert kept == {"a", "b", "c", "d"}


def test_selection_is_deterministic_under_term_reordering():
    shuffled = FieldCounts(
        dict(reversed(list(CORPUS[0].fields.heading.items()))),
        dict(CORPUS[0].fields.path),
        dict(reversed(list(CORPUS[0].fields.body.items()))),
    )
    other = DocumentModel("webhooks.md", shuffled, P)
    assert select_document(CORPUS[0], MODEL, P, share=0.5, floor=1) == \
        select_document(other, MODEL, P, share=0.5, floor=1)


def test_rule_c_is_order_independent():
    """A global sweep is where a set-iteration leak would hide."""
    baseline_kept = {d.doc_id: set() for d in CORPUS}
    term_centric_sweep(CORPUS, baseline_kept, MODEL, P, delta=2)

    rng = random.Random(7)
    for _ in range(5):
        shuffled = CORPUS[:]
        rng.shuffle(shuffled)
        kept = {d.doc_id: set() for d in shuffled}
        term_centric_sweep(shuffled, kept, MODEL, P, delta=2)
        assert kept == baseline_kept


def test_rule_c_guarantees_every_term_survives_in_its_best_documents():
    kept: dict[str, set[str]] = {d.doc_id: set() for d in CORPUS}
    term_centric_sweep(CORPUS, kept, MODEL, P, delta=1)
    # Every term in the corpus is reachable in at least one document.
    reachable = set().union(*kept.values())
    everything = set().union(*(d.vocabulary() for d in CORPUS))
    assert reachable == everything


def test_rule_c_reports_what_it_added_so_retention_is_not_assumed():
    kept = {d.doc_id: set(d.vocabulary()) for d in CORPUS}  # nothing to add
    assert term_centric_sweep(CORPUS, kept, MODEL, P, delta=3) == 0
    empty = {d.doc_id: set() for d in CORPUS}
    assert term_centric_sweep(CORPUS, empty, MODEL, P, delta=1) > 0
    assert term_centric_sweep(CORPUS, empty, MODEL, P, delta=0) == 0


def test_rule_c_breaks_impact_ties_on_document_id():
    twins = [
        doc("b.md", body={"same": 3}),
        doc("a.md", body={"same": 3}),
    ]
    model = build_collection_model(twins)
    kept = {d.doc_id: set() for d in twins}
    term_centric_sweep(twins, kept, model, P, delta=1)
    assert kept["a.md"] == {"same"} and kept["b.md"] == set()


def test_empty_document_selects_nothing():
    assert select_document(doc("empty"), MODEL, P, share=0.5, floor=8) == set()


def test_full_share_keeps_everything():
    for d in CORPUS:
        assert select_document(d, MODEL, P, share=1.0, floor=0) == d.vocabulary()


def test_arm_switches_produce_the_expected_rule_sets():
    d = CORPUS[0]
    impact_only = select_document(d, MODEL, P, share=0.4, floor=1, use_spine=False)
    combined = select_document(d, MODEL, P, share=0.4, floor=1, use_spine=True)
    assert heading_spine(d) <= combined
    assert len(impact_only) <= len(combined) + len(heading_spine(d))


def test_custom_scorer_shares_the_same_code_path():
    """Arm 1 (KL) must differ from arm 2 only in the ranking function."""
    def reverse_alpha(document, collection, params):  # noqa: ARG001
        return {t: float(-ord(t[0])) for t in document.vocabulary()}

    kept = select_document(CORPUS[0], MODEL, P, share=0.4, floor=1,
                           use_spine=False, scorer=reverse_alpha)
    assert kept and kept != select_document(CORPUS[0], MODEL, P, share=0.4, floor=1,
                                            use_spine=False)


def test_collection_model_rejects_nothing_silently():
    model = CollectionModel({}, 0, 0.0)
    assert model.avg_wlen == 1.0
    assert model.idf("anything") > 0
