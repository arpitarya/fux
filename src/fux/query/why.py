"""`fux why` — negative-result explanation (handoff 0005 §D).

`--explain` only explains results that *appeared*; `why` walks the pipeline for
one named document and reports the first place it fell out, ending in a single
verdict sentence — that sentence is the whole feature, everything above it is
evidence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from ..config import Config, find_root, load
from ..index.bm25f import tokenize


@dataclass
class WhyResult:
    doc_id: str
    in_corpus: bool
    corpus_detail: str
    chunks: list[dict] = field(default_factory=list)
    lexical: dict | None = None
    dense: dict | None = None
    graph: dict | None = None
    verdict: str = ""

    def to_json(self) -> dict:
        out = {
            "doc": self.doc_id,
            "in_corpus": self.in_corpus,
            "corpus_detail": self.corpus_detail,
            "chunks": self.chunks,
            "verdict": self.verdict,
        }
        if self.lexical is not None:
            out["lexical"] = self.lexical
        if self.dense is not None:
            out["dense"] = self.dense
        if self.graph is not None:
            out["graph"] = self.graph
        return out


def why(config: Config, query: str, doc_id: str, *, lexical_only: bool = False, top: int = 5) -> WhyResult:
    in_corpus, corpus_detail = _presence(config, doc_id)
    if not in_corpus:
        return WhyResult(
            doc_id=doc_id, in_corpus=False, corpus_detail=corpus_detail,
            verdict=f"not in corpus: {corpus_detail}",
        )

    from ..index import backend_for

    files = backend_for(config).load(config.root)
    meta = files.get(doc_id, {})
    q_terms = set(tokenize(query))
    chunks = [
        {
            "heading": c["heading"],
            "start": c.get("start"),
            "end": c.get("end"),
            "matches_query_terms": bool(q_terms & set(tokenize(c["heading"] + " " + c["text"]))),
        }
        for c in meta.get("chunks", [])
    ]
    if not chunks:
        return WhyResult(
            doc_id=doc_id, in_corpus=True, corpus_detail=corpus_detail, chunks=[],
            verdict="not returned: document is in the corpus but produced zero chunks",
        )

    from ..index import load_searcher
    from ..kernel import retrieve

    searcher = load_searcher(config)
    lexical = _lexical_detail(config, searcher, query, doc_id)
    dense = None if lexical_only else _dense_detail(config, searcher, query, doc_id)

    graph_result = retrieve(
        config, query, k=max(len(searcher.chunks), 1), lexical_only=lexical_only,
        searcher=searcher, files=files,
    )
    fused_rank = None
    for i, p in enumerate(graph_result.passages, start=1):
        if p.file == doc_id:
            fused_rank = i
            break
    graph_detail = _graph_detail(graph_result, doc_id)

    verdict = _verdict(doc_id, fused_rank, top, lexical, dense, graph_detail, config)
    return WhyResult(
        doc_id=doc_id, in_corpus=True, corpus_detail=corpus_detail, chunks=chunks,
        lexical=lexical, dense=dense, graph=graph_detail, verdict=verdict,
    )


def _presence(config: Config, doc_id: str) -> tuple[bool, str]:
    from ..index import doc_id_for
    from ..ingest.manifest import read as manifest_read

    manifest = manifest_read(config.root)
    by_doc = {doc_id_for(e): e for e in manifest.values()}
    entry = by_doc.get(doc_id)
    if entry is not None:
        return True, f"cache={entry.get('cache') or '(bulk tier — no file)'}  fidelity={entry.get('fidelity', 'inferred')}"

    from ..ingest.convert import skip_reason
    from ..ingest.walk import walk

    result = walk(config)
    for sf in result.files:
        if sf.rel == doc_id:
            reason = skip_reason(sf, sf.abspath.read_bytes())
            return False, reason or "matched a [sources] entry but has not been ingested yet — run `fux ingest`"
    on_disk = (config.root / doc_id).is_file()
    if on_disk:
        return False, "on disk but outside every configured [sources] entry (excluded, or no matching glob) — check fux.toml"
    return False, "no such file on disk, and no corpus entry with this id"


def _lexical_detail(config: Config, searcher, query: str, doc_id: str) -> dict:
    full = searcher.search(query, top=max(len(searcher.chunks), 1))
    rank = None
    score = None
    terms: dict = {}
    for i, r in enumerate(full, start=1):
        if r.file == doc_id:
            rank, score, terms = i, r.score, r.terms
            break
    pool = config.hybrid.candidate_pool
    return {
        "rank": rank,
        "score": round(score, 4) if score is not None else None,
        "in_candidate_pool": rank is not None and rank <= pool,
        "candidate_pool": pool,
        "terms": {
            term: {"idf": t["idf"], "tf": t["tf"], "contribution": t["contribution"]}
            for term, t in terms.items()
        },
    }


def _dense_detail(config: Config, searcher, query: str, doc_id: str) -> dict | None:
    from ..embed import get_model
    from ..embed.fuxvec import quantize
    from ..embed.store import load_vectors
    from ..state import load_state

    model = get_model()
    if model is None:
        return {"available": False, "reason": "no bundled model — lexical-only environment"}
    query_vec = model.embed(query)
    if query_vec is None:
        return {"available": False, "reason": "all-OOV query — the model has no vector for it"}

    vectors = load_vectors(config.root)
    entry = vectors.get(doc_id)
    similarity = None
    if entry:
        sims = [model.similarity(query_vec, v) for v in entry.get("vecs", []) if v is not None]
        similarity = max(sims) if sims else None

    state = load_state(config.root)
    codes = {d: e.code for d, e in state.items() if e.code is not None}
    in_prefilter = False
    hamming = None
    if doc_id in codes and codes:
        q_code = quantize(query_vec)
        hamming = (
            int.from_bytes(q_code, "little") ^ int.from_bytes(codes[doc_id], "little")
        ).bit_count()
        from ..embed.fuxvec import prefilter

        in_prefilter = doc_id in prefilter(q_code, codes, config.index.prefilter_width)
    return {
        "available": True,
        "similarity": round(similarity, 4) if similarity is not None else None,
        "has_code": doc_id in codes,
        "hamming_distance": hamming,
        "in_prefilter": in_prefilter,
        "prefilter_width": config.index.prefilter_width,
    }


def _graph_detail(graph_result, doc_id: str) -> dict:
    seed_ids = {s.doc_id for s in graph_result.seeds}
    if doc_id in seed_ids:
        return {"reached": True, "as": "seed", "via_seed": None, "edge_kind": None}
    for edge in graph_result.edges:
        if edge.dst == doc_id and edge.src in seed_ids:
            return {"reached": True, "as": "expanded", "via_seed": edge.src, "edge_kind": edge.kind}
        if edge.src == doc_id and edge.dst in seed_ids:
            return {"reached": True, "as": "expanded", "via_seed": edge.dst, "edge_kind": edge.kind}
    return {"reached": False, "as": None, "via_seed": None, "edge_kind": None}


def _verdict(doc_id, fused_rank, top, lexical, dense, graph_detail, config) -> str:
    if fused_rank is not None and fused_rank <= top:
        return f"returned: rank {fused_rank} at --top {top}"
    if fused_rank is not None:
        return f"not returned at --top {top}: rank {fused_rank} overall (raise --top to {fused_rank} to see it)"

    parts = []
    if lexical["rank"] is not None:
        pool_note = "" if lexical["in_candidate_pool"] else f" (outside the top {lexical['candidate_pool']} candidates)"
        parts.append(f"rank {lexical['rank']} lexical{pool_note}")
    else:
        parts.append("no lexical overlap")

    if dense is None:
        pass  # --lexical-only: dense was never consulted
    elif not dense["available"]:
        parts.append(dense["reason"])
    elif dense["similarity"] is None:
        parts.append("no semantic vector for this document")
    elif dense["in_prefilter"]:
        parts.append(f"dense candidate (cosine {dense['similarity']:.2f}, in the FuxVec prefilter)")
    else:
        parts.append(
            f"no dense candidate (cosine {dense['similarity']:.2f}, not among the "
            f"{dense['prefilter_width']} nearest FuxVec codes)"
        )

    if graph_detail["reached"]:
        parts.append(f"reached via graph from {graph_detail['via_seed']} ({graph_detail['edge_kind']})")
    else:
        parts.append("no edge from any seed")

    return "not returned: " + ", ".join(parts)


# -- CLI handler ---------------------------------------------------------------


def cmd_why(args) -> int:
    root = find_root()
    config = load(root)
    result = why(
        config, args.query, args.doc,
        lexical_only=getattr(args, "lexical_only", False), top=args.top,
    )
    if args.json:
        print(json.dumps(result.to_json(), ensure_ascii=False))
        return 0
    print(f"{result.doc_id}")
    print(f"  in corpus: {result.in_corpus}  ({result.corpus_detail})")
    if result.chunks:
        print(f"  chunks: {len(result.chunks)}")
        for c in result.chunks:
            mark = "✓" if c["matches_query_terms"] else "·"
            loc = f":{c['start']}-{c['end']}" if c["start"] is not None else ""
            heading = c["heading"] or "(no heading)"
            print(f"    {mark} {heading}{loc}")
    if result.lexical is not None:
        lx = result.lexical
        print(
            f"  lexical: rank={lx['rank']} score={lx['score']} "
            f"in_pool={lx['in_candidate_pool']} (pool={lx['candidate_pool']})"
        )
        for term, t in sorted(lx["terms"].items()):
            print(f"    {term}: idf={t['idf']} tf={t['tf']} contribution={t['contribution']}")
    if result.dense is not None:
        dn = result.dense
        if dn["available"]:
            print(
                f"  dense: similarity={dn['similarity']} in_prefilter={dn['in_prefilter']} "
                f"hamming={dn['hamming_distance']} (width={dn['prefilter_width']})"
            )
        else:
            print(f"  dense: unavailable ({dn['reason']})")
    if result.graph is not None:
        gr = result.graph
        print(
            f"  graph: reached={gr['reached']} as={gr['as']} "
            f"via={gr['via_seed']} edge={gr['edge_kind']}"
        )
    print()
    print(f"verdict: {result.verdict}")
    return 0
