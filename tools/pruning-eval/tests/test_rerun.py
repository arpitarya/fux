"""Harness validity for the five-arm run.

The experiment's whole claim is "the arms differ only in their criterion". That
is only true if retention is actually matched, so these tests target the
machinery that makes it so: the budget calibration, Rule C's cost accounting,
and the no-op identity that proves 100 % retention changes nothing.
"""

from __future__ import annotations

import pytest
from fux.config import BM25FParams

from pruning import rerun
from pruning.selector import FieldCounts

P = BM25FParams()


def _fields(heading=None, path=None, body=None) -> FieldCounts:
    return FieldCounts(heading or {}, path or {}, body or {})


def _corpus(n_docs: int = 40, vocab: int = 200) -> dict[str, FieldCounts]:
    """A corpus with enough vocabulary that a share is a real treatment."""
    out = {}
    for d in range(n_docs):
        body = {f"t{(d * 7 + i) % 900}": 1 + (i % 4) for i in range(vocab)}
        out[f"doc{d:03d}.md"] = _fields(
            heading={f"h{d}": 2, "shared": 1}, path={"docs": 1}, body=body
        )
    return out


PREP = rerun.prepare_models(_corpus(), P, delta=3)


def test_no_pruning_arm_keeps_every_posting():
    ceiling = rerun.ARMS[-1]
    kept = rerun.kept_for(PREP, ceiling, 1.0, 8)
    assert rerun.retention_of(PREP, kept) == 1.0
    for doc_id, terms in kept.items():
        assert terms == PREP.vocab[doc_id]


def test_full_share_is_a_byte_identical_no_op_for_every_arm():
    """100 % retention must reproduce the unpruned index exactly — the identity
    that proves any measured difference is caused by pruning and nothing else."""
    for spec in rerun.ARMS:
        kept = rerun.kept_for(PREP, spec, 1.0, 8)
        assert rerun.retention_of(PREP, kept) == pytest.approx(1.0), spec.label
        for doc_id, terms in kept.items():
            assert terms == PREP.vocab[doc_id], spec.label


@pytest.mark.parametrize("target", [0.06, 0.15, 0.30])
def test_calibration_matches_retention_within_the_validity_tolerance(target):
    """±1 pt is the handoff's validity bar; an unfair comparison is worse than
    no comparison."""
    for spec in rerun.ARMS[:-1]:
        fits = True
        if spec.use_sweep:
            d, fits = rerun.feasible_delta(PREP, target, 3)
            PREP.set_delta(d)
        _share, actual, _kept = rerun.calibrate(PREP, spec, target, 8)
        if fits:
            assert abs(actual - target) <= 0.01, f"{spec.label} at {target}: {actual}"
        else:
            # Rule C's floor cost makes this rung unreachable — the cell must be
            # *flagged*, never quietly compared at a different retention.
            assert actual > target
    PREP.set_delta(3)


def test_retention_is_monotone_in_the_share():
    spec = rerun.ARMS[1]  # impact only
    seen = [rerun.retention_of(PREP, rerun.kept_for(PREP, spec, s, 0))
            for s in (0.0, 0.1, 0.25, 0.5, 1.0)]
    assert seen == sorted(seen)
    assert seen[-1] == pytest.approx(1.0)


def test_rule_c_cost_is_reported_and_delta_steps_down_when_it_would_blow_the_rung():
    cost3 = PREP.sweep_cost(3)
    cost1 = PREP.sweep_cost(1)
    assert cost3 > cost1 > 0
    # A rung far below the sweep's own cost must force δ down.
    tiny = cost1 / 4
    assert rerun.feasible_delta(PREP, tiny, 3) == (1, False)
    # A generous rung keeps the requested δ.
    assert rerun.feasible_delta(PREP, 1.0, 3) == (3, True)


def test_sweeps_are_nested_so_stepping_delta_down_is_a_subset():
    small = PREP.sweep_by_delta[1]
    big = PREP.sweep_by_delta[3]
    for doc_id, terms in small.items():
        assert terms <= big[doc_id]


def test_arm_4_contains_the_spine_and_arm_3_does_too():
    for spec in (rerun.ARMS[2], rerun.ARMS[3]):
        kept = rerun.kept_for(PREP, spec, 0.05, 1)
        for doc_id, terms in kept.items():
            assert PREP.spine[doc_id] <= terms, spec.label


def test_arm_1_and_arm_2_rank_differently():
    """If KL and impact produced the same order, the experiment would be moot."""
    kl = rerun.kept_for(PREP, rerun.ARMS[0], 0.1, 1)
    impact = rerun.kept_for(PREP, rerun.ARMS[1], 0.1, 1)
    assert kl != impact


def test_preparation_is_deterministic_under_document_reordering():
    forward = rerun.prepare_models(_corpus(12, 60), P, delta=2)
    corpus = _corpus(12, 60)
    reversed_corpus = dict(reversed(list(corpus.items())))
    backward = rerun.prepare_models(reversed_corpus, P, delta=2)
    assert forward.order["impact"] == backward.order["impact"]
    assert forward.order["kl"] == backward.order["kl"]
    assert forward.sweep_by_delta[2] == backward.sweep_by_delta[2]
    for spec in rerun.ARMS:
        assert rerun.kept_for(forward, spec, 0.2, 4) == \
            rerun.kept_for(backward, spec, 0.2, 4)
