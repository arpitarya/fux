"""The accelerated candidate generator — same results, less work.

`ask()` here is the T1 path. It returns exactly what `query/scan.py` returns,
asserted byte-for-byte by `tools/differential/`, and it does so without
touching the committed shards at all: the doc table, the postings and the
statistics all come from `.fux/runtime/`.

## What this module is allowed to do

Generate **candidates and statistics**. It never scores and never sorts —
`query/rank.py` does both, for both paths, in query-hash order. That is not
tidiness: float addition is not associative, so a term-major accumulation
would produce different low-order bits and a different `--json` payload while
being logically correct. Keeping one scorer makes the differential law a
property of the candidate set rather than a hope about arithmetic.

## The skipping argument, in full

Query terms are opened rarest-first. After each term, every candidate seen so
far has an *exact, complete* score (deferred terms are filled in by
range-intersecting block reads), so the k-th best score `theta` is exact. A
document that has not been seen yet matches only the terms still deferred, so
its score is at most

    sum over deferred h of  max over h's blocks of  bound(h, block)

If that sum cannot reach `theta`, no unseen document can enter the top k, and
every unopened block is skippable. Otherwise the next term is opened and the
test is retried — so the worst case is opening everything, which is the scan's
work and never wrong.

`bound(h, block)` is an upper bound because a term's BM25F contribution

    idf(h) * wtf * (K1+1) / (wtf + K1*(1 - B + B*wlen/avg_wlen))

is strictly **increasing in `wtf`** (derivative `C(K1+1)/(wtf+C)^2 > 0`) and
strictly **decreasing in `wlen`**. So the block's maximum weighted tf (`mx`)
with the block's minimum length (`mnw`) dominates every posting in it. Both
are integers, stored in the offset table.

**The comparison is rounding-aware**, and that detail is load-bearing.
`rank()` orders by `(-round(score, 9), id)`, so a document scoring
`theta - 1e-12` still ties the k-th after rounding and can win on `id`. The
skip test is therefore `round(bound, 9) < round(theta, 9)`: since `round` is
monotone and `bound >= score`, that inequality proves the document loses
outright rather than tying. A naive `bound < theta` would be wrong here, and
wrong only on ties — which is exactly the class of bug a spot-check misses.
"""

from __future__ import annotations

import json
from bisect import bisect_left
from dataclasses import dataclass
from pathlib import Path

from ..errors import FuxError
from ..query.bm25f import DEFAULT_SCORING, Scoring, derive_wlen, idf
from ..query.rank import AskResult, Corpus, rank
from ..query.scan import query_term_hashes
from ..query.rank import Weighting
from . import format as fmt

__all__ = ["ask", "accel_candidates", "block_bound", "is_fresh", "Runtime"]


@dataclass(frozen=True)
class Block:
    """One offset-table entry: where a block is, and what it can possibly score."""

    term: str
    block_no: int
    offset: int
    length: int
    #: PER-FIELD extrema, unweighted (W-76 Phase 1). Recombined with the
    #: weights in force at query time by `block_bound`, so editing
    #: `tune.toml` never invalidates a built accelerator.
    mx: tuple[int, ...]
    mnw: tuple[int, ...]
    first_doc: int
    last_doc: int
    count: int


