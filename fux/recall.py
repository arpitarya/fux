"""`fux recall` — BM25-lite lexical retrieval ($0, phase-1 of recall-engine.compare.md).

Frontmatter fields (id/domain/related/aliases/keywords) are weighted above body
text so a curated, tagged corpus ranks precisely. Phase-2 opt-in local embedding
re-rank (config ``recall_rerank``) layers on top without changing this default.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path

from fux import config, loader, paths
from fux.model import Rule

_TOK = re.compile(r"[a-z0-9]+")
# Field weights — repeats a field's tokens to boost their term frequency.
_WEIGHTS = {"id": 5, "domain": 3, "aliases": 4, "keywords": 4, "related": 2, "type": 2}


def _tokens(text: str) -> list[str]:
    return _TOK.findall(text.lower())


def _doc_tokens(r: Rule) -> list[str]:
    toks = _tokens(r.body) + _tokens(r.id.replace("-", " "))
    for field, weight in _WEIGHTS.items():
        val = r.fm.get(field)
        if isinstance(val, list):
            val = " ".join(str(x) for x in val)
        toks += _tokens(str(val or "")) * weight
    return toks


def run(root: Path, query: str, top: int = 6) -> list[tuple[Rule, float]]:
    cfg = config.load(paths.Footprint(root).config)
    rules = loader.resolve(root, cfg).active()
    return rank(rules, query, top)


def rank(rules: list[Rule], query: str, top: int = 6) -> list[tuple[Rule, float]]:
    docs = [(r, _doc_tokens(r)) for r in rules]
    n = len(docs) or 1
    avg_len = sum(len(t) for _, t in docs) / n
    df: Counter = Counter()
    for _, toks in docs:
        df.update(set(toks))
    q_terms = set(_tokens(query))
    scored: list[tuple[Rule, float]] = []
    for r, toks in docs:
        scored.append((r, _bm25(toks, q_terms, df, n, avg_len)))
    scored = [s for s in scored if s[1] > 0]
    scored.sort(key=lambda s: s[1], reverse=True)
    return scored[:top]


def _bm25(toks: list[str], q_terms: set[str], df: Counter, n: int, avg_len: float) -> float:
    tf = Counter(toks)
    k1, b, score = 1.5, 0.75, 0.0
    dl = len(toks) or 1
    for term in q_terms:
        if term not in tf:
            continue
        idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
        freq = tf[term]
        score += idf * (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * dl / avg_len))
    return round(score, 4)
