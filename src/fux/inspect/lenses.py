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

from functools import lru_cache

import math
import re
from dataclasses import dataclass, field

from ..constants import fixed

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
    "families",
    "Families",
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
    "shared title": "a `title:` in front-matter, or a data decoder's `META_FIELDS` title claim (`fux-decoder`)",
    "title probe miss": "`fux enrich`, `fux correct`, or a title the document's own body also uses",
    "word-cut passage": "a decoder that emits one record per paragraph (`fux-decoder`)",
    "page chrome": "a consumer html decoder in `.fux/decoders/` that skips `nav`, `header`, `aside` and `footer` (`fux-decoder`)",
    "link-target tokens": "none a consumer can turn — an extraction-rule change under SR-EXTRACTED, its own item, measured first",
    "identifier family": "`fux identifiers --write` records it in `.fux/identifiers.toml [detected]`, `[user] drop` refuses one — an index change: `fux ingest` after (SR-IDENTIFIERS)",
}

#: 64 permutations in 16 bands of 4 rows. The banding threshold — the Jaccard
#: at which a pair is more likely than not to collide in at least one band — is
#: `(1/bands) ** (1/rows)` = `(1/16) ** (1/4)` ≈ **0.5**, so every pair at or
#: above `NEAR_DUPLICATE_JACCARD` is found with high probability and the
#: candidate set stays far smaller than all pairs. Broder 1997.
#:
#: ⚠ **`[minhash] signature_size` and `band_rows` in `.fux/inspect.toml`** since
#: W-225 stage 4c (SR-LAW-12), read through `view.config`; the template writes
#: 64 and 4, and the arithmetic above assumes those.

#: The estimated Jaccard at which two documents are reported as near
#: duplicates. **0.8, not 0.9**: the failure this lens exists to name is a
#: template filled in twice, which shares its headings and most of its
#: vocabulary while differing in the part that matters.
#: ⚠ **`[thresholds] near_duplicate_jaccard`** since W-225 stage 4c.

#: W-225 stage 5f — the near-duplicate lens's seed multiplier and mask, and the
#: two fit bounds, from `constants.toml [inspect.minhash]` / `[inspect.fits]`.
_GAMMA = int(fixed("inspect.minhash", "gamma"), fixed("radix", "hex"))
_BITS = fixed("inspect.minhash", "bits")
_MIN_POINTS = fixed("inspect.fits", "min_points")
_ZIPF_RANKS = fixed("inspect.fits", "zipf_ranks")
_TF_FIELDS = tuple(fixed("index", "tf_fields"))


def _field(flen, name: str) -> int:
    """A document's token count in one tf field, by NAME (`[index] tf_fields`);
    trailing zeros are omitted on the wire, so a short `flen` reads as 0."""
    i = _TF_FIELDS.index(name)
    return flen[i] if len(flen) > i else 0


#: Fixed permutation seeds — `min(x ^ seed)` over a document's term hashes.
#: XOR with a constant is a bijection on the 64-bit space, so each seed is a
#: genuine permutation and the minimum under it is a genuine minhash. Fixed
#: constants, never `random`: L4.
@lru_cache(maxsize=4)
def _seeds(size: int) -> tuple[int, ...]:
    """`size` permutation seeds — a pure function of the configured length."""
    mask = (1 << _BITS) - 1
    return tuple((_GAMMA * (i + 1)) & mask for i in range(size))


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


def boilerplate(view, dictionary, *, top: int) -> Boilerplate:
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
        # same number of documents must not swap places between runs (L4).
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
    frequencies = sorted((int(c) for c in view.cf), reverse=True)[:_ZIPF_RANKS]
    frequencies = [f for f in frequencies if f > 0]
    if len(frequencies) < _MIN_POINTS:
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
    if len(points) < _MIN_POINTS:
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
    denominator = sum((x - mean_x) * (x - mean_x) for x in xs)
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
#: ⚠ **`[findability] fingerprint_terms`** in `.fux/inspect.toml` since W-225 stage 4c.

#: The rank the document must reach in its own fingerprint's results. Three,
#: as `fux enrich --check`'s self-retrieval filter uses.
#: ⚠ **`[findability] findable_rank`** since W-225 stage 4c.

#: The default sample for the retrieval half. One full query per document, so
#: the whole corpus is only affordable on a small one; `--retrieval-sample 0`
#: asks for every document and says how long that will take.
#: ⚠ **`[findability] retrieval_sample`** since W-225 stage 4c; callers pass it.