class Runtime:
    """Lazily-loaded handle on `.fux/runtime/`.

    Nothing is read until it is needed: a query touching two terms reads two
    offset shards and the block lines those terms point at, and never opens
    the other 254.
    """

    def __init__(self, root: Path):
        self.root = root
        self.dir = fmt.runtime_dir(root)
        self._docs: list[dict] | None = None
        self._stats: dict | None = None
        self._offsets: dict[str, bytes] = {}
        self._postings: dict[str, bytes] = {}

    @property
    def stats(self) -> dict:
        if self._stats is None:
            self._stats = json.loads((self.dir / fmt.STATS_NAME).read_bytes())
        return self._stats

    @property
    def docs(self) -> list[dict]:
        if self._docs is None:
            raw = (self.dir / fmt.DOCS_NAME).read_bytes()
            self._docs = [json.loads(line) for line in raw.split(b"\n") if line]
        return self._docs

    def offsets(self, prefix: str) -> bytes:
        if prefix not in self._offsets:
            path = fmt.offsets_path(self.root, prefix)
            self._offsets[prefix] = path.read_bytes() if path.exists() else b""
        return self._offsets[prefix]

    def postings(self, prefix: str) -> bytes:
        if prefix not in self._postings:
            path = fmt.postings_path(self.root, prefix)
            self._postings[prefix] = path.read_bytes() if path.exists() else b""
        return self._postings[prefix]

    def blocks_for(self, term: str) -> list[Block]:
        """Every block of a term, by one bisect over the fixed-width table."""
        prefix = fmt.term_prefix(term)
        buf = self.offsets(prefix)
        if not buf:
            return []
        count = len(buf) // fmt.ENTRY_SIZE
        key = bytes.fromhex(term)

        lo, hi = 0, count
        while lo < hi:  # first entry whose term >= key
            mid = (lo + hi) // 2
            if fmt.unpack_entry(buf, mid)[0] < key:
                lo = mid + 1
            else:
                hi = mid

        out: list[Block] = []
        while lo < count:
            raw = fmt.unpack_entry(buf, lo)
            if raw[0] != key:
                break
            out.append(Block(term, raw[1], raw[2], raw[3], raw[4], raw[5], raw[6], raw[7], raw[8]))
            lo += 1
        return out

    def read_block(self, block: Block) -> list[tuple[int, list[int]]]:
        """Parse one block line into its postings. The only JSON parse on this path."""
        buf = self.postings(fmt.term_prefix(block.term))
        line = buf[block.offset : block.offset + block.length]
        _, entries = json.loads(line)
        return [(e[0], e[1]) for e in entries]


def block_bound(
    block: Block, df: int, n: int, avg_wlen: float, scoring: Scoring = DEFAULT_SCORING
) -> float:
    """The largest BM25F contribution any posting in `block` can make.

    Contribution increases in weighted tf and decreases in document length, so
    a block is dominated by (its maximum weighted tf, its minimum length).

    **Since W-76 Phase 1 the extrema are stored per field and recombined
    here**, at the weights in force, rather than stored pre-weighted. That is
    what lets a field weight be a `tune.toml` key without a rebuild — and it
    makes the bound LOOSER, provably in the safe direction:

        sum_i w_i * max_d tf_i(d)  >=  max_d sum_i w_i * tf_i(d)      (mx)
        sum_i w_i * min_d len_i(d) <=  min_d sum_i w_i * len_i(d)     (mnw)

    An over-estimated numerator and an under-estimated length both push the
    bound UP. A bound that is too high skips fewer blocks; a bound that is too
    low loses documents. Only the first is possible here.
    """
    weights = scoring.weights
    wtf = 0.0
    for i, value in enumerate(block.mx):
        if value:
            wtf += weights[i] * value
    if wtf == 0:
        return 0.0
    mnw = 0.0
    for i, value in enumerate(block.mnw):
        if value:
            mnw += weights[i] * value
    k1, b = scoring.k1, scoring.b
    denom = wtf + k1 * (1 - b + b * mnw / avg_wlen)
    return idf(df, n) * wtf * (k1 + 1) / denom


def is_fresh(root: Path) -> bool:
    """Cheap staleness check: shard sizes and mtimes against the build stamp.

    Deliberately not a re-hash of every shard — that is correct but costs
    hundreds of milliseconds on a large index and would land inside R3's
    budget. The deep check lives in `fux doctor`, which is allowed to be slow.
    """
    directory = fmt.runtime_dir(root)
    stamp_path = directory / fmt.STAMP_NAME
    manifest_path = directory / fmt.MANIFEST_NAME
    if not stamp_path.exists() or not manifest_path.exists():
        return False
    try:
        manifest = json.loads(manifest_path.read_bytes())
        stamp = json.loads(stamp_path.read_bytes())["shards"]
    except (OSError, ValueError, KeyError):
        return False
    if manifest.get("schema") != fmt.RUNTIME_SCHEMA:
        return False
    # The doc table's field set, not just the schema string. A field added to
    # the table without a schema bump is invisible to the check above and
    # produces a runtime the scorer reads facts OUT of that are not IN it --
    # so `--fast` and `--scan` weight the same document differently, silently.
    if list(manifest.get("docs_fields", ())) != list(fmt.DOCS_FIELDS):
        return False

    from .. import store as store_mod

    paths = store_mod.iter_shard_paths(root)
    if len(paths) != len(stamp):
        return False
    for path in paths:
        entry = stamp.get(path.name)
        if entry is None:
            return False
        st = path.stat()
        if [st.st_size, st.st_mtime_ns] != entry:
            return False
    return True


