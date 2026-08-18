"""The five-arm, retention-matched experiment.

P1-GATE failed because "k=128" meant different things on different documents.
This module fixes the *treatment strength* instead: every arm is calibrated to
keep the same fraction of postings, so a difference between arms is a
difference between **criteria** and nothing else. Comparing criteria at a fixed
k would repeat P1-GATE's error one level up.

Retention is measured as kept `(document, term)` pairs over total pairs —
the quantity the paper's §5 size model is denominated in.

Calibration is cheap because selection is *monotone in the budget*: rank a
document's terms once, and the kept set at any budget is a prefix of that
ranking (plus the spine, plus Rule C's fixed additions). So each arm ranks
every document once, then binary-searches a scalar. Rule C's additions are
independent of the budget — a term's top-δ documents are fixed by the corpus —
so the sweep is computed once per corpus, not once per rung.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from .kl_select import build_collection_model as build_kl_model
from .kl_select import term_scores as kl_term_scores
from .selector import (
    CollectionModel,
    DocumentModel,
    build_collection_model,
    heading_spine,
    impacts,
)

__all__ = ["ArmSpec", "ARMS", "PreparedCorpus", "prepare_models", "calibrate", "kept_for"]


class ArmSpec:
    """One arm: which rules it uses, and how it ranks a document's terms."""

    __slots__ = ("key", "label", "rules", "use_spine", "ranker", "use_sweep", "question")

    def __init__(self, key: str, label: str, rules: str, *, use_spine: bool,
                 ranker: str, use_sweep: bool, question: str):
        self.key = key
        self.label = label
        self.rules = rules
        self.use_spine = use_spine
        self.ranker = ranker  # "kl" | "impact" | "none"
        self.use_sweep = use_sweep
        self.question = question


ARMS = (
    ArmSpec("1", "KL only", "—", use_spine=False, ranker="kl", use_sweep=False,
            question="continuity with P1-GATE"),
    ArmSpec("2", "impact only", "B", use_spine=False, ranker="impact", use_sweep=False,
            question="is KL the defect, or pruning itself?"),
    ArmSpec("3", "A + B", "A+B", use_spine=True, ranker="impact", use_sweep=False,
            question="does the heading floor alone fix it?"),
    ArmSpec("4", "A + B + C", "A+B+C", use_spine=True, ranker="impact", use_sweep=True,
            question="the proposed selector"),
    ArmSpec("5", "no pruning", "—", use_spine=False, ranker="none", use_sweep=False,
            question="the quality ceiling / fallback"),
)


class PreparedCorpus:
    """Everything the arms need, computed once per corpus.

    ``order[arm_ranker][doc_id]`` is the document's non-spine terms in the order
    a budget would consume them — the whole reason calibration is affordable.
    """

    __slots__ = ("docs", "collection", "spine", "order", "vocab", "total_postings",
                 "sweep_by_delta", "sweep_additions", "delta")

    def __init__(self, docs, collection, spine, order, vocab, total_postings,
                 sweep_by_delta, delta):
        self.docs = docs
        self.collection = collection
        self.spine = spine
        self.order = order
        self.vocab = vocab
        self.total_postings = total_postings
        self.sweep_by_delta = sweep_by_delta
        self.set_delta(delta)

    def set_delta(self, delta: int) -> None:
        """Select which precomputed sweep is in force.

        Rule C's cost is `δ × |vocabulary|` postings, which is a *fixed* number
        — so as a share of the index it grows as the corpus shrinks. On a
        200-document corpus δ=3 alone consumes ~23 % of all postings, making a
        6 % rung unreachable and the comparison no longer retention-matched.
        Every δ is therefore precomputed once and chosen per cell.
        """
        self.delta = delta
        self.sweep_additions = self.sweep_by_delta.get(delta, {})

    def sweep_cost(self, delta: int) -> float:
        """Retention consumed by Rule C alone at this δ."""
        additions = self.sweep_by_delta.get(delta, {})
        kept = sum(len(v) for v in additions.values())
        return kept / self.total_postings if self.total_postings else 0.0


