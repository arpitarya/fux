"""The retrieval kernel — one algorithm, six verb projections (proposal §5).

Every verb is a *view* of the same computation, not its own pipeline:

| verb | seed | projection |
|------|------|------------|
| `ask` | text | passages |
| `find` | text | seed docs |
| `answer` | text | extractive synthesis over passages |
| `explain <doc>` | node | one node deep: outline + edges + key passages |
| `graph "<topic>"` | text | nodes + edges |
| `path <a> <b>` | two nodes | the paths slice, filtered a→b |

`explain` is `ask` seeded by a node: the node's own distinguishing terms
(`top_terms`, computed at ingest) become the query, so there is genuinely one
code path rather than two that must be kept in agreement.

**Parity is the constraint that shapes this module.** The v0.22 hybrid pipeline
moved here verbatim — same candidate pool, same RRF, same tie-breaks, same
rounding — because `ask`/`find`/`answer` must keep producing byte-identical
output. Graph signals are *added lists*, never edits to the existing ones, and
`--lexical-only` still bypasses everything downstream of BM25F.

Expansion is deliberately shallow here: direct adjacency and BFS trails, both
deterministic. PPR-lite scoring and the graph list joining RRF arrive at M6.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

from .config import Config
from .errors import FuxError
from .index import load_edges, load_searcher
from .index.bm25f import ScoredChunk, Searcher
from .index.fuse import rrf

# Edge reliability by grade (handoff §E): extracted facts are trusted fully,
# inferred ones discounted, and every hop decays.
GRADE_WEIGHT = {"EXTRACTED": 1.0, "INFERRED": 0.6}
HOP_DECAY = 0.8


@dataclass(frozen=True)
class NodeRef:
    """A seed that is a document rather than a question."""

    doc_id: str


@dataclass(frozen=True)
class SeedDoc:
    doc_id: str
    score: float
    bm25f_rank: int | None = None
    dense_rank: int | None = None
    dense_global_rank: int | None = None


@dataclass(frozen=True)
class Node:
    doc_id: str
    title: str = ""
    outline: str = ""
    top_terms: str = ""
    fidelity: str = "inferred"
    via: str = "seed"  # seed | expanded
    score: float = 0.0


@dataclass(frozen=True)
class Edge:
    src: str
    kind: str
    dst: str
    grade: str = "EXTRACTED"


@dataclass(frozen=True)
class Path:
    hops: tuple[Edge, ...]
    reliability: float

    @property
    def start(self) -> str:
        return self.hops[0].src if self.hops else ""

    @property
    def end(self) -> str:
        return self.hops[-1].dst if self.hops else ""


@dataclass(frozen=True)
class ResultGraph:
    seeds: list[SeedDoc] = field(default_factory=list)
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    paths: list[Path] = field(default_factory=list)
    passages: list[ScoredChunk] = field(default_factory=list)
    engine: str = "bm25f"
    model: object | None = None


def retrieve(
    config: Config,
    seed: str | NodeRef,
    *,
    k: int = 5,
    lexical_only: bool = False,
    expand_hops: int = 1,
    searcher: Searcher | None = None,
    files: dict | None = None,
) -> ResultGraph:
    """The one retrieval path. Text or node in, a ResultGraph out."""
    from .index import backend_for

    searcher = searcher if searcher is not None else load_searcher(config)
    files = files if files is not None else backend_for(config).load(config.root)

    if isinstance(seed, NodeRef):
        if seed.doc_id not in files:
            raise FuxError(
                f"no document {seed.doc_id!r} in the corpus — try `fux find` to locate it"
            )
        # "explain is ask seeded by a node": the document's own distinguishing
        # terms are the question, so there is no second retrieval path.
        query = files[seed.doc_id].get("top_terms") or files[seed.doc_id].get("title", "")
        pinned = seed.doc_id
    else:
        query, pinned = seed, None

    passages, engine, model = _passages(config, searcher, query, k, lexical_only)
    if pinned is not None:
        passages = [p for p in passages if p.file == pinned] or _own_chunks(
            searcher, pinned, k
        )

    seeds = _seed_docs(passages)
    edges = _edges_for(config, {s.doc_id for s in seeds})
    nodes = _nodes(files, seeds, edges, expand_hops)
    paths = _paths(edges, {s.doc_id for s in seeds}, expand_hops)
    return ResultGraph(
        seeds=seeds, nodes=nodes, edges=edges, paths=paths,
        passages=passages, engine=engine, model=model,
    )


# -- passages: the v0.22 hybrid pipeline, moved verbatim -------------------


def _passages(
    config: Config, searcher: Searcher, query: str, pool: int, lexical_only: bool
) -> tuple[list[ScoredChunk], str, object | None]:
    """BM25F ∪ dense-over-candidates → RRF. Unchanged from v0.22 by contract."""
    if lexical_only or not config.hybrid.enabled:
        return searcher.search(query, top=pool), "bm25f", None
    from .embed import get_model

    model = get_model()
    if model is None:
        return searcher.search(query, top=pool), "bm25f", None
    query_vec = model.embed(query)
    if query_vec is None:  # all-OOV query: dense has nothing to say
        return searcher.search(query, top=pool), "bm25f", None
    candidates = searcher.search(query, top=config.hybrid.candidate_pool)
    if not candidates:
        return [], "bm25f", None
    from .embed.store import load_vectors

    vectors = load_vectors(config.root)
    dense: list[tuple[ScoredChunk, float]] = []
    missing = False
    for r in candidates:
        entry = vectors.get(r.file)
        vec = None
        if entry and r.ordinal < len(entry["vecs"]):
            vec = entry["vecs"][r.ordinal]
        elif entry is None:
            missing = True
        if vec is not None:
            dense.append((r, model.similarity(query_vec, vec)))
    if missing:
        print(
            "warning: some chunks lack semantic vectors — run `fux ingest` to refresh",
            file=sys.stderr,
        )
    if not dense:
        return candidates[:pool], "bm25f", None
    dense.sort(key=lambda t: (-t[1], t[0].file, t[0].ordinal))
    similarity = {id(r): sim for r, sim in dense}
    by_id = {id(r): r for r in candidates}
    fused = rrf(
        [[id(r) for r in candidates], [id(r) for r, _ in dense]], k=config.hybrid.rrf_k
    )
    ordered = sorted(
        fused.items(), key=lambda kv: (-kv[1], by_id[kv[0]].file, by_id[kv[0]].ordinal)
    )
    lex_rank = {id(r): i for i, r in enumerate(candidates, start=1)}
    dense_rank = {id(r): i for i, (r, _) in enumerate(dense, start=1)}
    results = []
    for key, score in ordered[:pool]:
        r = by_id[key]
        r.hybrid = {
            "bm25f_rank": lex_rank[key],
            "bm25f_score": round(r.score, 3),
            "dense_rank": dense_rank.get(id(r)),
            "similarity": round(similarity[id(r)], 4) if id(r) in similarity else None,
            "rrf": round(score, 5),
        }
        r.score = score
        results.append(r)
    return results, "hybrid", model


def _own_chunks(searcher: Searcher, doc_id: str, k: int) -> list[ScoredChunk]:
    """Fallback for `explain` on a document its own terms did not surface."""
    out = []
    for chunk in searcher.chunks:
        if chunk["file"] != doc_id:
            continue
        out.append(
            ScoredChunk(
                file=chunk["file"], heading=chunk["heading"], text=chunk["text"],
                start=chunk["start"], end=chunk["end"], score=0.0,
                ordinal=chunk["ordinal"],
            )
        )
        if len(out) >= k:
            break
    return out


# -- projections -----------------------------------------------------------


def _seed_docs(passages: list[ScoredChunk]) -> list[SeedDoc]:
    """Documents behind the passages, best-passage-first — `find`'s projection."""
    best: dict[str, ScoredChunk] = {}
    for p in passages:
        if p.file not in best or p.score > best[p.file].score:
            best[p.file] = p
    ordered = sorted(best.items(), key=lambda kv: (-round(kv[1].score, 9), kv[0]))
    return [
        SeedDoc(
            doc_id=doc_id,
            score=p.score,
            bm25f_rank=(p.hybrid or {}).get("bm25f_rank"),
            dense_rank=(p.hybrid or {}).get("dense_rank"),
        )
        for doc_id, p in ordered
    ]