def accel_candidates(
    runtime: Runtime,
    query_hashes: list[str],
    top: int,
    *,
    skipping: bool = True,
    weighting: "Weighting | None" = None,
    scoring: Scoring = DEFAULT_SCORING,
    expansion=None,
) -> tuple[list[dict], dict[str, int], Corpus]:
    """Candidate records, `df`, and the corpus statistics — the scan's contract.

    Records are synthesized rather than read from the committed store: `rank()`
    reads only `terms` (at the query hashes), `wlen`, `id`, `title` and `loc`,
    all of which the doc table and the postings carry.

    `expansion` is W-109's `Expansion`. `query_hashes` is already its full hash
    list when one is in force — **this function never adds a term**, it only
    needs the object so the block bound can price each term at the weight
    `rank()` will actually score it with.
    """
    if weighting is None:
        weighting = Weighting()
    stats = runtime.stats
    if "total_flen" not in stats:
        # A `fux.runtime.v3` plane, built before the field weights became
        # tunable. `is_fresh` already refuses it, so the CLI degrades to the
        # scan path rather than arriving here — this is the direct-call door,
        # and a KeyError would name nothing a consumer can act on.
        raise FuxError(
            "the accelerator was built by an older fux (no `total_flen` in "
            "stats.json) -- run `fux build` to rebuild the derived plane. "
            "Nothing committed changed; the runtime is disposable"
        )
    # `total_flen` is the five RAW per-field token-count totals; the weights
    # are applied here, at query time, exactly as `scan.py` applies them. The
    # plane stored a pre-weighted `total_wlen` until 2026-08-24, which meant a
    # `tune.toml` field weight moved `avg_wlen` on the scan path and not on
    # this one — the same corpus, two `avg_wlen`s, and a differential-law break
    # that a rebuild would have been needed to repair.
    corpus = Corpus(
        n=stats["n"],
        total_wlen=derive_wlen(list(stats["total_flen"]), scoring),
        newest_mtime=stats.get("newest_mtime", 0),
    )
    if corpus.n == 0:
        return [], dict.fromkeys(query_hashes, 0), corpus
    avg_wlen = corpus.avg_wlen
    docs = runtime.docs

    blocks: dict[str, list[Block]] = {h: runtime.blocks_for(h) for h in query_hashes}
    df = {h: sum(b.count for b in blocks[h]) for h in query_hashes}

    # Rarest first: the cheapest term seeds the candidate set, and the most
    # expensive one is the most likely to be skipped outright.
    order = sorted(query_hashes, key=lambda h: (df[h], h))

    # docidx -> {term: per-field tf list}
    hits: dict[int, dict[str, list[int]]] = {}
    opened: set[str] = set()
    read_blocks: dict[str, set[int]] = {h: set() for h in query_hashes}

    for term in order:
        if skipping and hits and _cannot_reach(
            runtime, blocks, df, opened, order, hits, docs, corpus, top, avg_wlen,
            weighting, scoring, expansion,
        ):
            break
        for block in blocks[term]:
            read_blocks[term].add(block.block_no)
            for docidx, tf in runtime.read_block(block):
                hits.setdefault(docidx, {})[term] = tf
        opened.add(term)

    # Deferred terms still owe their tf for documents already in the candidate
    # set: without them a candidate would be scored on a subset of the query
    # and diverge from the scan. Only blocks whose docidx range covers a
    # candidate are read.
    _fill_deferred(runtime, blocks, opened, query_hashes, hits, read_blocks)

    candidates = [
        {
            "id": docs[docidx]["id"],
            "loc": docs[docidx]["loc"],
            "title": docs[docidx]["title"],
            "flen": docs[docidx]["flen"],
            "archived": docs[docidx].get("archived", False),
            "superseded": docs[docidx].get("superseded", False),
            "mtime": docs[docidx].get("mtime"),
            "terms": {term: list(tf) for term, tf in terms.items()},
        }
        for docidx, terms in hits.items()
    ]
    return candidates, df, corpus


