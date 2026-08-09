"""The combined pruning selector — Rules A, B and C of `pruning-criterion` §7.

The criterion ADR-0017 measured (KL divergence) rewards terms that are *rare
across the collection*, so in a corpus where every document is about payments
the word `payments` looks uninformative. The run literally dropped `webhook`
from `docs/api/webhooks.md`. Three rules answer that:

* **Rule A — the heading spine.** Terms in the document's title or any heading
  always survive. A document may not lose the words it announces itself with.
* **Rule B — the impact budget.** Fill the rest of the budget by *max BM25F
  impact*, i.e. by what the deployed scorer actually rewards, rather than by
  divergence from a collection model the scorer never consults.
* **Rule C — the per-term backstop.** After every document has chosen, sweep
  each term and force-keep it in its top-δ best-matching documents. This fixes
  the `webhooks.md` class of failure *by construction*: a term can never lose
  all of its best documents, whatever their local budgets decided.

Budget is `max(floor, ceil(share × |vocab(d)|))` — a *share*, not a constant k,
so the treatment means the same thing on a short note and a long specification.
Fixed k is exactly what made ADR-0017's run untestable.

Two properties the experiment depends on, both tested:

* **Rule C is order-independent.** Terms are swept in sorted order and impact
  ties break on document id, so the kept set is a function of the corpus alone.
* **Selection uses the *unpruned* collection model.** It must: you cannot rank
  terms by impact against statistics that depend on the ranking's own output.
  The final index then recomputes `df`/`n`/lengths over the kept postings. That
  is a deliberate two-pass build, not an inconsistency — see ADR-0018.

Pure functions, stdlib only, written to port into `src/fux/ingest/` unchanged.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

__all__ = [
    "FieldCounts",
    "DocumentModel",
    "CollectionModel",
    "build_collection_model",
    "heading_spine",
    "impacts",
    "select_document",
    "term_centric_sweep",
    "budget_for",
]


class FieldCounts:
    """A document's per-field term frequencies, aggregated over its chunks."""

    __slots__ = ("heading", "path", "body")

    def __init__(self, heading: Mapping[str, int], path: Mapping[str, int],
                 body: Mapping[str, int]):
        self.heading = dict(heading)
        self.path = dict(path)
        self.body = dict(body)

    def terms(self) -> set[str]:
        return set(self.heading) | set(self.path) | set(self.body)

    def weighted_tf(self, term: str, p) -> float:
        return (p.heading * self.heading.get(term, 0)
                + p.path * self.path.get(term, 0)
                + p.body * self.body.get(term, 0))

    def weighted_length(self, p) -> float:
        return (p.heading * sum(self.heading.values())
                + p.path * sum(self.path.values())
                + p.body * sum(self.body.values()))


class DocumentModel:
    """One document as the selector sees it."""

    __slots__ = ("doc_id", "fields", "wlen")

    def __init__(self, doc_id: str, fields: FieldCounts, params):
        self.doc_id = doc_id
        self.fields = fields
        self.wlen = fields.weighted_length(params)

    def vocabulary(self) -> set[str]:
        return self.fields.terms()


class CollectionModel:
    """Unpruned corpus statistics: document frequency, count, mean length."""

    __slots__ = ("df", "n", "avg_wlen")

    def __init__(self, df: Mapping[str, int], n: int, avg_wlen: float):
        self.df = dict(df)
        self.n = n
        self.avg_wlen = avg_wlen or 1.0

    def idf(self, term: str) -> float:
        """The archived scorer's idf, unchanged — the selector must rank terms
        by the same quantity the scorer will later use, or Rule B optimizes the
        wrong objective."""
        df = self.df.get(term, 0)
        return math.log((self.n - df + 0.5) / (df + 0.5) + 1)


def build_collection_model(documents: list[DocumentModel]) -> CollectionModel:
    """Built from the **unpruned** corpus, in deterministic document order."""
    df: dict[str, int] = {}
    total_wlen = 0.0
    for doc in sorted(documents, key=lambda d: d.doc_id):
        for term in sorted(doc.vocabulary()):
            df[term] = df.get(term, 0) + 1
        total_wlen += doc.wlen
    n = len(documents)
    return CollectionModel(df, n, total_wlen / n if n else 1.0)


