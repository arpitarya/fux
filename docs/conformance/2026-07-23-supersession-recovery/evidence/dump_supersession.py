"""Before/after answer-level supersession measurement. Mirrors _run_answer:
retrieve pool=10, then compare build_answer on raw results (BEFORE, no
preference) vs prefer_current(results) (AFTER). No src file modified."""
import json

from fux.config import load, find_root
from fux.index import load_searcher, backend_for
from fux.kernel import retrieve
from fux.query.answer import build_answer, prefer_current


def answer_sources(config, model_holder, passages, q, max_sentences):
    model = model_holder["model"]
    qsim = None
    if model is not None:
        qv = model.embed(q)

        def qsim(text):
            v = model.embed(text)
            if v is None or qv is None:
                return None
            return model.similarity(qv, v)

    sents = build_answer(passages, q, max_sentences, qsim=qsim)
    # source docs in citation order (unique, preserving first-seen)
    seen = []
    for s in sents:
        if s.file not in seen:
            seen.append(s.file)
    return seen


def main():
    root = find_root()
    config = load(root)
    searcher = load_searcher(config)
    files = backend_for(config).load(config.root)
    ms = config.answer.max_sentences

    manifest = json.load(open("_manifest.json"))
    pairs = [p for p in manifest["eval_pairs"] if p["kind"] == "stale-vs-current"]
    out = []
    for p in pairs:
        q = p["q"]
        stale = p["stale_doc"]
        current = p["doc"]
        graph = retrieve(config, q, k=10, lexical_only=False, searcher=searcher, files=files)
        mh = {"model": graph.model}
        pool = [r.file for r in graph.passages]
        pool_set = set(pool)
        smeta = files.get(stale, {})
        superseded = bool(smeta.get("superseded"))
        target = smeta.get("superseded_by_resolved") or smeta.get("superseded_by")
        before = answer_sources(config, mh, graph.passages, q, ms)
        after_passages = prefer_current(graph.passages, files)
        after = answer_sources(config, mh, after_passages, q, ms)
        out.append({
            "q": q,
            "current_doc": current,
            "stale_doc": stale,
            "stale_superseded_flag": superseded,
            "superseded_by_target": target,
            "stale_in_pool": stale in pool_set,
            "current_in_pool": current in pool_set,
            "target_in_pool": (target in pool_set) if target else None,
            "pool_order": pool,
            "answer_before_sources": before,
            "answer_after_sources": after,
            "before_top": before[0] if before else None,
            "after_top": after[0] if after else None,
        })
    print(json.dumps({"engine": graph.engine, "pairs": out}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
