"""ask / find / answer over the index — the query surface (CLI + library).

Output formats follow docs/cli-examples.md — the committed UX contract; the
e2e goldens derive from it. `--json` is the agent path and fully deterministic;
human output may include timing.
"""

from __future__ import annotations

import json
import sys
import time
from collections import defaultdict

from ..config import BM25FParams, Config, find_root, load
from ..index import load_searcher
from ..index.bm25f import ScoredChunk, Searcher
from ..ingest.manifest import quick_drift, read as manifest_read
from ..index.bm25f import tokenize
from .answer import _STOPWORDS, Sentence, build_answer
from .explain import chunk_explain_json, sentence_explain_line

_FIND_POOL = 200  # chunks scored before per-file aggregation
_ANSWER_POOL = 10


def cmd_query(args) -> int:
    started = time.perf_counter()
    root = find_root()
    config = load(root)
    searcher = load_searcher(config)
    manifest = manifest_read(root)
    _warn_if_stale(config)
    ctx = _Ctx(
        config=config,
        manifest=manifest,
        corpus={"docs": len(manifest), "chunks": len(searcher.chunks)},
        started=started,
    )
    return {"ask": _run_ask, "find": _run_find, "answer": _run_answer}[args.mode](
        searcher, ctx, args
    )


class _Ctx:
    def __init__(self, config: Config, manifest: dict, corpus: dict, started: float):
        self.config = config
        self.manifest = manifest
        self.corpus = corpus
        self.started = started

    def fidelity(self, rel: str) -> str:
        return self.manifest.get(rel, {}).get("fidelity", "inferred")

    def elapsed_ms(self) -> int:
        return max(1, round((time.perf_counter() - self.started) * 1000))


def _warn_if_stale(config: Config) -> None:
    if not quick_drift(config).clean:
        print(
            "warning: sources changed since the last ingest — run `fux ingest` to refresh",
            file=sys.stderr,
        )


def _no_hits(args, ctx: _Ctx) -> int:
    if args.json:
        print(
            json.dumps(
                {"query": args.query, "results": [], "corpus": ctx.corpus, "engine": "bm25f"},
                ensure_ascii=False,
            )
        )
        return 0
    content_terms = [t for t in tokenize(args.query) if t not in _STOPWORDS][:2]
    hint = " ".join(content_terms) or args.query
    print("No confident matches.")
    print(f'Try: fux find "{hint}" · broaden the question · fux ingest new sources')
    return 0


def _loc(file: str, line: int | None) -> str:
    return file if line is None else f"{file}:{line}"


# -- ask -------------------------------------------------------------------