def budget_for(doc: DocumentModel, share: float, floor: int) -> int:
    """`max(floor, ceil(share × |vocab|))` — a share, never a constant k."""
    if share < 0 or floor < 0:
        raise ValueError("share and floor must be non-negative")
    return max(floor, math.ceil(share * len(doc.vocabulary())))


def heading_spine(doc: DocumentModel) -> set[str]:
    """**Rule A** — terms in the title or any heading field, always kept.

    The archived scorer folds the document title into the heading field, so
    this is exactly "the words the document announces itself with".
    """
    return {t for t, c in doc.fields.heading.items() if c > 0}


def impacts(doc: DocumentModel, collection: CollectionModel, params) -> dict[str, float]:
    """max BM25F contribution of each term in this document.

    The archived scorer's formula, at document granularity — production prunes a
    document's entry, not a chunk's. Terms are returned rounded so that a
    last-ulp difference in `math.log` cannot reorder two otherwise-equal terms
    across platforms.
    """
    out: dict[str, float] = {}
    for term in doc.vocabulary():
        wtf = doc.fields.weighted_tf(term, params)
        if wtf <= 0:
            continue
        denom = wtf + params.k1 * (1 - params.b + params.b * doc.wlen / collection.avg_wlen)
        out[term] = round(collection.idf(term) * wtf * (params.k1 + 1) / denom, 12)
    return out


def select_document(
    doc: DocumentModel,
    collection: CollectionModel,
    params,
    *,
    share: float,
    floor: int,
    use_spine: bool = True,
    use_impact: bool = True,
    scorer=None,
) -> set[str]:
    """**Rules A + B** — one document's local pass.

    ``use_spine`` / ``use_impact`` select which arm this is; ``scorer`` replaces
    the impact ranking (arm 1 passes a KL scorer) so every arm shares one code
    path and cannot differ by accident.
    """
    vocab = doc.vocabulary()
    if not vocab:
        return set()
    budget = budget_for(doc, share, floor)
    spine = heading_spine(doc) if use_spine else set()
    if len(spine) >= budget:
        # The spine alone exceeds the budget. Keep it whole rather than
        # truncating: Rule A is a floor, not a suggestion. Reported as
        # over-budget retention rather than silently violated.
        return set(spine)
    ranked = (scorer or impacts)(doc, collection, params) if use_impact or scorer else {}
    remaining = budget - len(spine)
    candidates = sorted(
        ((t, s) for t, s in ranked.items() if t not in spine),
        key=lambda kv: (-kv[1], kv[0]),
    )
    return spine | {t for t, _ in candidates[:remaining]}


def term_centric_sweep(
    documents: list[DocumentModel],
    kept: dict[str, set[str]],
    collection: CollectionModel,
    params,
    *,
    delta: int,
    impact_cache: dict[str, dict[str, float]] | None = None,
) -> int:
    """**Rule C** — force-keep each term in its top-δ best documents.

    Runs *after* every document's local pass (mutating ``kept`` in place) and
    *before* corpus statistics are recomputed, because the sweep changes `df`.

    Order-independent by construction: terms are visited in sorted order and
    documents rank by ``(-impact, doc_id)``. Returns the number of postings the
    sweep added, so the caller can report retention honestly rather than
    assuming the local budget was the final one.
    """
    if delta <= 0:
        return 0
    cache = impact_cache if impact_cache is not None else {}
    by_term: dict[str, list[tuple[float, str]]] = {}
    for doc in sorted(documents, key=lambda d: d.doc_id):
        scores = cache.get(doc.doc_id)
        if scores is None:
            scores = impacts(doc, collection, params)
            if impact_cache is not None:
                cache[doc.doc_id] = scores
        for term, score in scores.items():
            by_term.setdefault(term, []).append((score, doc.doc_id))

    added = 0
    for term in sorted(by_term):
        ranked = sorted(by_term[term], key=lambda si: (-si[0], si[1]))
        for _score, doc_id in ranked[:delta]:
            bucket = kept.setdefault(doc_id, set())
            if term not in bucket:
                bucket.add(term)
                added += 1
    return added