def findability(
    root,
    view,
    dictionary,
    *,
    sample: int | None,
    top_lists: int,
    progress=None,
    cache: dict | None = None,
) -> Findability:
    """`sample=None` skips the retrieval half (the exhaustive half always runs).

    `cache`, when given, maps a query to the ids it returned under the current
    ranking key (`probes.ranking_key`) — the same cache the probe lens fills, so
    a second look at an unchanged index asks nothing (W-220).
    """
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

    indices = [] if sample is None else _sample_indices(view.n, sample)
    out.sample_is_whole_corpus = sample is not None and len(indices) == view.n
    out.sampled = len(indices)
    with progress.phase("retrieval", len(indices), "queries") as p:
        for index in indices:
            p.update(1)
            query = _fingerprint(view, dictionary, index)
            findable = view.config.findable_rank
            rank = _self_rank(root, view.docs[index].id, query, findable, cache) if query else None
            if rank is not None and rank <= findable:
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
        if len(words) >= view.config.fingerprint_terms:
            break
    return " ".join(words)


def term_hash_in(analyzed: list[str], wanted: str, hasher) -> bool:
    return any(hasher(a) == wanted for a in analyzed)


def _self_rank(root, doc_id: str, query: str, findable_rank: int, cache: dict | None) -> int | None:
    """1-based rank of `doc_id` in `query`'s results, or `None` if absent.

    ⚠ **Never raises.** `inspect` is a report; a query that cannot run is a
    miss with no rank, which is what `None` already means, and a traceback out
    of a diagnostic command is the worst possible answer to *"what is wrong
    with my index"*.
    """
    from ..query import run_query

    key = f"self@{findable_rank}:{query}"
    ids = cache.get(key) if cache is not None else None
    if ids is None:
        try:
            results, _ = run_query(root, query, findable_rank, force_scan=False, use_tune=True)
        except Exception:  # pragma: no cover - a report must not fail a command
            return None
        ids = [result.id for result in results]
        if cache is not None:
            cache[key] = ids
    for position, other in enumerate(ids, start=1):
        if other == doc_id:
            return position
    return None


# --------------------------------------------------------------------------
# 3 · length and fields
# --------------------------------------------------------------------------


def lengths(view, *, top_lists: int) -> Lengths:
    from ..store import TF_FIELDS

    out = Lengths(total_flen=view.total_flen, field_names=TF_FIELDS)
    body = [(doc.flen[0] if doc.flen else 0) for doc in view.docs]
    out.body_percentiles = _percentiles(body)
    out.vocabulary_percentiles = _percentiles([doc.nterms for doc in view.docs])
    for doc in view.docs:
        title_tokens = _field(doc.flen, "title")
        heading_tokens = doc.flen[1] if len(doc.flen) > 1 else 0
        ctx_tokens = _field(doc.flen, "ctx")
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


def duplication(view, *, top_lists: int) -> Duplication:
    out = Duplication(docs=view.n)
    config = view.config
    seeds = _seeds(config.signature_size)
    rows = config.band_rows
    signatures = [_signature(view, i, seeds) for i in range(view.n)]
    candidates: set[tuple[int, int]] = set()
    bands = config.signature_size // rows
    for band in range(bands):
        buckets: dict[tuple, list[int]] = {}
        lo = band * rows
        for index, signature in enumerate(signatures):
            if signature is None:
                continue
            buckets.setdefault(tuple(signature[lo : lo + rows]), []).append(index)
        for members in buckets.values():
            if len(members) <= 1:
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
        if exact < config.near_duplicate_jaccard:
            continue
        in_a_pair.update((a, b))
        pairs.append((view.docs[a].id, view.docs[b].id, exact))
    out.documents_in_a_pair = len(in_a_pair)
    out.pair_count = len(pairs)
    # Strongest resemblance first; the id pair breaks ties so the list is a
    # function of the corpus and not of set iteration order.
    out.near_duplicates = sorted(pairs, key=lambda row: (-row[-1], row[0], row[1]))[:top_lists]

    families: dict[tuple[str, ...], list[str]] = {}
    for doc in view.docs:
        # Two or more headings: one shared heading is a coincidence
        # (`## Context` is in every record here), a whole shared heading SET is
        # a template. The set, not the sequence — a filled-in template
        # reorders sections and is still the same template.
        if len(doc.phrases) <= 1:
            continue
        families.setdefault(tuple(sorted(doc.phrases)), []).append(doc.id)
    in_a_family: set[str] = set()
    named: list[tuple[str, list[str]]] = []
    for headings, members in families.items():
        if len(members) <= 1:
            continue
        in_a_family.update(members)
        named.append((" · ".join(headings[:4]), sorted(members)))
    out.documents_in_a_family = len(in_a_family)
    out.family_count = len(named)
    out.families = sorted(named, key=lambda row: (-len(row[1]), row[0]))[:top_lists]
    return out


