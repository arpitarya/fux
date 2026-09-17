"""The six lenses — each a pure function of the `IndexView` (plus the local
dictionary, where it needs a word rather than a hash).

**Every lens returns numbers and named lists. None of them returns a verdict.**
That split is the whole discipline of this verb: three checks carry a flag
(`checks.py`) and nothing else does, because a wall of red on an unmeasured
floor is how a diagnostic tool gets ignored. The one-number *index score* is
refused for the same reason the confidence band refuses to be one number —
it would be the number everyone quotes and the one nobody can act on.

**Every finding names its lever and applies none.** The levers are in `LEVERS`
below, held equal to [SR-INSPECT](../../../records/0156_inspect.md)'s table by
`tests/test_inspect_levers.py`, so a report can never recommend a knob the
records do not describe.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

__all__ = [
    "LEVERS",
    "Boilerplate",
    "Findability",
    "Lengths",
    "Duplication",
    "Coverage",
    "GraphShape",
    "boilerplate",
    "findability",
    "lengths",
    "duplication",
    "coverage",
    "graph_shape",
    "SIGNATURE_SIZE",
    "BAND_ROWS",
    "NEAR_DUPLICATE_JACCARD",
]

#: finding -> the lever that already exists for it. **The report prints the
#: lever beside the finding and never applies one** — every entry here changes
#: what is indexed or how it ranks, and both are somebody else's decision.
LEVERS: dict[str, str] = {
    "boilerplate term": "`[index]` stopwords, or an analyzer amendment — an index change, with its own record",
    "template family": "`.fuxignore`, `archived=`, or `supersedes` on the one that is current",
    "near-duplicate pair": "`.fuxignore`, `archived=`, or `supersedes` on the one that is current",
    "unfindable document": "`fux enrich`, `fux correct`, or fix the source",
    "orphan": "link-IDF and the graph-composed `ask` (W-161) — until then, add a link from a document that is read",
    "hub": "link-IDF and the graph-composed `ask` (W-161) — until then, nothing: a hub is a fact about the corpus",
    "file-name-only document": "a decoder (`fux-decoder`), or leave it in `.fux/enrich/queue.tsv` for a model to describe",
    "unreadable document": "re-ingest, or `keep = true` on the url line so the bytes are retained",
}

#: 64 permutations in 16 bands of 4 rows. The banding threshold — the Jaccard
#: at which a pair is more likely than not to collide in at least one band — is
#: `(1/bands) ** (1/rows)` = `(1/16) ** (1/4)` ≈ **0.5**, so every pair at or
#: above `NEAR_DUPLICATE_JACCARD` is found with high probability and the
#: candidate set stays far smaller than all pairs. Broder 1997.
SIGNATURE_SIZE = 64
BAND_ROWS = 4

#: The estimated Jaccard at which two documents are reported as near
#: duplicates. **0.8, not 0.9**: the failure this lens exists to name is a
#: template filled in twice, which shares its headings and most of its
#: vocabulary while differing in the part that matters.
NEAR_DUPLICATE_JACCARD = 0.80

#: Fixed permutation seeds — `min(x ^ seed)` over a document's term hashes.
#: XOR with a constant is a bijection on the 64-bit space, so each seed is a
#: genuine permutation and the minimum under it is a genuine minhash. Fixed
#: constants, never `random`: L3.
_SEEDS: tuple[int, ...] = tuple(
    (0x9E3779B97F4A7C15 * (i + 1)) & 0xFFFFFFFFFFFFFFFF for i in range(SIGNATURE_SIZE)
)


@dataclass
class Boilerplate:
    """What is on everything, and how the vocabulary is shaped."""

    #: `(term hash, word, df, df share, idf)`, highest `df` first
    top: list[tuple[str, str, int, float, float]] = field(default_factory=list)
    terms: int = 0
    hapax: int = 0
    boilerplate_terms: int = 0
    boilerplate_postings: int = 0
    postings: int = 0
    zipf_slope: float | None = None
    heaps_beta: float | None = None
    heaps_k: float | None = None

    @property
    def hapax_share(self) -> float:
        return self.hapax / self.terms if self.terms else 0.0

    @property
    def boilerplate_share(self) -> float:
        """Share of all POSTINGS whose term is on half the corpus or more.

        Postings rather than terms, deliberately: a handful of boilerplate
        terms can be most of the index's bytes, and *"12 of 26 749 terms"*
        makes that sound negligible when it is not.
        """
        return self.boilerplate_postings / self.postings if self.postings else 0.0


@dataclass
class Findability:
    """Whether a query can reach a document at all — *the* quality metric.

    Two numbers with different strengths, and the report says which is which:

    - `unfindable` is EXHAUSTIVE. A document with no distinctive term carries
      nothing a query can select it by; no retrieval run is needed to know it.
    - `retrieved` / `sampled` is a SAMPLE. Building each document's own
      fingerprint and asking the engine for it is one full query per document,
      so it runs over an evenly spaced sample and reports the size.
    """

    distinctive: list[tuple[str, int]] = field(default_factory=list)
    unfindable: list[str] = field(default_factory=list)
    sampled: int = 0
    retrieved: int = 0
    misses: list[tuple[str, int | None]] = field(default_factory=list)
    sample_is_whole_corpus: bool = False

    @property
    def findable_share(self) -> float | None:
        return self.retrieved / self.sampled if self.sampled else None


@dataclass
class Lengths:
    """Field totals, the body-length distribution, and the empty fields."""

    total_flen: tuple[int, ...] = ()
    field_names: tuple[str, ...] = ()
    body_percentiles: dict[str, int] = field(default_factory=dict)
    vocabulary_percentiles: dict[str, int] = field(default_factory=dict)
    empty_title: list[str] = field(default_factory=list)
    no_headings: list[str] = field(default_factory=list)
    ctx_over_body: list[tuple[str, int, int]] = field(default_factory=list)
    shortest: list[tuple[str, int]] = field(default_factory=list)
    longest: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class Duplication:
    """⚠ **`near_duplicates` and `families` are TRUNCATED; the counts are not.**

    Every list in this report that is cut to a top-k ships the full count
    beside it. A capped list read as a total is how *"20 near-duplicate pairs"*
    comes to mean *"exactly 20"* when the real number is 900 — and the
    truncation would be invisible, because 20 is exactly what a cap of 20 looks
    like.
    """

    near_duplicates: list[tuple[str, str, float]] = field(default_factory=list)
    pair_count: int = 0
    documents_in_a_pair: int = 0
    families: list[tuple[str, list[str]]] = field(default_factory=list)
    family_count: int = 0
    documents_in_a_family: int = 0
    docs: int = 0

    @property
    def near_duplicate_share(self) -> float:
        return self.documents_in_a_pair / self.docs if self.docs else 0.0


@dataclass
class Coverage:
    """What the analyzer and the decoders could and could not see."""

    raw_runs: int = 0
    kept: int = 0
    #: Documents that contributed **no content terms at all** — nothing in
    #: `body`, `heading` or `ctx`. ⚠ **Not `flen == 0`, which is unreachable:**
    #: `title` falls back to the filename and `path` is always tokenised, so
    #: every indexed document carries some term. A document in this list is one
    #: the index knows only by its own file name — an image, a scanned PDF, a
    #: page that decoded to nothing. That is the W-86 P6 queue case, and it is
    #: the only shape of *"the analyzer never saw the text"* that can occur.
    no_content: list[str] = field(default_factory=list)
    undecodable: list[str] = field(default_factory=list)
    unreadable: list[tuple[str, str]] = field(default_factory=list)
    queued: list[tuple[str, str]] = field(default_factory=list)
    named_terms: int = 0
    total_terms: int = 0

    @property
    def kept_share(self) -> float | None:
        return self.kept / self.raw_runs if self.raw_runs else None

    @property
    def dictionary_coverage(self) -> float | None:
        return self.named_terms / self.total_terms if self.total_terms else None


@dataclass
class GraphShape:
    """Same truncation rule as `Duplication`: every capped list carries its
    full count, so a top-20 list is never read as a total."""

    nodes: int = 0
    edges: int = 0
    orphans: list[str] = field(default_factory=list)
    orphan_count: int = 0
    hubs: list[tuple[str, int]] = field(default_factory=list)
    communities: list[tuple[str, int]] = field(default_factory=list)
    community_count: int = 0
    singleton_communities: int = 0


# --------------------------------------------------------------------------
# 1 · boilerplate
# --------------------------------------------------------------------------


def boilerplate(view, dictionary, *, top: int = 20) -> Boilerplate:
    out = Boilerplate(terms=len(view.term_of), postings=view.postings)
    threshold = view.boilerplate_df
    for term_id, df in enumerate(view.df):
        if df == 1:
            out.hapax += 1
        if df >= threshold:
            out.boilerplate_terms += 1
            out.boilerplate_postings += df
    order = sorted(
        range(len(view.term_of)),
        # `df` descending, then the hash ascending: two terms on exactly the
        # same number of documents must not swap places between runs (L3).
        key=lambda i: (-view.df[i], view.term_of[i]),
    )[:top]
    out.top = [
        (
            view.term_of[i],
            dictionary.name(view.term_of[i]),
            view.df[i],
            view.df[i] / view.n if view.n else 0.0,
            view.idf(i),
        )
        for i in order
    ]
    out.zipf_slope = _zipf_slope(view)
    out.heaps_beta, out.heaps_k = _heaps_fit(view)
    return out


def _zipf_slope(view) -> float | None:
    """Least-squares slope of `log cf` against `log rank`. Zipf predicts ≈ -1.

    Fitted over the **top 1 000 ranks** rather than the whole vocabulary: the
    tail is dominated by hapax terms, which are a flat line at `cf = 1` and
    drag the slope toward zero on every corpus, telling the reader nothing
    about their own.
    """
    frequencies = sorted((int(c) for c in view.cf), reverse=True)[:1000]
    frequencies = [f for f in frequencies if f > 0]
    if len(frequencies) < 10:
        return None
    xs = [math.log(r) for r in range(1, len(frequencies) + 1)]
    ys = [math.log(f) for f in frequencies]
    return _slope(xs, ys)


def _heaps_fit(view) -> tuple[float | None, float | None]:
    """`V = K · T^beta`, fitted in log space over the per-document curve.

    `beta` is the one number here that says something a reader can act on: a
    corpus of near-identical documents saturates its vocabulary early and comes
    out LOW, because each new document brings almost no new words.
    """
    points = [(t, v) for t, v in view.heaps if t > 0 and v > 0]
    if len(points) < 10:
        return None, None
    xs = [math.log(t) for t, _ in points]
    ys = [math.log(v) for _, v in points]
    beta = _slope(xs, ys)
    if beta is None:
        return None, None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    return beta, math.exp(mean_y - beta * mean_x)


def _slope(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    denominator = sum((x - mean_x) ** 2 for x in xs)
    if denominator == 0:
        return None
    return sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denominator


# --------------------------------------------------------------------------
# 2 · findability
# --------------------------------------------------------------------------

#: How many of a document's own most distinctive terms make up the fingerprint
#: query. **Six**, which is about the length of a real question once stopwords
#: are gone — a fingerprint of thirty terms would retrieve the document by
#: sheer overlap and would measure nothing.
FINGERPRINT_TERMS = 6

#: The rank the document must reach in its own fingerprint's results. Three,
#: as `fux enrich --check`'s self-retrieval filter uses.
FINDABLE_RANK = 3

#: The default sample for the retrieval half. One full query per document, so
#: the whole corpus is only affordable on a small one; `--retrieval-sample 0`
#: asks for every document and says how long that will take.
DEFAULT_RETRIEVAL_SAMPLE = 100


def findability(
    root,
    view,
    dictionary,
    *,
    sample: int = DEFAULT_RETRIEVAL_SAMPLE,
    top_lists: int = 20,
    progress=None,
) -> Findability:
    from ..progress import NULL as _NULL_PROGRESS

    progress = progress or _NULL_PROGRESS
    out = Findability()
    threshold = view.distinctive_df
    counts: list[int] = []
    for index, doc in enumerate(view.docs):
        distinctive = sum(1 for t in view.doc_terms[index] if view.df[t] <= threshold)
        counts.append(distinctive)
        if distinctive == 0:
            out.unfindable.append(doc.id)
    out.distinctive = sorted(
        ((view.docs[i].id, c) for i, c in enumerate(counts)), key=lambda pair: (pair[1], pair[0])
    )[:top_lists]

    indices = _sample_indices(view.n, sample)
    out.sample_is_whole_corpus = len(indices) == view.n
    out.sampled = len(indices)
    with progress.phase("retrieval", len(indices), "queries") as p:
        for index in indices:
            p.update(1)
            query = _fingerprint(view, dictionary, index)
            rank = _self_rank(root, view.docs[index].id, query) if query else None
            if rank is not None and rank <= FINDABLE_RANK:
                out.retrieved += 1
            else:
                out.misses.append((view.docs[index].id, rank))
    return out


def _sample_indices(n: int, sample: int) -> list[int]:
    """Evenly spaced document indices — deterministic, never `random.sample`.

    Evenly spaced rather than the first `k`, because `docs` is sorted by id and
    the first `k` of that is one directory: on this repo it would be all of
    `archive/` and none of `src/`.
    """
    if n == 0:
        return []
    if sample <= 0 or sample >= n:
        return list(range(n))
    step = n / sample
    return sorted({min(n - 1, int(i * step)) for i in range(sample)})


def _fingerprint(view, dictionary, index: int) -> str:
    """This document's own most distinctive words, as a query string.

    ⚠ **Only surfaces that round-trip are used.** The dictionary's spelling is
    the one a human typed; the index is keyed by the analyzed form. A surface
    whose re-analysis does not contain the term would ask the engine for a
    different word than the one this document is being tested on, and the miss
    would be the fingerprint's fault rather than the corpus's.
    """
    from ..query.tokenize import tokenize
    from ..store import term_hash

    terms = sorted(
        view.doc_terms[index],
        key=lambda t: (-view.idf(t), view.term_of[t]),
    )
    words: list[str] = []
    for term_id in terms:
        h = view.term_of[term_id]
        surface = dictionary.surfaces.get(h) or dictionary.terms.get(h)
        if not surface:
            continue
        if term_hash_in(tokenize(surface), h, term_hash):
            words.append(surface)
        if len(words) >= FINGERPRINT_TERMS:
            break
    return " ".join(words)


def term_hash_in(analyzed: list[str], wanted: str, hasher) -> bool:
    return any(hasher(a) == wanted for a in analyzed)


def _self_rank(root, doc_id: str, query: str) -> int | None:
    """1-based rank of `doc_id` in `query`'s results, or `None` if absent.

    ⚠ **Never raises.** `inspect` is a report; a query that cannot run is a
    miss with no rank, which is what `None` already means, and a traceback out
    of a diagnostic command is the worst possible answer to *"what is wrong
    with my index"*.
    """
    from ..query import run_query

    try:
        results, _ = run_query(root, query, FINDABLE_RANK, force_scan=False)
    except Exception:  # pragma: no cover - a report must not fail a command
        return None
    for position, result in enumerate(results, start=1):
        if result.id == doc_id:
            return position
    return None


# --------------------------------------------------------------------------
# 3 · length and fields
# --------------------------------------------------------------------------


def lengths(view, *, top_lists: int = 10) -> Lengths:
    from ..store import TF_FIELDS

    out = Lengths(total_flen=view.total_flen, field_names=TF_FIELDS)
    body = [(doc.flen[0] if doc.flen else 0) for doc in view.docs]
    out.body_percentiles = _percentiles(body)
    out.vocabulary_percentiles = _percentiles([doc.nterms for doc in view.docs])
    for doc in view.docs:
        title_tokens = doc.flen[2] if len(doc.flen) > 2 else 0
        heading_tokens = doc.flen[1] if len(doc.flen) > 1 else 0
        ctx_tokens = doc.flen[4] if len(doc.flen) > 4 else 0
        body_tokens = doc.flen[0] if doc.flen else 0
        if title_tokens == 0:
            out.empty_title.append(doc.id)
        if heading_tokens == 0:
            out.no_headings.append(doc.id)
        if ctx_tokens > body_tokens:
            out.ctx_over_body.append((doc.id, ctx_tokens, body_tokens))
    ordered = sorted(
        ((doc.id, doc.flen[0] if doc.flen else 0) for doc in view.docs),
        key=lambda pair: (pair[1], pair[0]),
    )
    out.shortest = ordered[:top_lists]
    out.longest = list(reversed(ordered[-top_lists:]))
    return out


def _percentiles(values: list[int]) -> dict[str, int]:
    """p10/p50/p90 plus min and max, by nearest rank — never interpolated.

    Nearest rank so every number printed is a value some document actually
    has. An interpolated median is a token count no document in the corpus
    carries, and a reader who goes looking for that document will not find it.
    """
    if not values:
        return {}
    ordered = sorted(values)
    def at(share: float) -> int:
        return ordered[min(len(ordered) - 1, max(0, int(round(share * (len(ordered) - 1)))))]
    return {
        "min": ordered[0],
        "p10": at(0.10),
        "p50": at(0.50),
        "p90": at(0.90),
        "max": ordered[-1],
    }


# --------------------------------------------------------------------------
# 4 · duplication and templates
# --------------------------------------------------------------------------


def duplication(view, *, top_lists: int = 20) -> Duplication:
    out = Duplication(docs=view.n)
    signatures = [_signature(view, i) for i in range(view.n)]
    candidates: set[tuple[int, int]] = set()
    bands = SIGNATURE_SIZE // BAND_ROWS
    for band in range(bands):
        buckets: dict[tuple, list[int]] = {}
        lo = band * BAND_ROWS
        for index, signature in enumerate(signatures):
            if signature is None:
                continue
            buckets.setdefault(tuple(signature[lo : lo + BAND_ROWS]), []).append(index)
        for members in buckets.values():
            if len(members) < 2:
                continue
            for i, a in enumerate(members):
                for b in members[i + 1 :]:
                    candidates.add((a, b))

    in_a_pair: set[int] = set()
    pairs: list[tuple[str, str, float]] = []
    for a, b in sorted(candidates):
        # 🔴 **The signature is used for BANDING ONLY, never as a second
        # filter**, and the difference is not cosmetic. A 64-permutation
        # estimate of a true Jaccard of 0.818 has a standard error near 0.048,
        # so filtering on `estimate >= 0.80` throws away a genuine pair
        # **roughly a third of the time** — found by
        # `tests/test_inspect.py::test_the_reported_number_is_the_exact_jaccard_not_the_estimate`,
        # which planted exactly that pair and got an empty list. Banding
        # narrows the candidate set; the exact set intersection decides.
        exact = _jaccard(view.doc_terms[a], view.doc_terms[b])
        if exact < NEAR_DUPLICATE_JACCARD:
            continue
        in_a_pair.update((a, b))
        pairs.append((view.docs[a].id, view.docs[b].id, exact))
    out.documents_in_a_pair = len(in_a_pair)
    out.pair_count = len(pairs)
    # Strongest resemblance first; the id pair breaks ties so the list is a
    # function of the corpus and not of set iteration order.
    out.near_duplicates = sorted(pairs, key=lambda row: (-row[2], row[0], row[1]))[:top_lists]

    families: dict[tuple[str, ...], list[str]] = {}
    for doc in view.docs:
        # Two or more headings: one shared heading is a coincidence
        # (`## Context` is in every record here), a whole shared heading SET is
        # a template. The set, not the sequence — a filled-in template
        # reorders sections and is still the same template.
        if len(doc.phrases) < 2:
            continue
        families.setdefault(tuple(sorted(doc.phrases)), []).append(doc.id)
    in_a_family: set[str] = set()
    named: list[tuple[str, list[str]]] = []
    for headings, members in families.items():
        if len(members) < 2:
            continue
        in_a_family.update(members)
        named.append((" · ".join(headings[:4]), sorted(members)))
    out.documents_in_a_family = len(in_a_family)
    out.family_count = len(named)
    out.families = sorted(named, key=lambda row: (-len(row[1]), row[0]))[:top_lists]
    return out


def _signature(view, index: int) -> list[int] | None:
    """The document's minhash signature, or `None` when it has no terms."""
    terms = view.doc_terms[index]
    if not len(terms):
        return None
    values = [view.term_value[t] for t in terms]
    return [min(value ^ seed for value in values) for seed in _SEEDS]


