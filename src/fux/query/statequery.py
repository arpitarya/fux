"""Renderers for state-only mode — the fresh-clone query path.

Output formats follow docs/cli-examples.md. Every rendering says *doc-level*
somewhere, because that is the honest description: without the runtime plane
there are no chunk scores, and pretending otherwise would make a weaker result
look like a stronger one.

`answer` deliberately has no state-only mode. It is extractive and cited, and
citations need line-anchored passages; producing them from re-derived text
would risk citing lines the index never saw. It says so and exits 0.
"""

from __future__ import annotations

import json

from ..config import Config
from ..errors import FuxError
from .lean import LeanCorpus

_STATE_HINT = "run `fux ingest` for ranked passages"


def run_state_query(config: Config, args, started: float) -> int:
    corpus = LeanCorpus(config)
    if not corpus:
        raise FuxError("no index found — run `fux ingest` first")
    if args.mode == "answer":
        return _answer_unavailable(args, corpus)
    ranked = corpus.search(args.query, top=max(args.top, 1))
    if args.mode == "find":
        return _render_find(args, corpus, ranked)
    return _render_ask(config, args, corpus, ranked)


def _corpus_meta(corpus: LeanCorpus) -> dict:
    return {"docs": len(corpus.docs), "chunks": None}


def _render_find(args, corpus: LeanCorpus, ranked) -> int:
    if args.json:
        print(
            json.dumps(
                {
                    "query": args.query,
                    "results": [
                        {
                            "path": doc_id,
                            "title": why["title"],
                            "level": "doc",
                            **({"explain": why} if args.explain else {}),
                        }
                        for doc_id, why in ranked
                    ],
                    "corpus": _corpus_meta(corpus),
                    "engine": "state",
                },
                ensure_ascii=False,
            )
        )
        return 0
    if not ranked:
        print("No confident matches in the committed state.")
        print(f"Try: broaden the question · {_STATE_HINT}")
        return 0
    for i, (doc_id, why) in enumerate(ranked, start=1):
        title = f"   {why['title']}" if why["title"] else ""
        print(f"{i}.  {doc_id}{title}")
        if args.explain:
            print(
                f"    signature rank {why['signature_rank']} · "
                f"dense rank {why['dense_rank']} → rrf {why['rrf']}"
            )
    plural = "doc" if len(ranked) == 1 else "docs"
    print(f"{len(ranked)} {plural} · doc-level (committed state; {_STATE_HINT})")
    return 0


def _render_ask(config: Config, args, corpus: LeanCorpus, ranked) -> int:
    from .cat import document_text

    shown = []
    for doc_id, why in ranked[: args.top]:
        try:
            text = document_text(config, doc_id)
        except FuxError:
            continue  # source not present in this clone: skip, don't invent
        shown.append((doc_id, why, text))

    if args.json:
        print(
            json.dumps(
                {
                    "query": args.query,
                    "results": [
                        {
                            "path": doc_id,
                            "title": why["title"],
                            "level": "doc",
                            "text": _preview(text, args),
                            **({"explain": why} if args.explain else {}),
                        }
                        for doc_id, why, text in shown
                    ],
                    "corpus": _corpus_meta(corpus),
                    "engine": "state",
                },
                ensure_ascii=False,
            )
        )
        return 0
    if not shown:
        print("No confident matches in the committed state.")
        print(f"Try: broaden the question · {_STATE_HINT}")
        return 0
    print()
    for doc_id, why, text in shown:
        print(f"{doc_id}  (doc-level)")
        for line in _preview(text, args).split("\n"):
            print(f"  {line}")
        if args.explain:
            print(
                f"  signature rank {why['signature_rank']} · "
                f"dense rank {why['dense_rank']} → rrf {why['rrf']}"
            )
        print()
    plural = "doc" if len(shown) == 1 else "docs"
    print(f"{len(shown)} {plural} · re-derived from source · {_STATE_HINT}")
    return 0


def _preview(text: str, args) -> str:
    lines = [line for line in text.split("\n") if line.strip()]
    limit = getattr(args, "context", 4) or 4
    return "\n".join(lines[:limit])


def _answer_unavailable(args, corpus: LeanCorpus) -> int:
    message = (
        "answers are extractive and cited, which needs line-anchored passages — "
        "run `fux ingest` first (doc-level search works now: try `fux find`)"
    )
    if args.json:
        print(
            json.dumps(
                {
                    "query": args.query, "answer": None, "sentences": [], "sources": [],
                    "corpus": _corpus_meta(corpus), "engine": "state", "note": message,
                },
                ensure_ascii=False,
            )
        )
        return 0
    print(f"No answer available yet — {message}")
    return 0
