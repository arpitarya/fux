"""Extractive answer synthesis — select and order source sentences, never
generate (compare/query-output.compare.md). Sentence score = normalized BM25F
passage score × question-term overlap × TextRank centrality; the winners are
re-ordered into document order and each carries its `file:line` citation."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from ..index.bm25f import ScoredChunk, tokenize

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_BULLET_RE = re.compile(r"^([-*+]|\d+\.)\s+")
_MIN_WORDS = 4
_CANDIDATE_CHUNKS = 10
# Sentences scoring under this fraction of the best sentence are noise, not answer.
_RELATIVE_KEEP = 0.35
# Question-side stopwords: overlap must measure content terms, or "how are ..."
# matches every sentence containing "are". Used only here, never in BM25F.
_STOPWORDS = frozenset(
    "a an and are as at be but by can did do does for from had has have how i if in "
    "is it its me my of on or our so that the their then there these they this to "
    "was we were what when where which who why will with would you your".split()
)


@dataclass
class Sentence:
    text: str
    file: str
    line: int | None
    score: float
    factors: dict = field(default_factory=dict)


def build_answer(
    results: list[ScoredChunk], query: str, max_sentences: int, qsim=None
) -> list[Sentence]:
    candidates: list[Sentence] = []
    max_passage = max((r.score for r in results), default=0.0) or 1.0
    for r in results[:_CANDIDATE_CHUNKS]:
        for text, chunk_line in _sentences(r.text):
            line = r.start + chunk_line - 1 if r.start is not None else None
            candidates.append(
                Sentence(
                    text=text,
                    file=r.file,
                    line=line,
                    score=0.0,
                    factors={"passage": round(r.score / max_passage, 4)},
                )
            )
    if not candidates:
        return []

    q_terms = set(tokenize(query)) - _STOPWORDS or set(tokenize(query))
    token_sets = [set(tokenize(s.text)) for s in candidates]
    centrality = _textrank(token_sets)
    for s, toks, cent in zip(candidates, token_sets, centrality):
        overlap = len(q_terms & toks) / len(q_terms) if q_terms else 0.0
        s.factors["overlap"] = round(overlap, 4)
        s.factors["centrality"] = round(cent, 4)
        # overlap smoothed so TextRank can rescue paraphrases; centrality floored
        # so a uniquely relevant sentence isn't crushed for being unlike its peers.
        s.score = s.factors["passage"] * (overlap + 0.05) * (0.5 + 0.5 * cent)
        if qsim is not None:  # engine v2: question-similarity from the bundled model
            sim = qsim(s.text)
            if sim is not None:
                s.factors["qsim"] = round(sim, 4)
                s.score *= 0.5 + 0.5 * max(0.0, sim)

    ranked = sorted(
        candidates, key=lambda s: (-round(s.score, 9), s.file, s.line or 0, s.text)
    )
    keep_floor = _RELATIVE_KEEP * ranked[0].score
    chosen: list[Sentence] = []
    seen: set[str] = set()
    for s in ranked:
        if s.score < keep_floor:
            break
        key = " ".join(tokenize(s.text))
        if key in seen:
            continue
        seen.add(key)
        chosen.append(s)
        if len(chosen) >= max_sentences:
            break
    chosen.sort(key=lambda s: (s.file, s.line or 0))
    return chosen


def _sentences(text: str):
    """Prose sentences with their 1-based chunk line: fences, tables, headings out."""
    paras: list[list[tuple[int, str]]] = []
    cur: list[tuple[int, str]] = []
    in_fence = False
    for i, raw in enumerate(text.split("\n"), start=1):
        stripped = raw.strip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            stripped = ""
        if in_fence or not stripped or stripped.startswith(("#", "|")):
            if cur:
                paras.append(cur)
                cur = []
            continue
        cur.append((i, _BULLET_RE.sub("", stripped)))
    if cur:
        paras.append(cur)
    for para in paras:
        yield from _split_para(para)


def _split_para(para: list[tuple[int, str]]):
    joined = ""
    bounds: list[tuple[int, int]] = []  # (char offset, line)
    for line_no, text in para:
        if joined:
            joined += " "
        bounds.append((len(joined), line_no))
        joined += text
    pos = 0
    for part in _SENT_SPLIT.split(joined):
        stripped = part.strip()
        if len(stripped.split()) < _MIN_WORDS:
            continue
        start = joined.find(part, pos)
        pos = start + len(part)
        line = next(ln for off, ln in reversed(bounds) if off <= start)
        yield stripped, line


def _textrank(token_sets: list[set[str]], damping: float = 0.85, iters: int = 30):
    """Classic TextRank (Mihalcea & Tarau 2004) with overlap/log-length similarity;
    fixed iteration count keeps it deterministic. Returns scores normalized to 1."""
    n = len(token_sets)
    if n == 0:
        return []
    if n == 1:
        return [1.0]
    weights = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            a, b = token_sets[i], token_sets[j]
            if len(a) > 1 and len(b) > 1:
                overlap = len(a & b)
                if overlap:
                    w = overlap / (math.log(len(a)) + math.log(len(b)))
                    weights[i][j] = weights[j][i] = w
    out_sum = [sum(row) or 1.0 for row in weights]
    scores = [1.0 / n] * n
    for _ in range(iters):
        scores = [
            (1 - damping) / n
            + damping
            * sum(weights[j][i] / out_sum[j] * scores[j] for j in range(n) if weights[j][i])
            for i in range(n)
        ]
    top = max(scores) or 1.0
    return [s / top for s in scores]
