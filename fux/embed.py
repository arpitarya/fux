"""Phase-2 recall re-rank — local & $0-by-default (recall-engine.compare.md).

Gated behind ``recall_rerank`` in config. Prefers a local sentence-transformers
model if installed (the [embeddings] extra); otherwise falls back to a
dependency-free char-trigram cosine — still local, still $0, no API. Never a
mandatory dependency, never an LLM call.
"""
from __future__ import annotations

import math
from collections import Counter

from fux.model import Rule

_LEX_W, _SEM_W = 0.6, 0.4


def rerank(query: str, candidates: list[tuple[Rule, float]], cfg: dict
           ) -> list[tuple[Rule, float]]:
    """Re-order (rule, lexical_score) pairs by lexical+semantic blend if enabled."""
    if not cfg.get("recall_rerank") or len(candidates) < 2:
        return candidates
    sims = _semantic(query, [r for r, _ in candidates])
    top_lex = max((s for _, s in candidates), default=1.0) or 1.0
    blended = [(r, _LEX_W * (s / top_lex) + _SEM_W * sim)
               for (r, s), sim in zip(candidates, sims)]
    blended.sort(key=lambda x: x[1], reverse=True)
    return blended


def _text(r: Rule) -> str:
    extra = " ".join(str(x) for x in (r.fm.get("aliases") or []) + (r.fm.get("keywords") or []))
    return f"{r.id} {r.title} {r.body} {extra}".lower()


def _semantic(query: str, rules: list[Rule]) -> list[float]:
    model = _load_model()
    if model is not None:
        import numpy as np  # ships with sentence-transformers
        vecs = model.encode([query] + [_text(r) for r in rules], normalize_embeddings=True)
        q = vecs[0]
        return [float(np.dot(q, v)) for v in vecs[1:]]
    qg = _ngrams(query.lower())
    return [_cosine(qg, _ngrams(_text(r))) for r in rules]


def _load_model():
    try:
        from sentence_transformers import SentenceTransformer
    except ModuleNotFoundError:
        return None
    if not hasattr(_load_model, "_m"):
        _load_model._m = SentenceTransformer("all-MiniLM-L6-v2")  # local, downloaded once
    return _load_model._m


def _ngrams(text: str, n: int = 3) -> Counter:
    text = " " + " ".join(text.split()) + " "
    return Counter(text[i:i + n] for i in range(max(len(text) - n + 1, 0)))


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a[k] * b.get(k, 0) for k in a)
    return dot / (math.sqrt(sum(v * v for v in a.values())) *
                  math.sqrt(sum(v * v for v in b.values())) or 1.0)