def _edges_for(config: Config, doc_ids: set[str]) -> list[Edge]:
    """Edges touching the seed set — the neighbourhood, sorted for reproducibility."""
    if not doc_ids:
        return []
    return [
        Edge(src, kind, dst, grade)
        for src, kind, dst, grade in load_edges(config)
        if src in doc_ids or dst in doc_ids
    ]


def _nodes(files: dict, seeds: list[SeedDoc], edges: list[Edge], hops: int) -> list[Node]:
    seed_ids = {s.doc_id for s in seeds}
    scores = {s.doc_id: s.score for s in seeds}
    reached = set(seed_ids)
    if hops > 0:
        for edge in edges:
            if edge.src in seed_ids:
                reached.add(edge.dst)
            if edge.dst in seed_ids:
                reached.add(edge.src)
    out = []
    for doc_id in sorted(reached, key=lambda d: (-scores.get(d, 0.0), d)):
        meta = files.get(doc_id, {})
        out.append(
            Node(
                doc_id=doc_id,
                title=meta.get("title", ""),
                outline=meta.get("outline", ""),
                top_terms=meta.get("top_terms", ""),
                fidelity=meta.get("fidelity", "inferred"),
                via="seed" if doc_id in seed_ids else "expanded",
                score=scores.get(doc_id, 0.0),
            )
        )
    return out


def _paths(edges: list[Edge], seed_ids: set[str], hops: int) -> list[Path]:
    """Deterministic BFS trails out of the seeds, reliability-scored.

    Reliability is the product of per-edge grade weights times a per-hop decay,
    so a long chain of inferred edges never outranks a direct extracted one.
    """
    if not seed_ids or hops < 1:
        return []
    adjacency: dict[str, list[Edge]] = {}
    for edge in edges:
        adjacency.setdefault(edge.src, []).append(edge)
    for neighbours in adjacency.values():
        neighbours.sort(key=lambda e: (e.dst, e.kind))  # sorted traversal = reproducible

    out: list[Path] = []
    for start in sorted(seed_ids):
        frontier: list[tuple[str, tuple[Edge, ...], float]] = [(start, (), 1.0)]
        for _ in range(hops):
            nxt = []
            for node, trail, reliability in frontier:
                for edge in adjacency.get(node, []):
                    if any(h.src == edge.dst for h in trail) or edge.dst == start:
                        continue  # no cycles: a trail that returns explains nothing
                    weight = GRADE_WEIGHT.get(edge.grade, 0.6) * (HOP_DECAY ** len(trail))
                    scored = reliability * weight
                    hop_trail = trail + (edge,)
                    out.append(Path(hops=hop_trail, reliability=round(scored, 6)))
                    nxt.append((edge.dst, hop_trail, scored))
            frontier = nxt
    out.sort(key=lambda p: (-p.reliability, p.start, p.end, len(p.hops)))
    return out


def paths_between(graph: ResultGraph, source: str, target: str) -> list[Path]:
    """`fux path a b` — the paths slice, filtered to trails that actually land."""
    return [p for p in graph.paths if p.start == source and p.end == target]
