"""The three index arms — baseline, pruned, and the diagnostic.

The whole experiment turns on one sentence: **only the index differs**. Every
arm is an instance of the archived v0.26 ``Searcher`` and is scored by the
archived ``Searcher.search``; this module never reimplements BM25F, and never
edits the archive. It builds the ``Searcher``'s internal state directly
(``Searcher.__new__`` plus field assignment) so that:

* the baseline arm is byte-identical to what ``Searcher(files, params)`` builds
  (asserted by a test, not assumed), and
* the pruned arms can drop postings and recompute lengths without a
  ``Searcher`` subclass hook that the archive does not expose.

The subtle correctness point, spelled out because getting it wrong silently
invalidates the result: the **pruned** arm recomputes ``df``, ``n`` and
``avg_wlen`` from the pruned postings. In production, ``D/`` holds exact ``df``
over the pruned index — a term's ``df`` is the number of documents in which it
*survived*. Borrowing the baseline's statistics makes the scores line up
better and measures a system nobody is going to ship. That borrowing is exactly
what the **diag** arm does, deliberately, so losses can be attributed to
*missing postings* versus *shifted statistics* — and diag never enters the
verdict.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator

from fux.config import BM25FParams
from fux.index.bm25f import Searcher, path_tokens, tokenize

from .kl_select import CollectionModel, build_collection_model, select_top_k

__all__ = [
    "ChunkFields",
    "iter_chunk_fields",
    "document_term_frequencies",
    "collection_model_for",
    "kept_terms_by_doc",
    "build_arm",
    "BorrowedStats",
    "ArmStats",
]


class ChunkFields:
    """One chunk's per-field term counts, in the archived Searcher's own order."""

    __slots__ = ("file", "ordinal", "heading", "path", "body")

    def __init__(self, file: str, ordinal: int, heading: Counter, path: Counter, body: Counter):
        self.file = file
        self.ordinal = ordinal
        self.heading = heading
        self.path = path
        self.body = body

    def terms(self) -> set[str]:
        return set(self.heading) | set(self.path) | set(self.body)


def iter_chunk_fields(files: dict[str, dict]) -> Iterator[ChunkFields]:
    """Reproduce the archived ``Searcher.__init__`` tokenization, in its order.

    Chunk index order is load-bearing: ``Searcher.search`` breaks score ties on
    ``(file, chunk_index)``, so a different traversal would silently change
    rankings. This iterates ``sorted(files)`` then chunk ordinal, exactly as the
    archive does.
    """
    for rel in sorted(files):
        meta = files[rel]
        ptoks = Counter(path_tokens(rel))
        title = meta.get("title", "")
        for ordinal, chunk in enumerate(meta["chunks"]):
            htoks = Counter(tokenize(chunk["heading"]) + tokenize(title))
            btoks = Counter(tokenize(chunk["text"]))
            yield ChunkFields(rel, ordinal, htoks, ptoks, btoks)


def document_term_frequencies(files: dict[str, dict]) -> dict[str, dict[str, int]]:
    """Per-document raw term counts — the input to KL selection.

    Definition (pre-registered): the sum of every chunk's heading and body
    counts, plus the document's path tokens counted **once**. Path tokens are a
    property of the document, not of each chunk; counting them per chunk would
    scale a document's path weight with its length and make long documents
    keep their path tokens for the wrong reason.

    Counts are raw and unweighted. Field weights are a *scoring* concern; the
    weighted-selection variant is a declared non-goal here.
    """
    doc_tf: dict[str, dict[str, int]] = {}
    for rel in sorted(files):
        meta = files[rel]
        tf: dict[str, int] = {}
        for term, count in Counter(path_tokens(rel)).items():
            tf[term] = tf.get(term, 0) + count
        title = meta.get("title", "")
        for chunk in meta["chunks"]:
            for term, count in Counter(tokenize(chunk["heading"]) + tokenize(title)).items():
                tf[term] = tf.get(term, 0) + count
            for term, count in Counter(tokenize(chunk["text"])).items():
                tf[term] = tf.get(term, 0) + count
        doc_tf[rel] = tf
    return doc_tf


def document_field_counts(files: dict[str, dict]) -> dict[str, object]:
    """Per-document, per-field term counts — the selector's view of the corpus.

    Aggregates each document's chunks into one field triple, because production
    prunes a *document's* index entry, not a chunk's. Path tokens are counted
    once per document for the same reason they are in
    ``document_term_frequencies``: they describe the document, not each of its
    slices.
    """
    from .selector import FieldCounts

    out: dict[str, object] = {}
    for rel in sorted(files):
        meta = files[rel]
        heading: dict[str, int] = {}
        body: dict[str, int] = {}
        path = dict(Counter(path_tokens(rel)))
        title = meta.get("title", "")
        for chunk in meta["chunks"]:
            for term, count in Counter(tokenize(chunk["heading"]) + tokenize(title)).items():
                heading[term] = heading.get(term, 0) + count
            for term, count in Counter(tokenize(chunk["text"])).items():
                body[term] = body.get(term, 0) + count
        out[rel] = FieldCounts(heading, path, body)
    return out


def collection_model_for(doc_tf: dict[str, dict[str, int]]) -> CollectionModel:
    """``P(t|C)`` over the **unpruned** corpus, in deterministic document order."""
    return build_collection_model(doc_tf[rel] for rel in sorted(doc_tf))


def kept_terms_by_doc(
    doc_tf: dict[str, dict[str, int]], model: CollectionModel, k: int | None
) -> dict[str, set[str]]:
    """The surviving vocabulary per document. ``k=None`` keeps everything."""
    return {rel: set(select_top_k(doc_tf[rel], model, k)) for rel in sorted(doc_tf)}


class ArmStats:
    """Corpus statistics an arm actually holds — reported, never injected.

    The pruned arm runs with ``Searcher.stats = None`` on purpose: with no
    injected statistics the archived scorer derives ``df`` from the length of
    each (pruned) posting list, ``n`` from the chunk count, and ``avg_wlen``
    from the (recomputed) lengths. That is precisely the production definition,
    obtained without touching the scorer.
    """

    __slots__ = ("chunks", "postings", "avg_wlen", "kept_postings", "pruned_docs", "total_docs")

    def __init__(self, chunks: int, postings: int, avg_wlen: float,
                 kept_postings: int, pruned_docs: int, total_docs: int):
        self.chunks = chunks
        self.postings = postings
        self.avg_wlen = avg_wlen
        self.kept_postings = kept_postings
        self.pruned_docs = pruned_docs
        self.total_docs = total_docs


class BorrowedStats:
    """The **diagnostic** arm's statistics: pruned postings, baseline numbers.

    Implements the archived ``stats`` protocol (``total_chunks``, ``avg_wlen``,
    ``df_of``) that ``Searcher.search`` already consults — the seam the archived
    lean profile uses, reused here rather than invented.

    This arm is a measuring instrument, not a candidate system. It answers "was
    this loss caused by the missing postings, or by the statistics moving?" and
    nothing else.
    """

    __slots__ = ("total_chunks", "_avg_wlen", "_df")

    def __init__(self, total_chunks: int, avg_wlen: float, df: dict[str, int]):
        self.total_chunks = total_chunks
        self._avg_wlen = avg_wlen
        self._df = df

    def avg_wlen(self, params: BM25FParams) -> float:  # noqa: ARG002 — protocol shape
        return self._avg_wlen

    def df_of(self, term: str) -> int:
        return self._df.get(term, 0)


def build_arm(
    files: dict[str, dict],
    params: BM25FParams,
    *,
    kept: dict[str, set[str]] | None = None,
    stats: BorrowedStats | None = None,
    keep_payload: bool = False,
) -> tuple[Searcher, ArmStats]:
    """Construct one arm's ``Searcher``.

    ``kept=None`` builds the full baseline index. Otherwise every posting whose
    document did not keep that term is dropped, and each chunk's weighted length
    is recomputed over the surviving terms only.

    ``keep_payload=False`` blanks the chunk text/heading/span carried into
    ``ScoredChunk``. Document-level metrics never read those fields, and holding
    the whole corpus text in memory is what makes a 10⁵-document arm
    impractical. **Every arithmetic input to the scorer is untouched** — the
    per-field term frequencies, the weighted lengths, the posting order and the
    tie-break key are all exactly what the archive builds.
    """
    searcher = Searcher.__new__(Searcher)
    searcher.params = params
    searcher.stats = stats
    chunks: list[dict] = []
    postings: dict[str, list[tuple[int, int, int, int]]] = {}
    total_wlen = 0.0
    posting_count = 0

    for cf in iter_chunk_fields(files):
        keep = kept.get(cf.file) if kept is not None else None
        if keep is None:
            htoks, ptoks, btoks = cf.heading, cf.path, cf.body
        else:
            htoks = Counter({t: c for t, c in cf.heading.items() if t in keep})
            ptoks = Counter({t: c for t, c in cf.path.items() if t in keep})
            btoks = Counter({t: c for t, c in cf.body.items() if t in keep})
        wlen = (
            params.heading * sum(htoks.values())
            + params.path * sum(ptoks.values())
            + params.body * sum(btoks.values())
        )
        ix = len(chunks)
        chunks.append(
            {
                "file": cf.file,
                "heading": "",
                "text": "",
                "start": None,
                "end": None,
                "ordinal": cf.ordinal,
                "wlen": wlen,
            }
        )
        for term in set(htoks) | set(ptoks) | set(btoks):
            postings.setdefault(term, []).append(
                (ix, htoks[term], ptoks[term], btoks[term])
            )
            posting_count += 1
        total_wlen += wlen

    searcher.chunks = chunks
    searcher.postings = postings
    searcher.avg_wlen = total_wlen / len(chunks) if chunks else 1.0

    # ``pruned_docs`` needs the *unpruned* vocabulary sizes, which live in the
    # caller's ``doc_tf``; it is filled in by ``prune_coverage`` rather than
    # recomputed here from data this function does not hold.
    stats_out = ArmStats(
        chunks=len(chunks),
        postings=posting_count,
        avg_wlen=searcher.avg_wlen,
        kept_postings=posting_count,
        pruned_docs=0,
        total_docs=len(files),
    )
    return searcher, stats_out


def prune_coverage(doc_tf: dict[str, dict[str, int]], k: int | None) -> tuple[int, int]:
    """``(documents actually pruned, total documents)`` at this ``k``.

    "Actually pruned" means the document's distinct vocabulary exceeded ``k``.
    For every other document top-``k`` is a no-op, and a corpus made mostly of
    such documents cannot test P1 — reporting this is what stops a vacuous PASS.
    """
    total = len(doc_tf)
    if k is None:
        return 0, total
    return sum(1 for tf in doc_tf.values() if len(tf) > k), total


def vocabulary_profile(doc_tf: dict[str, dict[str, int]]) -> dict[str, float]:
    """Distinct-term counts per document: min / median / p90 / p99 / max / mean.

    This is the number that decides whether a corpus can test top-*k* pruning at
    all. The paper's size model assumes ~10⁴-word documents, whose vocabularies
    run into the thousands; a corpus of short documents is simply *below* the
    operating point and will report a delta of zero for the uninteresting reason
    that nothing was dropped.
    """
    sizes = sorted(len(tf) for tf in doc_tf.values())
    if not sizes:
        return {"n": 0}

    def pct(p: float) -> int:
        idx = min(len(sizes) - 1, int(p * (len(sizes) - 1)))
        return sizes[idx]

    return {
        "n": len(sizes),
        "min": sizes[0],
        "median": pct(0.5),
        "p90": pct(0.9),
        "p99": pct(0.99),
        "max": sizes[-1],
        "mean": round(sum(sizes) / len(sizes), 2),
    }


def baseline_df(searcher: Searcher) -> dict[str, int]:
    """Per-term document (chunk) frequency of a built arm — the ``diag`` input."""
    return {term: len(plist) for term, plist in searcher.postings.items()}