def _signature(view, index: int, seeds: tuple[int, ...]) -> list[int] | None:
    """The document's minhash signature, or `None` when it has no terms."""
    terms = view.doc_terms[index]
    if not len(terms):
        return None
    values = [view.term_value[t] for t in terms]
    return [min(value ^ seed for value in values) for seed in seeds]


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
        ctx = _field(doc.flen, "ctx")
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
    path = root / fixed("files", "enrich_queue")
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
        loc, sep, rest = line.partition("\t")
        if sep:
            rows.append((loc, rest.split("\t")[0]))
    return sorted(rows)


# --------------------------------------------------------------------------
# 6 · graph
# --------------------------------------------------------------------------


def graph_shape(view, *, top_lists: int) -> GraphShape:
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


# --------------------------------------------------------------------------
# 7 · families — documents grouped by shape (W-228)
# --------------------------------------------------------------------------

#: What masks a heading before two are compared: a run of digits. `2026-09-28`,
#: `Step 3` and `v0.26` become `#-#-#`, `step #` and `v#.#`, so a dated or
#: numbered template still reads as one shape.
_DIGITS = re.compile(r"\d+")


def _mask(heading: str) -> str:
    return " ".join(_DIGITS.sub("#", heading).lower().split())


@dataclass
class Families:
    """⚠ **`families`, `misfits`, `singletons` and `no_headings` are TRUNCATED;
    the counts are not** — the `Duplication` rule, for the same reason.

    A document's SHAPE is its heading skeleton (the committed `phrases`, masked,
    so a dated or numbered template is one shape, less a leading heading equal
    to its title) and its front-matter key names (pass A's `meta_keys`). Two
    documents share a family when they share a heading and the Jaccard of those
    feature sets is at least `[families] skeleton_jaccard` against EVERY member
    — complete linkage, one pass in doc-id order, ties to the older family. A
    function of the corpus and nothing else (L4): no k, no seed.
    """

    families: list[dict] = field(default_factory=list)
    family_count: int = 0
    documents_in_a_family: int = 0
    misfits: list[dict] = field(default_factory=list)
    misfit_count: int = 0
    singletons: list[str] = field(default_factory=list)
    singleton_count: int = 0
    no_headings: list[str] = field(default_factory=list)
    no_headings_count: int = 0
    docs: int = 0
    misfit_floor: float = 0.0

    @property
    def families_share(self) -> float:
        return self.documents_in_a_family / self.docs if self.docs else 0.0

    @property
    def misfit_share(self) -> float:
        return self.misfit_count / self.documents_in_a_family if self.documents_in_a_family else 0.0

    @property
    def misfit_flagged(self) -> bool:
        return self.misfit_share > self.misfit_floor


def _band(tokens: int, edges: tuple[int, ...]) -> str:
    """The length band a body-token count falls in — `edges` from inspect.toml."""
    if tokens < edges[0]:
        return f"<{edges[0]}"
    for lo, hi in zip(edges, edges[1:]):
        if tokens < hi:
            return f"{lo}–{hi - 1}"
    return f"≥{edges[-1]}"


def _jaccard_sets(a: frozenset, b: frozenset) -> float:
    union = len(a | b)
    return len(a & b) / union if union else 0.0