def _jaccard(a, b) -> float:
    """The EXACT Jaccard over the two term-id sets.

    ⚠ **The estimate finds candidates; the exact number is what is reported.**
    A 64-permutation estimate has a standard error near 0.06, so publishing it
    would put a number in the report that moves when the seeds move — and the
    seeds are an implementation detail nobody should have to know about.
    """
    left, right = set(a), set(b)
    union = len(left | right)
    return len(left & right) / union if union else 0.0


# --------------------------------------------------------------------------
# 5 · analyzer coverage
# --------------------------------------------------------------------------


def coverage(root, view, dictionary) -> Coverage:
    out = Coverage()
    for raw_runs, kept in dictionary.token_counts.values():
        out.raw_runs += raw_runs
        out.kept += kept
    for doc in view.docs:
        body = doc.flen[0] if doc.flen else 0
        heading = doc.flen[1] if len(doc.flen) > 1 else 0
        ctx = doc.flen[4] if len(doc.flen) > 4 else 0
        if body + heading + ctx == 0:
            out.no_content.append(doc.id)
    out.undecodable = sorted(dictionary.undecodable)
    out.unreadable = sorted(dictionary.unreadable.items())
    out.queued = _queue(root)
    out.named_terms, out.total_terms = dictionary.coverage(view.term_of)
    return out


