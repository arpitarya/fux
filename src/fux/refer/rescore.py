"""Passage scoring on the fetched bytes.

**One scorer, not two.** This reuses `query/bm25f.py` — weight-then-saturate
once, never a per-field BM25 summed. Writing a second scorer for passages is
how the index and the refer plane end up disagreeing about what "relevant"
means, and the disagreement surfaces as an answer whose top citation is not the
top document.

The corpus statistics are the *passage set's*, not the index's, and that is
deliberate: the question here is "which part of these documents answers the
query", which is a different question from "which document answers it". The
index already answered the second one — that is what produced the candidates.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..query.bm25f import score_record
from ..query.scan import query_term_hashes
from ..query.tokenize import tokenize
from .chunk import Passage

__all__ = ["ScoredPassage", "rescore"]


@dataclass(frozen=True)
class ScoredPassage:
    """A passage with its score and the document it came from."""

    doc_id: str
    loc: str
    sha: str
    passage: Passage
    score: float

    @property
    def nbytes(self) -> int:
        return self.passage.nbytes

    @property
    def locator(self) -> str:
        """A stable, citable address: the loc plus the passage's ordinal."""
        return f"{self.loc}#p{self.passage.ordinal}"


def rescore(query: str, candidates: list[tuple[str, str, str, list[Passage]]]) -> list[ScoredPassage]:
    """Score every passage of every fetched document against the query.

    `candidates` is `(doc_id, loc, sha, passages)` per fetched document.
    Returns every passage scored, sorted by `(-score, locator)` — ties break on
    the locator, never on iteration order, because the assembler downstream
    must be able to promise byte-identical output.
    """
    hashes = query_term_hashes(query)
    if not hashes:
        return []

    rows: list[tuple[str, str, str, Passage, dict[str, list[int]], int]] = []
    df: dict[str, int] = {}
    total_wlen = 0

    for doc_id, loc, sha, passages in candidates:
        for passage in passages:
            terms, wlen = _terms_of(passage)
            rows.append((doc_id, loc, sha, passage, terms, wlen))
            total_wlen += wlen
            for term in terms:
                df[term] = df.get(term, 0) + 1

    if not rows:
        return []
    n = len(rows)
    avg_wlen = total_wlen / n if n else 0.0

    scored = [
        ScoredPassage(
            doc_id=doc_id,
            loc=loc,
            sha=sha,
            passage=passage,
            score=score_record(terms, wlen, hashes, df, n, avg_wlen),
        )
        for doc_id, loc, sha, passage, terms, wlen in rows
    ]
    scored.sort(key=lambda s: (-s.score, s.locator))
    return scored


def _terms_of(passage: Passage) -> tuple[dict[str, list[int]], int]:
    """`{hash: [tf_heading, tf_body]}` and the passage's length, its own fields.

    A passage's *heading* is its heading line and its *body* is its text, which
    is the same two-field shape the index uses — so the weights carry over
    unchanged rather than being re-picked here.
    """
    from .. import store as store_mod

    terms: dict[str, list[int]] = {}
    for word in tokenize(passage.heading):
        terms.setdefault(store_mod.term_hash(word), [0, 0])[0] += 1
    body = tokenize(passage.text)
    for word in body:
        terms.setdefault(store_mod.term_hash(word), [0, 0])[1] += 1
    return terms, len(body)