def _cannot_reach(
    runtime, blocks, df, opened, order, hits, docs, corpus, top, avg_wlen,
    weighting=None, scoring: Scoring = DEFAULT_SCORING, expansion=None,
) -> bool:
    """True when no unseen document can enter the top `top`.

    `theta` is the k-th best *weighted* score over the candidates gathered so
    far. An unseen document matches only deferred terms, so its ceiling is the
    sum of those terms' best block bounds — **scaled by the largest weight the
    configuration can produce** (W-73).

    The scale factor is `weighting.maximum`, not the weight of any candidate:
    the document this test is about has not been seen, so nothing is known
    about its weight except that the configuration bounds it.

    ## 🔴 W-109: each term's bound is priced at THAT TERM's weight

    `--expand` gives individual terms a multiplier, and an unweighted ceiling
    over weighted scores is the **W-73 class of defect** — a bound that no
    longer bounds. It is priced per term rather than by a single maximum
    because the arithmetic is exact either way and the exact form is tighter:
    an expansion term's true contribution is `w · base`, so `w · bound` is
    still an upper bound on it. **Safe in both directions** — `w < 1` tightens
    the ceiling correctly and `w > 1` loosens it correctly — which is what lets
    `expand_weight` be a tunable rather than a capped constant.

    ⚠ **`weighting.maximum` still multiplies the whole sum afterwards.** The
    two scalings compose: one prices the *terms*, the other the *document*, and
    dropping either reintroduces a different unbounded bound.
    """
    if weighting is None:
        weighting = Weighting()
    deferred = [h for h in order if h not in opened]
    if not deferred:
        return True

    ceiling = 0.0
    for term in deferred:
        term_blocks = blocks[term]
        if not term_blocks:
            continue
        bound = max(block_bound(b, df[term], corpus.n, avg_wlen, scoring) for b in term_blocks)
        if expansion is not None and not expansion.trivial:
            bound *= expansion.weight_of(term)
        ceiling += bound

    if not weighting.trivial:
        ceiling *= weighting.maximum

    theta = _kth_score(
        hits, docs, [h for h in order if h in opened], df, corpus, top, avg_wlen,
        weighting, scoring, expansion,
    )
    if theta is None:
        return False
    # Rounding-aware: `rank()` compares round(score, 9), so a bound that merely
    # falls below theta could still tie after rounding and win on id.
    return round(ceiling, 9) < round(theta, 9)


