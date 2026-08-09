"""Dump best_confidence per eval question, mirroring _run_answer exactly.
Run with the acme corpus venv, cwd = the corpus dir. Writes JSON to stdout."""
import json
import os
import sys

from fux.config import load, find_root
from fux.index import load_searcher, backend_for
from fux.kernel import retrieve
from fux.query.answer import build_answer

GIBBERISH = "xyzzy plugh frobnicate quux zork blorptang wibblesnarf"


def best_conf_for(config, searcher, files, q, max_sentences):
    graph = retrieve(config, q, k=10, lexical_only=False, searcher=searcher, files=files)
    model = graph.model
    passages = graph.passages
    qsim = None
    if model is not None:
        query_vec = model.embed(q)

        def qsim(text):
            vec = model.embed(text)
            if vec is None or query_vec is None:
                return None
            return model.similarity(query_vec, vec)

    sentences = build_answer(passages, q, max_sentences, qsim=qsim)
    if not sentences:
        return None, 0, graph.engine  # already declines via empty pool
    best = max(s.score for s in sentences)
    return best, len(sentences), graph.engine


def main():
    root = find_root()
    config = load(root)
    searcher = load_searcher(config)
    files = backend_for(config).load(config.root)
    max_sentences = config.answer.max_sentences

    manifest = json.load(open("_manifest.json"))
    rows = []
    for p in manifest["eval_pairs"]:
        best, n, engine = best_conf_for(config, searcher, files, p["q"], max_sentences)
        rows.append({"q": p["q"], "kind": p["kind"], "doc": p.get("doc", ""),
                     "best_confidence": best, "n_sentences": n})
    # gibberish control
    best, n, engine = best_conf_for(config, searcher, files, GIBBERISH, max_sentences)
    rows.append({"q": GIBBERISH, "kind": "gibberish", "doc": "",
                 "best_confidence": best, "n_sentences": n})
    print(json.dumps({"engine": engine, "max_sentences": max_sentences, "rows": rows}, ensure_ascii=False))


if __name__ == "__main__":
    main()
