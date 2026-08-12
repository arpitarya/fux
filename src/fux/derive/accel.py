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
from ..query.bm25f import B, K1, idf
from ..query.rank import AskResult, Corpus, rank
from ..query.scan import query_term_hashes
from . import format as fmt

__all__ = ["ask", "accel_candidates", "block_bound", "is_fresh", "Runtime"]


@dataclass(frozen=True)
class Block:
    """One offset-table entry: where a block is, and what it can possibly score."""

    term: str
    block_no: int
    offset: int
    length: int
    mx: int
    mnw: int
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

    def read_block(self, block: Block) -> list[tuple[int, int, int]]:
        """Parse one block line into its postings. The only JSON parse on this path."""
        buf = self.postings(fmt.term_prefix(block.term))
        line = buf[block.offset : block.offset + block.length]
        _, entries = json.loads(line)
        return [(e[0], e[1], e[2]) for e in entries]


def block_bound(block: Block, df: int, n: int, avg_wlen: float) -> float:
    """The largest BM25F contribution any posting in `block` can make.

    Uses `mx` (max weighted tf, contribution increases in it) with `mnw` (min
    document length, contribution decreases in it). Proof in the module
    docstring; exhaustively tested against every posting in
    `tests/derive/test_bounds.py`.
    """
    wtf = float(block.mx)
    if wtf == 0:
        return 0.0
    denom = wtf + K1 * (1 - B + B * block.mnw / avg_wlen)
    return idf(df, n) * wtf * (K1 + 1) / denom


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
) -> tuple[list[dict], dict[str, int], Corpus]:
    """Candidate records, `df`, and the corpus statistics — the scan's contract.

    Records are synthesized rather than read from the committed store: `rank()`
    reads only `terms` (at the query hashes), `wlen`, `id`, `title` and `loc`,
    all of which the doc table and the postings carry.
    """
    stats = runtime.stats
    corpus = Corpus(n=stats["n"], total_wlen=stats["total_wlen"])
    if corpus.n == 0:
        return [], dict.fromkeys(query_hashes, 0), corpus
    avg_wlen = corpus.avg_wlen
    docs = runtime.docs

    blocks: dict[str, list[Block]] = {h: runtime.blocks_for(h) for h in query_hashes}
    df = {h: sum(b.count for b in blocks[h]) for h in query_hashes}

    # Rarest first: the cheapest term seeds the candidate set, and the most
    # expensive one is the most likely to be skipped outright.
    order = sorted(query_hashes, key=lambda h: (df[h], h))

    # docidx -> {term: (tf_h, tf_b)}
    hits: dict[int, dict[str, tuple[int, int]]] = {}
    opened: set[str] = set()
    read_blocks: dict[str, set[int]] = {h: set() for h in query_hashes}

    for term in order:
        if skipping and hits and _cannot_reach(runtime, blocks, df, opened, order, hits, docs, corpus, top, avg_wlen):
            break
        for block in blocks[term]:
            read_blocks[term].add(block.block_no)
            for docidx, tf_h, tf_b in runtime.read_block(block):
                hits.setdefault(docidx, {})[term] = (tf_h, tf_b)
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
            "wlen": docs[docidx]["wlen"],
            "terms": {term: [tf_h, tf_b] for term, (tf_h, tf_b) in terms.items()},
        }
        for docidx, terms in hits.items()
    ]
    return candidates, df, corpus


def _cannot_reach(runtime, blocks, df, opened, order, hits, docs, corpus, top, avg_wlen) -> bool:
    """True when no unseen document can enter the top `top`.

    `theta` is the k-th best *exact* score over the candidates gathered so far.
    An unseen document matches only deferred terms, so its ceiling is the sum
    of those terms' best block bounds.
    """
    deferred = [h for h in order if h not in opened]
    if not deferred:
        return True

    ceiling = 0.0
    for term in deferred:
        term_blocks = blocks[term]
        if not term_blocks:
            continue
        ceiling += max(block_bound(b, df[term], corpus.n, avg_wlen) for b in term_blocks)

    theta = _kth_score(hits, docs, [h for h in order if h in opened], df, corpus, top, avg_wlen)
    if theta is None:
        return False
    # Rounding-aware: `rank()` compares round(score, 9), so a bound that merely
    # falls below theta could still tie after rounding and win on id.
    return round(ceiling, 9) < round(theta, 9)


def _kth_score(hits, docs, opened_order, df, corpus, top, avg_wlen) -> float | None:
    """The `top`-th best score among current candidates, or None if too few.

    Scored over the **opened terms only**, so it under-estimates each
    candidate's final score once deferred terms are filled in. That is the safe
    direction: a lower `theta` skips less, never more.
    """
    if len(hits) < top:
        return None
    from ..query.bm25f import score_record

    scores = []
    for docidx, terms in hits.items():
        record_terms = {term: [tf_h, tf_b] for term, (tf_h, tf_b) in terms.items()}
        scores.append(
            score_record(record_terms, docs[docidx]["wlen"], opened_order, df, corpus.n, avg_wlen)
        )
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
            for docidx, tf_h, tf_b in runtime.read_block(block):
                if docidx in hits:
                    hits[docidx][term] = (tf_h, tf_b)


def ask(root: Path, query: str, top: int = 5, *, skipping: bool = True) -> list[AskResult]:
    """The accelerated `ask`. Identical output to `query.scan.ask`, by law."""
    query_hashes = query_term_hashes(query)
    if not query_hashes:
        return []
    runtime = Runtime(root)
    if not (runtime.dir / fmt.STATS_NAME).exists():
        raise FuxError("no accelerator built — run `fux ingest` (or `fux build`) first")
    candidates, df, corpus = accel_candidates(runtime, query_hashes, top, skipping=skipping)
    return rank(candidates, query_hashes, df, corpus, top)