def _kth_score(
    hits, docs, opened_order, df, corpus, top, avg_wlen,
    weighting=None, scoring: Scoring = DEFAULT_SCORING, expansion=None,
) -> float | None:
    """The `top`-th best **weighted** score among current candidates.

    `None` when there are fewer than `top` candidates.

    Scored over the **opened terms only**, so it under-estimates each
    candidate's final score once deferred terms are filled in. That is the safe
    direction: a lower `theta` skips less, never more. Multiplying by a
    non-negative `w(d)` preserves that direction, because
    `w(d)*S_opened(d) <= w(d)*S_full(d)` — which is what makes it legal to
    weight an under-estimate rather than having to weight the final score.

    ⚠ **`expansion`'s per-term weights apply here too, and must.** `theta` is
    compared against a ceiling computed with them; computing it without would
    compare two numbers in different units and skip blocks a document needed.

    🔴 **And a candidate `rank()` will DROP may not set `theta`.** With
    `--expand`, a document matching only expansion terms is discarded by the
    hallucination guard — so counting it here raises the threshold on the
    strength of a document nobody will ever be shown, and the accelerator skips
    blocks holding documents that should have entered the top `k`. **Measured,
    not reasoned**: `tests/derive/test_expand_bound.py` diverged at every
    `expand_weight >= 0.5` at `top = 20` until this filter existed, including
    at `1.0` where the weights change no arithmetic at all — the guard alone
    was enough to break the bound.

    The filter is on the terms **seen so far**, so a document whose required
    term is still deferred is excluded and `theta` is under-estimated. That is
    the safe direction, and it is the same direction this function's
    opened-terms-only scoring already errs in.
    """
    if weighting is None:
        weighting = Weighting()
    guarded = (
        {i: t for i, t in hits.items() if expansion.matches(t)}
        if expansion is not None and not expansion.trivial
        else hits
    )
    if len(guarded) < top:
        return None
    from ..query.bm25f import score_record

    term_weights = (expansion.weights or None) if expansion is not None else None
    scores = []
    for docidx, terms in guarded.items():
        record_terms = {term: list(tf) for term, tf in terms.items()}
        s = score_record(
            record_terms, docs[docidx]["flen"], opened_order, df, corpus.n, avg_wlen, scoring,
            term_weights,
        )
        if not weighting.trivial:
            s *= weighting.of(docs[docidx])
        scores.append(s)
    scores.sort(reverse=True)
    return scores[top - 1]


def _fill_deferred(runtime, blocks, opened, query_hashes, hits, read_blocks) -> None:
    """Complete known candidates from the few blocks that actually cover them.

    The intersection test reads `first_doc`/`last_doc` straight from the offset
    table, so a block that covers no candidate is never parsed — which is the
    whole reason those two fields are in the entry.
    """
    if not hits:
        return
    wanted = sorted(hits)
    for term in query_hashes:
        if term in opened:
            continue
        for block in blocks[term]:
            if block.block_no in read_blocks[term]:
                continue
            lo = bisect_left(wanted, block.first_doc)
            if lo >= len(wanted) or wanted[lo] > block.last_doc:
                continue  # covers no candidate — not read, not parsed
            read_blocks[term].add(block.block_no)
            for docidx, tf in runtime.read_block(block):
                if docidx in hits:
                    hits[docidx][term] = tf


def ask(
    root: Path,
    query: str,
    top: int = 5,
    *,
    skipping: bool = True,
    archived_weight: float = 1.0,
    archived_dirs: frozenset[str] = frozenset(),
    weighting: "Weighting | None" = None,
    scoring: Scoring = DEFAULT_SCORING,
    stats_out: dict | None = None,
    expansion=None,
) -> list[AskResult]:
    """The accelerated `ask`. Identical output to `query.scan.ask`, by law.

    `stats_out` is threaded straight through to `rank()`, which means the
    confidence block is under the differential law like everything else here:
    both paths derive `df` over the same query hashes and report the same `n`,
    so `--fast` and `--scan` cannot disagree about how confident fux is
    (ADR-CONFIDENCE decision 8).
    """
    query_hashes = query_term_hashes(query)
    if not query_hashes:
        if stats_out is not None:
            stats_out.setdefault("df", {})
            stats_out.setdefault("n", 0)
        return []
    runtime = Runtime(root)
    if not (runtime.dir / fmt.STATS_NAME).exists():
        raise FuxError("no accelerator built — run `fux ingest` (or `fux build`) first")
    if weighting is None:
        weighting = Weighting(archived_weight=archived_weight, archived_dirs=archived_dirs)
    collect = list(expansion.hashes) if expansion is not None else query_hashes
    candidates, df, corpus = accel_candidates(
        runtime, collect, top, skipping=skipping, weighting=weighting, scoring=scoring,
        expansion=expansion,
    )
    return rank(
        candidates, collect, df, corpus, top,
        archived_weight=archived_weight, archived_dirs=archived_dirs,
        weighting=weighting, scoring=scoring, stats_out=stats_out,
        expansion=expansion,
    )