def prepare_models(
    doc_fields: dict[str, object], params, *, delta: int,
    progress: Callable[[str], None] | None = None,
) -> PreparedCorpus:
    """Rank every document once, per ranker, and precompute Rule C's additions."""
    docs = [DocumentModel(doc_id, fields, params)
            for doc_id, fields in sorted(doc_fields.items())]
    collection = build_collection_model(docs)

    spine = {d.doc_id: heading_spine(d) for d in docs}
    vocab = {d.doc_id: d.vocabulary() for d in docs}
    total_postings = sum(len(v) for v in vocab.values())

    if progress:
        progress(f"ranking {len(docs):,} documents by impact")
    impact_by_doc: dict[str, dict[str, float]] = {}
    order: dict[str, dict[str, list[str]]] = {"impact": {}, "kl": {}}
    for d in docs:
        scores = impacts(d, collection, params)
        impact_by_doc[d.doc_id] = scores
        order["impact"][d.doc_id] = [
            t for t, _ in sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        ]

    if progress:
        progress("ranking by KL divergence (arm 1)")
    kl_model = build_kl_model(
        {t: _raw_count(d, t) for t in d.vocabulary()} for d in docs
    )
    for d in docs:
        raw = {t: _raw_count(d, t) for t in d.vocabulary()}
        scores = kl_term_scores(raw, kl_model)
        order["kl"][d.doc_id] = [
            t for t, _ in sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        ]

    if progress:
        progress(f"precomputing Rule C sweeps (δ ≤ {delta})")
    # Every δ up to the requested one, so a cell can step down when the sweep
    # alone would blow the retention rung. Nested by construction: the top-δ
    # documents for δ=1 are a prefix of those for δ=3.
    sweep_by_delta = _sweep_additions_upto(impact_by_doc, delta)
    del impact_by_doc  # ~1 GB at 10⁴ long documents; the sweeps are what we keep
    return PreparedCorpus(docs, collection, spine, order, vocab, total_postings,
                          sweep_by_delta, delta)


def feasible_delta(prep: PreparedCorpus, target: float, requested: int,
                   *, headroom: float = 0.5) -> tuple[int, bool]:
    """``(δ, fits)`` — the largest δ whose sweep leaves room for the rung.

    Rule C is a *backstop*, not the whole budget: if the sweep alone consumed
    the rung, arm 4 would be measured at a retention no other arm was measured
    at, and the comparison would stop meaning anything.

    **Rule C has a floor cost**, and it is structural rather than a tuning
    accident: the sweep keeps `δ` postings for *every distinct term in the
    collection*, so it costs `δ × |vocabulary| / |postings|` — a quantity that
    grows as the corpus shrinks. On a few-hundred-document corpus even δ=1 can
    exceed a 6 % rung, which means **arm 4 is not merely expensive there, it is
    unreachable**. That is reported (``fits=False``) rather than papered over by
    degenerating the arm into arm 3, which would silently compare a different
    selector under arm 4's name.
    """
    for d in range(requested, 0, -1):
        if prep.sweep_cost(d) <= headroom * target:
            return d, True
    return 1, False


def _raw_count(doc: DocumentModel, term: str) -> int:
    f = doc.fields
    return f.heading.get(term, 0) + f.path.get(term, 0) + f.body.get(term, 0)


