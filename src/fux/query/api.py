"""ask / find / answer over the index — the query surface (CLI + library)."""

from __future__ import annotations

import json
import sys
from collections import defaultdict

from ..config import Config, find_root, load
from ..index import load_searcher
from ..index.bm25f import ScoredChunk, Searcher
from ..ingest.manifest import quick_drift
from .answer import Sentence, build_answer
from .explain import chunk_explain_json, chunk_explain_lines, sentence_explain_line

_FIND_POOL = 200  # chunks scored before per-file aggregation
_ANSWER_POOL = 10


def cmd_query(args) -> int:
    root = find_root()
    config = load(root)
    searcher = load_searcher(config)
    _warn_if_stale(config)
    return {
        "ask": _run_ask,
        "find": _run_find,
        "answer": _run_answer,
    }[args.mode](searcher, config, args)


def _warn_if_stale(config: Config) -> None:
    drift = quick_drift(config)
    if not drift.clean:
        print(
            "warning: sources changed since the last ingest — run `fux ingest` to refresh",
            file=sys.stderr,
        )


def _no_hits(args) -> int:
    if args.json:
        print(json.dumps({"query": args.query, "results": []}, ensure_ascii=False))
    else:
        print(
            "no matches for that question — try broader terms with `fux find`, "
            "or re-run `fux ingest` after adding sources"
        )
    return 0


def _location(file: str, start: int | None, end: int | None) -> str:
    if start is None:
        return file
    return f"{file}:{start}" if start == end else f"{file}:{start}-{end}"


def _run_ask(searcher: Searcher, config: Config, args) -> int:
    results = searcher.search(args.query, top=args.top)
    if not results:
        return _no_hits(args)
    if args.json:
        payload = {
            "query": args.query,
            "results": [_chunk_json(r, args.explain) for r in results],
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    for i, r in enumerate(results, start=1):
        heading = f"  ·  {r.heading}" if r.heading else ""
        print(f"{i}. {_location(r.file, r.start, r.end)}  ·  {r.score:.3f}{heading}")
        lines = r.text.split("\n")
        shown = lines if args.context == 0 else lines[: args.context]
        for line in shown:
            print(f"   {line}")
        if len(shown) < len(lines):
            print(f"   … ({len(lines) - len(shown)} more lines; use -C 0 for all)")
        if args.explain:
            for line in chunk_explain_lines(r):
                print(f"   ↳ {line}")
        print()
    return 0


def _chunk_json(r: ScoredChunk, explain: bool) -> dict:
    out = {
        "file": r.file,
        "lines": [r.start, r.end] if r.start is not None else None,
        "heading": r.heading,
        "score": round(r.score, 3),
        "text": r.text,
    }
    if explain:
        out["explain"] = chunk_explain_json(r)
    return out


def _run_find(searcher: Searcher, config: Config, args) -> int:
    results = searcher.search(args.query, top=_FIND_POOL)
    if not results:
        return _no_hits(args)
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
                    "file": file,
                    "score": round(agg["score"], 3),
                    "matching_passages": agg["chunks"],
                    **({"explain": chunk_explain_json(agg["best"])} if args.explain else {}),
                }
                for file, agg in ranked
            ],
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    for i, (file, agg) in enumerate(ranked, start=1):
        plural = "passage" if agg["chunks"] == 1 else "passages"
        print(f"{i}. {file}  ·  {agg['score']:.3f}  ·  {agg['chunks']} matching {plural}")
        if args.explain:
            for line in chunk_explain_lines(agg["best"]):
                print(f"   ↳ {line}")
    return 0


def _run_answer(searcher: Searcher, config: Config, args) -> int:
    results = searcher.search(args.query, top=_ANSWER_POOL)
    max_sentences = args.answer_max or config.answer.max_sentences
    sentences = build_answer(results, args.query, max_sentences)
    if not sentences:
        if args.json:
            print(
                json.dumps(
                    {"query": args.query, "answer": None, "sentences": [], "sources": []},
                    ensure_ascii=False,
                )
            )
        else:
            print(
                "no confident answer — the corpus may not cover this; "
                "try `fux find` to locate related files, or re-run `fux ingest`"
            )
        return 0
    sources = _sources(sentences, results)
    if args.json:
        payload = {
            "query": args.query,
            "answer": " ".join(s.text for s in sentences),
            "sentences": [_sentence_json(s, args.explain) for s in sentences],
            "sources": sources,
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    for s in sentences:
        cite = _location(s.file, s.line, s.line)
        print(f"{s.text}  [{cite}]")
        if args.explain:
            print(f"   ↳ {sentence_explain_line(s)}")
    print("\nsources:")
    for src in sources:
        print(f"- {src}")
    return 0


def _sentence_json(s: Sentence, explain: bool) -> dict:
    out = {"text": s.text, "file": s.file, "line": s.line, "score": round(s.score, 3)}
    if explain:
        out["factors"] = s.factors
    return out


def _sources(sentences: list[Sentence], results: list[ScoredChunk]) -> list[str]:
    spans = {r.file: (r.start, r.end) for r in results}
    out = []
    for file in dict.fromkeys(s.file for s in sentences):
        start, end = spans.get(file, (None, None))
        out.append(_location(file, start, end))
    return out
