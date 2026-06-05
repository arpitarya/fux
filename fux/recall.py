"""`fux recall` — BM25F lexical retrieval ($0, phase-1 of recall-engine.compare.md).

True **BM25F**: each frontmatter field (id/domain/aliases/keywords/related/type) is
weighted *and* length-normalised independently before a single saturation, so a
curated, tagged corpus ranks precisely — strictly better than the old "lite" scorer
that flattened everything into one bag (plan §17.18a). An opt-in **deterministic
query expansion** (`recall_expand` / `--expand`) widens the query with glossary
synonyms and 1-hop graph neighbours before scoring (§17.18b). Phase-2 local
embedding re-rank and phase-3 RRF hybrid still layer on top unchanged.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path

from fux import config, loader, paths
from fux.model import Rule

_TOK = re.compile(r"[a-z0-9]+")
# Per-field weight and length-normalisation (BM25F). Body is the baseline field.
_FIELDS = {"body": 1.0, "id": 5.0, "domain": 3.0, "aliases": 4.0,
           "keywords": 4.0, "related": 2.0, "type": 2.0}
_K1, _B = 1.5, 0.75


def _tokens(text: str) -> list[str]:
    return _TOK.findall(text.lower())


def _field_tokens(r: Rule) -> dict[str, list[str]]:
    """Tokens per BM25F field — the id's words live in the high-weight `id` field."""
    fields = {"body": _tokens(r.body),
              "id": _tokens(r.id.replace("-", " ")) + _tokens(str(r.fm.get("id") or ""))}
    for f in ("domain", "aliases", "keywords", "related", "type"):
        val = r.fm.get(f)
        if isinstance(val, list):
            val = " ".join(str(x) for x in val)
        fields[f] = _tokens(str(val or ""))
    return fields


def run(root: Path, query: str, top: int = 6, hybrid: bool | None = None,
        expand: bool | None = None) -> list[tuple[Rule, float]]:
    cfg = config.load(paths.Footprint(root).config)
    rules = loader.resolve(root, cfg).active()
    use_expand = cfg.get("recall_expand", False) if expand is None else expand
    extra = expand_terms(rules, query) if use_expand else None
    use_hybrid = cfg.get("recall_hybrid", False) if hybrid is None else hybrid
    if use_hybrid:
        from fux import hybrid as hy  # lazy: pulls embed/graphquery only when asked
        results = hy.fuse(root, query, rules, top=top, cfg=cfg)
    elif cfg.get("recall_rerank"):
        from fux import embed  # lazy: keeps the default path dependency-free
        results = embed.rerank(query, rank(rules, query, top * 3, extra_terms=extra), cfg)[:top]
    else:
        results = rank(rules, query, top, extra_terms=extra)
    if cfg.get("usage_tracking"):
        from fux import usage          # served = a genuine "use" signal (§17.20c)
        usage.record(root, [r.id for r, _ in results])
    if cfg.get("cost_tracking"):
        from fux import costledger     # accumulate per-lookup savings into cost.json
        costledger.record(root, query, [r for r, _ in results])
    return results


def expand_terms(rules: list[Rule], query: str) -> set[str]:
    """Deterministic query expansion: glossary synonyms + 1-hop `related` neighbours.

    A query term that names a glossary entry pulls in that entry's defining words;
    a term that names any rule pulls in its `related` ids. `$0`, no model (§17.18b).
    """
    qt = set(_tokens(query))
    extra: set[str] = set()
    for r in rules:
        names = set(_tokens(r.id.replace("-", " ")))
        for a in (r.fm.get("aliases") or []):
            names |= set(_tokens(str(a)))
        if not (qt & names):
            continue
        if r.type == "glossary":
            extra |= set(_tokens(r.title))
            for k in (r.fm.get("keywords") or []):
                extra |= set(_tokens(str(k)))
        for rel in r.related:
            extra |= set(_tokens(rel.replace("-", " ")))
    return extra - qt


def rank(rules: list[Rule], query: str, top: int = 6,
         extra_terms: set[str] | None = None) -> list[tuple[Rule, float]]:
    docs = [(r, _field_tokens(r)) for r in rules]
    n = len(docs) or 1
    avg = {f: 0.0 for f in _FIELDS}
    df: Counter = Counter()
    for _, ft in docs:
        present: set[str] = set()
        for f in _FIELDS:
            toks = ft.get(f, [])
            avg[f] += len(toks)
            present |= set(toks)
        df.update(present)
    for f in _FIELDS:
        avg[f] = (avg[f] / n) or 1.0
    q_terms = set(_tokens(query)) | (extra_terms or set())
    scored = [(r, _bm25f(ft, q_terms, df, n, avg)) for r, ft in docs]
    scored = [s for s in scored if s[1] > 0]
    scored.sort(key=lambda s: (-s[1], s[0].id))     # id tie-break → deterministic
    return scored[:top]


def _bm25f(ft: dict[str, list[str]], q_terms: set[str], df: Counter,
           n: int, avg: dict[str, float]) -> float:
    counts = {f: Counter(toks) for f, toks in ft.items()}
    score = 0.0
    for term in q_terms:
        if term not in df:
            continue
        weighted_tf = 0.0
        for f, wf in _FIELDS.items():
            tf = counts[f].get(term, 0)
            if not tf:
                continue
            norm = 1 - _B + _B * len(ft[f]) / avg[f]    # per-field length normalisation
            weighted_tf += wf * tf / norm
        if weighted_tf <= 0:
            continue
        idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
        score += idf * weighted_tf / (_K1 + weighted_tf)   # single saturation (BM25F)
    return round(score, 4)