def _run_ask(searcher: Searcher, ctx: _Ctx, args) -> int:
    results = searcher.search(args.query, top=args.top)
    if not results:
        return _no_hits(args, ctx)
    if args.json:
        payload = {
            "query": args.query,
            "results": [_chunk_json(r, ctx, args.explain) for r in results],
            "corpus": ctx.corpus,
            "engine": "bm25f",
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    print()
    for r in results:
        print(f"{_loc(r.file, r.start)}  (score {r.score:.3f})")
        lines = r.text.split("\n")
        shown = lines if args.context == 0 else lines[: args.context]
        for line in shown:
            print(f"  {line}")
        if len(shown) < len(lines):
            print(f"  … ({len(lines) - len(shown)} more lines; use -C 0 for all)")
        if args.explain:
            for line in _explain_tree(r, ctx.config.bm25f):
                print(f"  {line}")
        print()
    plural = "passage" if len(results) == 1 else "passages"
    print(
        f"{len(results)} {plural} · corpus {ctx.corpus['docs']} docs · {ctx.elapsed_ms()}ms"
    )
    return 0


def _chunk_json(r: ScoredChunk, ctx: _Ctx, explain: bool) -> dict:
    out = {
        "path": r.file,
        "line_start": r.start,
        "line_end": r.end,
        "score": round(r.score, 3),
        "heading_path": [p for p in r.heading.split(" > ") if p],
        "fidelity": ctx.fidelity(r.file),
        "text": r.text,
    }
    if explain:
        out["explain"] = chunk_explain_json(r)
    return out


def _explain_tree(r: ScoredChunk, params: BM25FParams) -> list[str]:
    """Per-field breakdown (cli-examples.md format): contribution apportioned to
    each field by its share of the weighted tf — truthful under joint saturation."""
    weights = {"heading": params.heading, "path": params.path, "body": params.body}
    terms: dict[str, list] = {f: [] for f in weights}
    totals: dict[str, float] = {f: 0.0 for f in weights}
    for term, info in sorted(r.terms.items()):
        tf = info["tf"]
        wtf = sum(weights[f] * tf[f] for f in weights)
        if not wtf:
            continue
        for f in weights:
            if tf[f]:
                terms[f].append(f"{term}×{tf[f]}")
                totals[f] += info["contribution"] * (weights[f] * tf[f] / wtf)
    rows = [f for f in ("heading", "path", "body") if terms[f]]
    lines = []
    for i, f in enumerate(rows):
        glyph = "└─" if i == len(rows) - 1 else "├─"
        lines.append(
            f"{glyph} {f}: {', '.join(terms[f])}  (weight {weights[f]} → +{totals[f]:.3f})"
        )
    return lines


# -- find ------------------------------------------------------------------


def _run_find(searcher: Searcher, ctx: _Ctx, args) -> int:
    results = searcher.search(args.query, top=_FIND_POOL)
    if not results:
        return _no_hits(args, ctx)
    per_file: dict[str, dict] = defaultdict(lambda: {"score": 0.0, "chunks": 0, "best": None})
    for r in results:
        agg = per_file[r.file]
        agg["chunks"] += 1
        if r.score > agg["score"]:
            agg["score"], agg["best"] = r.score, r
    ranked = sorted(per_file.items(), key=lambda kv: (-round(kv[1]["score"], 9), kv[0]))
    ranked = ranked[: args.top]
    if args.json:
        payload = {
            "query": args.query,
            "results": [
                {
                    "path": file,
                    "score": round(agg["score"], 3),
                    "matching_passages": agg["chunks"],
                    "fidelity": ctx.fidelity(file),
                    **({"explain": chunk_explain_json(agg["best"])} if args.explain else {}),
                }
                for file, agg in ranked
            ],
            "corpus": ctx.corpus,
            "engine": "bm25f",
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    for i, (file, agg) in enumerate(ranked, start=1):
        print(f"{i}.  {agg['score']:.3f}  {file}")
        if args.explain:
            for line in _explain_tree(agg["best"], ctx.config.bm25f):
                print(f"    {line}")
    return 0


# -- answer ----------------------------------------------------------------


def _run_answer(searcher: Searcher, ctx: _Ctx, args) -> int:
    results = searcher.search(args.query, top=_ANSWER_POOL)
    max_sentences = args.answer_max or ctx.config.answer.max_sentences
    sentences = build_answer(results, args.query, max_sentences)
    if not sentences:
        if args.json:
            print(
                json.dumps(
                    {
                        "query": args.query,
                        "answer": None,
                        "sentences": [],
                        "sources": [],
                        "corpus": ctx.corpus,
                        "engine": "bm25f",
                    },
                    ensure_ascii=False,
                )
            )
            return 0
        print("No confident answer — the corpus may not cover this.")
        print('Try: fux find "…" to locate related files · fux ingest new sources')
        return 0

    citations = _assign_citations(sentences)
    if args.json:
        payload = {
            "query": args.query,
            "answer": " ".join(s.text for s in sentences),
            "sentences": [_sentence_json(s, citations, args.explain) for s in sentences],
            "sources": [
                {"id": cid, "path": file, "line": line}
                for (file, line), cid in citations.items()
            ],
            "corpus": ctx.corpus,
            "engine": "bm25f",
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    print()
    body = " ".join(f"{s.text} [{citations[(s.file, s.line)]}]" for s in sentences)
    print(body)
    if args.explain:
        for s in sentences:
            print(f"  [{citations[(s.file, s.line)]}] {sentence_explain_line(s)}")
    print("\nSources:")
    for (file, line), cid in citations.items():
        print(f"  [{cid}] {_loc(file, line)}")
    print("\n(extractive — sentences are verbatim from sources)")
    return 0


def _assign_citations(sentences: list[Sentence]) -> dict[tuple, int]:
    citations: dict[tuple, int] = {}
    for s in sentences:
        key = (s.file, s.line)
        if key not in citations:
            citations[key] = len(citations) + 1
    return citations


def _sentence_json(s: Sentence, citations: dict[tuple, int], explain: bool) -> dict:
    out = {
        "text": s.text,
        "path": s.file,
        "line": s.line,
        "citation": citations[(s.file, s.line)],
        "score": round(s.score, 3),
    }
    if explain:
        out["factors"] = s.factors
    return out
