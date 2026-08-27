"""The reranker. W-76 Phase 6.

BM25F is a **bag of words**: it knows how often each query term occurs and how
long the document is, and it knows nothing whatever about *where* the terms
are. Two documents with identical term counts score identically even when one
says the query back as a sentence and the other scatters the same words across
four unrelated sections.

That blindness is most of what a reranker exists to fix, and on the playground
corpus it is measurable: ADR-0007 (superseded) outranks ADR-0019 (current) on
six of eight supersession queries, because both are dense in the same
vocabulary and the *superseded* one is shorter, so the length normaliser
prefers it. The sentence that settles the question --

    "This is the current decision for east-west traffic."

-- is a fact about **adjacency**, and BM25F cannot see adjacency.

## Why this is stdlib arithmetic and not a cross-encoder

W-76 Phase 6 as written specified a 17-32 M cross-encoder behind an optional
`onnxruntime`. That was refused, and the reason is not cost:

1. **It would break cross-machine determinism, which is the product.**
   ADR-GRAPH proved fux's float maths is byte-identical between x86-64 Linux
   and arm64 macOS -- *for pure Python*. `onnxruntime` dispatches to different
   SIMD kernels per architecture and reduces GEMMs in a different order, so
   two developers running the same query against the same commit would get
   different orderings. "Clone it and run the query" stops being true.
2. **Optional-but-on breaks L4; optional-but-off is not a feature.** Either
   fux downloads ~35 MB on first run -- offline-by-default gone -- or the lane
   ships dark and nobody measures it.
3. **The number was unknown.** Nothing said whether reranking was worth 2
   points or 20. Building the cheap signal first turns the neural question
   from a preference into arithmetic: *this bought N; is a binary dependency
   worth what is left?*

So the reranker computes three things BM25F structurally cannot, over the
**same analyzed token stream** the index was built from:

| signal | what it catches | what BM25F does instead |
|---|---|---|
| **coverage** | all query terms present, once each | sums per term, so 5x one term beats 1x five |
| **min span** | the terms occur *together* | ignores position entirely |
| **adjacency** | query bigrams occur as bigrams | ignores order entirely |

## The rules it obeys

- **It re-orders; it never retrieves.** The candidate set is exactly what the
  ranker produced. A document BM25F did not find cannot be rescued here --
  which is what keeps *the committed plane is sufficient to answer* true.
- **Same analyzer, by construction.** Positions come from `analyze()`, the one
  the index was built with. A reranker with its own notion of a token is a
  second scorer that will disagree with the first (`refer/rescore.py`'s
  opening argument, applied again).
- **Deterministic.** Pure Python, no floats crossing a machine boundary that
  ADR-GRAPH did not already cover, and the sort key is
  `(-round(score, 9), id)` -- never iteration order.
- **A document it cannot read is left alone.** Offline, a `url:` document has
  no text to rerank against; it keeps its BM25F score rather than being
  demoted for being unreachable.
"""

from __future__ import annotations

from pathlib import Path

from .analyzer import analyze

__all__ = ["COVERAGE_POWER", "DEPTH", "WEIGHT", "boost", "passage_boost", "rerank", "signals"]

#: How far down the ranking to reorder. Beyond this the reranker would be
#: paying to read documents nobody will look at; W-76's gate is phrased
#: `top-20 -> top-5`, and this is the 20.
DEPTH = 20

#: The maximum fraction a perfect proximity match may add to a BM25F score.
#: A **bounded multiplicative uplift**, exactly like the dense lane's `fuse()`:
#: the two quantities are on unrelated scales and adding them would let a
#: proximity signal of 0.4 outweigh a real term match on a corpus where BM25F
#: happens to score low. Tunable via `[ranking] rerank_weight`.
#:
#: `1.0` means *a perfect proximity match may at most double a score*. Chosen
#: off a measured plateau rather than a peak: the 4x5 sweep of
#: (COVERAGE_POWER, WEIGHT) over the 50 goldens scores 30-32 everywhere, with
#: 32 at (2, 1.0), (2, 1.5), (3, 1.5), (3, 2.0) and (4, 2.0). A constant
#: picked from the middle of a plateau survives a corpus it was not tuned on;
#: one picked from a spike is an overfit to 50 queries.
WEIGHT = 1.0

#: How hard a **missing** query term is punished. Coverage is raised to this
#: before it multiplies, so a passage covering 4 of 5 query terms keeps 64 %
#: of its proximity rather than 80 %.
#:
#: The measured argument, on golden `q015` (*"what is the current decision for
#: east west traffic"*): the superseded ADR-0007 scores BM25F **8.01** against
#: the current ADR-0019's **6.64**, because both are dense in the same
#: vocabulary and the superseded one is shorter. ADR-0019 contains every query
#: term; ADR-0007 is missing exactly one -- `current` -- which is *the entire
#: question*. Linear coverage prices that omission at 20 % and loses; squared
#: prices it at 36 % and wins.
COVERAGE_POWER = 2

#: Below two distinct query terms there is no proximity to measure -- one term
#: is always perfectly covered, adjacent to nothing, and spans itself.
_MIN_TERMS = 2