def _queue(root) -> list[tuple[str, str]]:
    """`.fux/enrich/queue.tsv` — what fux could not read and a model must.

    Joined in rather than re-derived: the queue is a committed team fact
    (SR-ENRICH), and a second opinion about which documents are unreadable is
    exactly the drift this lens exists to surface.
    """
    path = root / ".fux" / "enrich" / "queue.tsv"
    if not path.is_file():
        return []
    rows: list[tuple[str, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            rows.append((parts[0], parts[1]))
    return sorted(rows)


# --------------------------------------------------------------------------
# 6 · graph
# --------------------------------------------------------------------------


def graph_shape(view, *, top_lists: int = 20) -> GraphShape:
    from ..graph.community import assign
    from ..graph.model import TAG_PREFIX, Edge, Graph

    graph = Graph([Edge(*row) for row in view.edges])
    out = GraphShape(nodes=len(graph.nodes), edges=len(graph.edges))
    linked = {node for node in graph.nodes}
    # A tag node is minted by `ingest/edges.py`, not indexed as a document, so
    # it is never an orphan and never a document-level hub. Excluded by name
    # rather than by shape, because the namespace has an owner.
    orphans = sorted(doc.id for doc in view.docs if doc.id not in linked)
    out.orphan_count = len(orphans)
    out.orphans = orphans[:top_lists]
    inbound: dict[str, int] = {}
    for _src, _kind, dst, _grade in view.edges:
        inbound[dst] = inbound.get(dst, 0) + 1
    out.hubs = sorted(
        ((node, count) for node, count in inbound.items() if not node.startswith(TAG_PREFIX)),
        key=lambda pair: (-pair[1], pair[0]),
    )[:top_lists]
    communities = assign(graph)
    sizes: dict[str, int] = {}
    for label in communities.values():
        sizes[label] = sizes.get(label, 0) + 1
    out.singleton_communities = sum(1 for size in sizes.values() if size == 1)
    out.community_count = len(sizes)
    out.communities = sorted(sizes.items(), key=lambda pair: (-pair[1], pair[0]))[:top_lists]
    return out
