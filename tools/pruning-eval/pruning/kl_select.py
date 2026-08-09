"""Document-centric static index pruning — KL top-k term selection.

The rule (Büttcher & Clarke, CIKM 2006): for a document *d*, score each term by
its contribution to the Kullback–Leibler divergence between the document's term
distribution and the collection's, and keep the top *k*::

    score(t, d) = P(t|d) · log( P(t|d) / P(t|C) )

Why *document*-centric rather than term-centric (Carmel et al., SIGIR 2001):
term-centric pruning trims each posting list independently and can therefore
strip a document of every posting it had, making it unreachable. Document-centric
pruning guarantees each document keeps min(k, |vocab(d)|) postings, so nothing
becomes invisible — the property that lets the ledger promise every indexed
document is at least *findable*.

Three properties this module is written to hold, because they are the ones the
engine depends on:

* **Pure.** ``select_top_k`` is a function of its arguments — no I/O, no
  globals, no clock, no randomness. It is written to be moved into
  ``src/fux/ingest/`` unchanged.
* **Deterministic.** Ties break lexicographically on the term, and scores are
  rounded to a fixed precision before ordering so that a last-ulp difference in
  ``math.log`` across platforms cannot reorder two otherwise-equal terms.
* **Collection model from the *unpruned* corpus.** ``P(t|C)`` must be estimated
  before anything is dropped; building it from an already-pruned corpus would
  make the criterion depend on its own output.

Stdlib only. No third-party imports, ever.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping

__all__ = ["CollectionModel", "build_collection_model", "term_scores", "select_top_k"]

# Scores are compared after rounding to this many decimal places. ``math.log``
# is libm-backed and may differ in the last ulp between platforms; without this,
# two terms with mathematically identical scores could order differently on
# different machines and break byte-identical index builds.
_SCORE_PRECISION = 12


class CollectionModel:
    """``P(t|C)`` over the whole collection, built from unpruned documents.

    Holds collection term frequencies (``cf``) and the collection's total token
    count. ``cf`` is the right statistic here rather than document frequency:
    the criterion compares two *term distributions*, and a document frequency is
    not a distribution over terms.
    """

    __slots__ = ("_cf", "_total", "_floor")

    def __init__(self, cf: Mapping[str, int], total_tokens: int):
        if total_tokens < 0:
            raise ValueError("total_tokens must be non-negative")
        self._cf = cf
        self._total = total_tokens
        # A term absent from the collection cannot occur in a document of that
        # collection, so this floor is defensive only. It keeps the log finite
        # if a caller scores a document against a foreign collection model.
        self._floor = 1.0 / (total_tokens + 1) if total_tokens >= 0 else 1.0

    @property
    def total_tokens(self) -> int:
        return self._total

    def cf(self, term: str) -> int:
        """Collection frequency of ``term`` (0 if unseen)."""
        return self._cf.get(term, 0)

    def p(self, term: str) -> float:
        """``P(t|C)`` — never zero, so the log is always defined."""
        if self._total == 0:
            return self._floor
        count = self._cf.get(term, 0)
        if count == 0:
            return self._floor
        return count / self._total

    def __len__(self) -> int:
        return len(self._cf)


def build_collection_model(documents: Iterable[Mapping[str, int]]) -> CollectionModel:
    """Build ``P(t|C)`` from an iterable of per-document term-frequency maps.

    **Must be fed the unpruned corpus.** The caller owns the definition of a
    document's term-frequency map (which fields contribute, whether path tokens
    count once or per chunk); this function only sums what it is given.
    """
    cf: dict[str, int] = {}
    total = 0
    for doc_tf in documents:
        for term, count in doc_tf.items():
            if count < 0:
                raise ValueError(f"negative term frequency for {term!r}")
            cf[term] = cf.get(term, 0) + count
            total += count
    return CollectionModel(cf, total)


def term_scores(
    doc_tf: Mapping[str, int], model: CollectionModel
) -> dict[str, float]:
    """KL contribution of every term in ``doc_tf``, rounded for determinism.

    A term whose document probability equals its collection probability scores
    exactly ``0.0`` — it carries no discriminative power, which is why a term
    appearing uniformly everywhere is the first thing pruning drops.

    Note the sign: a term *rarer* in the document than in the collection scores
    **negative**. Those sort last and are pruned first, which is correct — the
    kept set is the document's positively distinctive vocabulary.
    """
    doc_total = 0
    for count in doc_tf.values():
        if count < 0:
            raise ValueError("negative term frequency")
        doc_total += count
    if doc_total == 0:
        return {}
    scores: dict[str, float] = {}
    for term, count in doc_tf.items():
        if count == 0:
            continue
        p_d = count / doc_total
        p_c = model.p(term)
        scores[term] = round(p_d * math.log(p_d / p_c), _SCORE_PRECISION)
    return scores


def select_top_k(
    doc_tf: Mapping[str, int], model: CollectionModel, k: int | None
) -> list[str]:
    """The kept term set for one document, highest KL contribution first.

    ``k=None`` means "keep everything" — pruning becomes a no-op, which is the
    identity the eval harness uses to prove that the only difference between its
    arms is pruning. ``k=0`` keeps nothing. Negative ``k`` is a caller bug.

    Returns a **list, in score order**, not a set: the order is meaningful (it
    is the order in which terms would be dropped by a smaller ``k``) and it is
    what makes the function's output byte-comparable across runs.
    """
    if k is not None and k < 0:
        raise ValueError("k must be non-negative or None")
    scores = term_scores(doc_tf, model)
    if not scores:
        return []
    ordered = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    if k is None:
        return [term for term, _ in ordered]
    return [term for term, _ in ordered[:k]]