def families(view, facts, *, top_lists: int) -> Families:
    """Group documents by shape; name each family, its misfits and its singletons."""
    config = view.config
    by_id = getattr(facts, "by_id", {}) or {}
    out = Families(docs=view.n, misfit_floor=config.misfit_floor)
    shaped: list[tuple[int, frozenset, list[str]]] = []
    originals: dict[str, str] = {}
    # Doc-id order, so the spelling a masked heading is shown with — the first
    # document's — is a function of the corpus and never of read order (L4).
    for index, doc in sorted(enumerate(view.docs), key=lambda pair: pair[1].id):
        heads = [p.strip() for p in doc.phrases if p and p.strip()]
        # A leading heading that IS the document's title is the document's name,
        # not its template's: kept, it made 14 of rung-01000's 16 misfits and
        # split one wiki template four ways by company name (W-228 DoD 11 run).
        # The same test `probes` uses to find a title heading.
        if heads and heads[0] == (doc.title or "").strip():
            heads = heads[1:]
        masked = [_mask(p) for p in heads]
        for p, m in zip(heads, masked):
            originals.setdefault(m, p)
        meta = (by_id.get(doc.id) or {}).get("meta_keys") or []
        features = frozenset({"h:" + m for m in masked} | {"m:" + str(k) for k in meta})
        if not masked:
            # No headings at all — a spreadsheet row set, a chat log. Named as
            # *no headings*, never as a unique shape (W-228 §6).
            out.no_headings.append(doc.id)
            continue
        shaped.append((index, features, masked))
    shaped.sort(key=lambda row: view.docs[row[0]].id)

    groups: list[list[int]] = []          # indices into `shaped`
    # HEADING -> the groups holding it. Only a shared heading makes two documents
    # candidates; front-matter keys refine the score and never found a family —
    # two unrelated notes with six common keys and no common heading clear 0.60.
    postings: dict[str, set[int]] = {}
    cut = config.skeleton_jaccard
    for position, (_index, features, masked) in enumerate(shaped):
        best, best_score = None, -1.0
        for group in sorted({g for m in masked for g in postings.get(m, ())}):
            worst = 1.0
            for member in groups[group]:
                worst = min(worst, _jaccard_sets(features, shaped[member][1]))
                if worst < cut:
                    break
            if worst >= cut and worst > best_score:
                best, best_score = group, worst
        if best is None:
            best = len(groups)
            groups.append([])
        groups[best].append(position)
        for m in masked:
            postings.setdefault(m, set()).add(best)

    edges = config.length_edges
    named: list[dict] = []
    misfits: list[dict] = []
    for members in groups:
        docs = [view.docs[shaped[m][0]] for m in members]
        if len(members) <= 1:
            out.singletons.append(docs[0].id)
            continue
        out.documents_in_a_family += len(members)
        counts: dict[str, int] = {}
        for m in members:
            for h in set(shaped[m][-1]):
                counts[h] = counts.get(h, 0) + 1
        core = {h for h, c in counts.items() if c / len(members) >= config.core_share}
        order = [h for h in shaped[members[0]][-1] if h in core]
        # Named by its shared skeleton — the first four core headings, in the
        # first member's order, as the exact-set families are named.
        name = " · ".join(originals[h] for h in list(dict.fromkeys(order))[:4])
        metas = [set((by_id.get(d.id) or {}).get("meta_keys") or []) for d in docs]
        shared_meta = sorted(set.intersection(*metas)) if metas else []
        folders = sorted({d.loc.rsplit("/", 1)[0] + "/" if "/" in d.loc else "./" for d in docs})
        bands = sorted({_band(d.flen[0] if d.flen else 0, edges) for d in docs}, key=lambda b: _band_order(b, edges))
        ids = sorted(d.id for d in docs)
        named.append({
            "name": name or "(no shared heading)",
            "size": len(members),
            "members": ids,
            "folders": folders,
            "shared_meta_keys": shared_meta,
            "length_bands": bands,
        })
        for m, d in zip(members, docs):
            missing = sorted(core - set(shaped[m][-1]), key=lambda h: order.index(h) if h in order else len(order))
            if missing:
                misfits.append({"id": d.id, "family": name or "(no shared heading)",
                                "missing": [originals[h] for h in missing]})
    out.family_count = len(named)
    out.misfit_count = len(misfits)
    out.singleton_count = len(out.singletons)
    out.no_headings_count = len(out.no_headings)
    out.families = sorted(named, key=lambda row: (-row["size"], row["name"], row["members"][0]))[:top_lists]
    out.misfits = sorted(misfits, key=lambda row: (-len(row["missing"]), row["id"]))[:top_lists]
    out.singletons = sorted(out.singletons)[:top_lists]
    out.no_headings = sorted(out.no_headings)[:top_lists]
    return out


def _band_order(band: str, edges: tuple[int, ...]) -> int:
    labels = [_band(0, edges)] + [_band(e, edges) for e in edges]
    return labels.index(band) if band in labels else len(labels)