def _sweep_additions_upto(
    impact_by_doc: dict[str, dict[str, float]], max_delta: int
) -> dict[int, dict[str, set[str]]]:
    """**Rule C**, precomputed for every δ ≤ ``max_delta`` in a single pass.

    A term's best documents are a property of the corpus, not of any budget, so
    this is computed once and reused across every rung. The δ=1 sweep is a
    prefix of the δ=2 sweep and so on, which is why one ranking serves them all
    — recomputing per δ would quadruple the cost on a 10⁴-document corpus for
    no new information.

    Ordering is ``(-impact, doc_id)``: that tie-break is what makes the sweep
    order-independent, and it is asserted by a test rather than assumed.
    """
    if max_delta <= 0:
        return {0: {}}
    by_term: dict[str, list[tuple[float, str]]] = {}
    for doc_id in sorted(impact_by_doc):
        for term, score in impact_by_doc[doc_id].items():
            by_term.setdefault(term, []).append((score, doc_id))

    out: dict[int, dict[str, set[str]]] = {d: {} for d in range(max_delta + 1)}
    for term in sorted(by_term):
        bucket = by_term[term]
        # Only the top max_delta matter; a full sort of a long posting list is
        # wasted work when max_delta is 3.
        top = sorted(bucket, key=lambda si: (-si[0], si[1]))[:max_delta]
        for rank, (_score, doc_id) in enumerate(top, start=1):
            for d in range(rank, max_delta + 1):
                out[d].setdefault(doc_id, set()).add(term)
    return out


def kept_for(prep: PreparedCorpus, arm: ArmSpec, share: float, floor: int) -> dict[str, set[str]]:
    """The kept vocabulary per document for one arm at one budget share."""
    if arm.ranker == "none":
        return {doc_id: set(v) for doc_id, v in prep.vocab.items()}
    ranked = prep.order[arm.ranker]
    kept: dict[str, set[str]] = {}
    for doc_id, vocab in prep.vocab.items():
        budget = max(floor, math.ceil(share * len(vocab)))
        spine = prep.spine[doc_id] if arm.use_spine else set()
        if len(spine) >= budget:
            kept[doc_id] = set(spine)  # Rule A is a floor, never truncated
            continue
        remaining = budget - len(spine)
        picked = set(spine)
        for term in ranked[doc_id]:
            if len(picked) - len(spine) >= remaining:
                break
            if term not in spine:
                picked.add(term)
        kept[doc_id] = picked
    if arm.use_sweep:
        for doc_id, terms in prep.sweep_additions.items():
            if doc_id in kept:
                kept[doc_id] |= terms
    return kept


def retention_of(prep: PreparedCorpus, kept: dict[str, set[str]]) -> float:
    total = prep.total_postings
    return (sum(len(v) for v in kept.values()) / total) if total else 1.0


def calibrate(
    prep: PreparedCorpus, arm: ArmSpec, target: float, floor: int,
    *, tolerance: float = 0.0025, max_iter: int = 40,
) -> tuple[float, float, dict[str, set[str]]]:
    """Find the share whose *actual* retention hits ``target``.

    Matched retention is the whole point of the design: without it, an arm that
    happens to keep more postings would look better for a reason that has
    nothing to do with its criterion. Returns ``(share, actual, kept)``.

    Rule C and the budget floor both add postings the share does not control,
    so an arm may be unable to reach a low target at all. That is reported as
    an over-retention, not silently accepted — the caller decides whether the
    cell is comparable.
    """
    if arm.ranker == "none":
        kept = kept_for(prep, arm, 1.0, floor)
        return 1.0, retention_of(prep, kept), kept

    lo, hi = 0.0, 1.0
    best = kept_for(prep, arm, 0.0, floor)
    best_share, best_actual = 0.0, retention_of(prep, best)
    if best_actual >= target:  # floor + spine + sweep already exceed the target
        return 0.0, best_actual, best

    for _ in range(max_iter):
        mid = (lo + hi) / 2
        kept = kept_for(prep, arm, mid, floor)
        actual = retention_of(prep, kept)
        best_share, best_actual, best = mid, actual, kept
        if abs(actual - target) <= tolerance:
            break
        if actual < target:
            lo = mid
        else:
            hi = mid
    return best_share, best_actual, best