def signals(query_terms: list[str], doc_terms: list[str]) -> tuple[float, float, float]:
    """`(coverage, span, adjacency)`, each in `[0, 1]`.

    Computed over analyzed token *positions*, so a stem matches a stem and the
    reranker cannot disagree with the index about what a term is.
    """
    wanted = list(dict.fromkeys(query_terms))  # distinct, query order preserved
    if not wanted or not doc_terms:
        return 0.0, 0.0, 0.0

    positions: dict[str, list[int]] = {}
    for i, term in enumerate(doc_terms):
        if term in wanted:
            positions.setdefault(term, []).append(i)

    present = [t for t in wanted if t in positions]
    coverage = len(present) / len(wanted)
    if len(present) < _MIN_TERMS:
        # One term (or none) -- coverage is the only honest signal, and there
        # is no window to measure. Returning a span here would reward a
        # single-term document for a proximity it never demonstrated.
        return coverage, 0.0, 0.0

    span = _span_signal(positions, present)
    adjacency = _adjacency_signal(positions, wanted)
    return coverage, span, adjacency


def _span_signal(positions: dict[str, list[int]], present: list[str]) -> float:
    """How tightly the matched terms cluster, at their tightest.

    The **minimum window** containing one occurrence of every present term,
    found by advancing the earliest pointer -- the standard linear sweep, not
    an all-pairs product, because a common term in a long document has
    thousands of positions and the quadratic version is what makes naive
    proximity scoring too slow to ship.

    Normalised as `k / window`, so a window exactly as wide as the number of
    terms (they are adjacent) scores 1.0 and a window twice that scores 0.5.
    """
    k = len(present)
    cursors = {term: 0 for term in present}
    best = None
    while True:
        current = [(positions[t][cursors[t]], t) for t in present]
        low, low_term = min(current)
        high = max(p for p, _ in current)
        width = high - low + 1
        if best is None or width < best:
            best = width
        cursors[low_term] += 1
        if cursors[low_term] >= len(positions[low_term]):
            break
    return k / best if best else 0.0


def _adjacency_signal(positions: dict[str, list[int]], wanted: list[str]) -> float:
    """Fraction of query bigrams that occur as bigrams in the document.

    Ordered and immediate: `a b` in the query counts only where `b` follows
    `a` directly. This is the signal that separates *"the current decision for
    east-west traffic"* from a document that merely uses all five words.
    """
    pairs = [(wanted[i], wanted[i + 1]) for i in range(len(wanted) - 1)]
    if not pairs:
        return 0.0
    hits = 0
    for first, second in pairs:
        if first not in positions or second not in positions:
            continue
        later = set(positions[second])
        if any(p + 1 in later for p in positions[first]):
            hits += 1
    return hits / len(pairs)


def passage_boost(query_terms: list[str], passage_terms: list[str]) -> float:
    """One passage's proximity score in `[0, 1]`.

    **Coverage multiplies rather than adds**, and that is the whole difference
    between a reranker that works and one that does not. Measured on the 50
    goldens: with coverage as a weighted *addend* the reranker moved 2
    queries, because every candidate in a corpus about one subject scores
    0.85-1.0 and an 8 % spread cannot overcome a BM25F gap. Multiplying it
    makes a missing term expensive -- a passage covering 4 of 5 query terms
    keeps at most 80 % of its proximity, not 95 % of it.

    That is also the right shape on the merits. Span and adjacency are claims
    about terms the passage HAS; they are meaningless about a term it lacks.
    Scoring them as if a missing term were merely a small deduction rewards a
    passage for the tightness of an incomplete match.
    """
    coverage, span, adjacency = signals(query_terms, passage_terms)
    if coverage <= 0:
        return 0.0
    return (coverage**COVERAGE_POWER) * (0.55 + 0.30 * span + 0.15 * adjacency)


def boost(query_terms: list[str], text: str) -> float:
    """A document scores as its BEST passage, never its average one.

    The deleted dense lane made the same argument for vectors (max-sim per
    document, never mean-sim), and it matters more here: measured over whole
    documents, every candidate in a
    corpus about one subject reaches coverage 1.0 somewhere, and the signal
    flattens to noise. A document that answers the question in one section and
    discusses nine other things is exactly what should win, and averaging is
    how it loses.

    Chunking is the refer plane's, deliberately -- one chunker, so a passage
    the reranker scored is a passage `answer` can cite.
    """
    from ..refer._chunk import chunk

    best = 0.0
    for passage in chunk(text):
        score = passage_boost(query_terms, analyze(passage.text))
        if score > best:
            best = score
    return best


def rerank(root: Path, query: str, results, *, depth: int = DEPTH, weight: float = WEIGHT, read=None):
    """Reorder the top `depth` results by proximity. Never adds or drops one.

    `read` is **injected, never imported** -- the same rule `refer/source.py`
    follows for fetchers. It takes `(root, doc_id, loc)` and returns text, or
    `None` when the document cannot be read; the default reads local files and
    declines `url:` documents, because reranking one offline would mean
    fetching, and `ask` is not a networked verb.
    """
    if weight <= 0 or depth <= 0 or len(results) < 2:
        return list(results)

    query_terms = analyze(query)
    if len(dict.fromkeys(query_terms)) < _MIN_TERMS:
        # A one-term query has no proximity. Reranking it would be arithmetic
        # on a signal that is constant across every candidate.
        return list(results)

    reader = read if read is not None else _read_local_text
    head = list(results[:depth])
    tail = list(results[depth:])

    rescored = []
    for result in head:
        text = reader(root, result.id, result.loc)
        if text is None:
            rescored.append((result.score, result))
            continue
        uplift = 1.0 + weight * boost(query_terms, text)
        rescored.append((result.score * uplift, result))

    rescored.sort(key=lambda pair: (-round(pair[0], 9), pair[1].id))
    import dataclasses

    return [dataclasses.replace(r, score=s) for s, r in rescored] + tail


def _read_local_text(root: Path, doc_id: str, loc: str) -> str | None:
    """Local file text, or `None` for anything that would need the network."""
    if not doc_id.startswith("file:"):
        return None
    path = root / loc
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
