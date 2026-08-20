"""The byte budget — assembling the most answer that fits.

Graduating `work/proposals/token-budget-retrieval.md`.

## `k` is the wrong limit for an agent

The binding constraint on a caller is the **context window**, not the result
count. Ten results is a human-browsing artifact: an agent wants the most answer
that fits in the space it has, which may be one long passage from one document
or twelve short ones from nine.

So the budget is primary and `k` is demoted to a secondary cap — it survives
because humans genuinely do want a list.

## Bytes, never tokens

Carrying a tokenizer per model family violates L1, and an *approximate* token
count is worse than an honest byte count: it is wrong in a way the caller
cannot see. Bytes are exact, and the caller knows their own ratio.

## The budget bounds the whole rendered answer

Not just the citation texts — the headers, the locators, and the ranking
explanation too. That is the honest reading of "fits in my context"; bounding
only the payload and then emitting three kilobytes of scaffolding around it
means the number the caller passed was a suggestion.

## Three properties that are not optional

1. **Deterministic ties.** Equal score-per-byte resolves by
   `(-score, sha, locator)`, never by set iteration order. Same corpus, same
   budget, same bytes.
2. **A floor for the best answer.** Greedy score-per-byte is *systematically*
   biased toward short passages: a 50-byte passage scoring 3 (0.060/byte) beats
   a 2000-byte passage scoring 8 (0.004/byte) every time, so the one long
   passage that actually answers the question is crowded out by efficient
   fragments. The floor is that **the single highest-scoring passage is seated
   first**, by absolute score, whenever it fits the budget at all. Everything
   after it is greedy. Without this the assembler reliably returns the cheapest
   answer rather than the best one, and
   `tests/refer/test_assemble.py::test_the_best_answer_is_not_crowded_out_by_cheaper_fragments`
   fails.
3. **A per-document cap — that never silences a document entirely.** One
   document must not consume the whole budget, so it is capped at
   `PER_DOC_FRACTION`. But a cap that blocks a document's *first* citation
   turns "do not dominate" into "do not appear", and at small budgets that
   excludes the best answer for a reason the caller never asked for. So **a
   document's first citation is exempt from the per-document cap** and bounded
   only by the total budget.
"""

from __future__ import annotations

from dataclasses import dataclass

from .rescore import ScoredPassage

__all__ = ["Assembled", "Citation", "assemble", "DEFAULT_BUDGET", "PER_DOC_FRACTION"]

#: Bytes. A default a human can read and an agent can afford.
DEFAULT_BUDGET = 8000

#: No single document may take more than this share of the budget.
PER_DOC_FRACTION = 0.5

#: Per-citation overhead charged against the budget — the locator line and the
#: separator that will be rendered around each passage. Charged rather than
#: ignored, because the budget bounds the *rendered* answer.
CITATION_OVERHEAD = 80


@dataclass(frozen=True)
class Citation:
    """One selected passage, with everything a reader needs to verify it."""

    doc_id: str
    locator: str
    sha: str
    heading: str
    text: str
    score: float
    source: str  # "index" | "fetched"

    @property
    def nbytes(self) -> int:
        return len(self.text.encode("utf-8")) + CITATION_OVERHEAD


@dataclass(frozen=True)
class Assembled:
    """The assembled answer, and an honest account of what did not fit."""

    citations: list[Citation]
    budget: int
    used: int
    dropped: int

    @property
    def remaining(self) -> int:
        return self.budget - self.used


def assemble(
    scored: list[ScoredPassage],
    *,
    budget: int = DEFAULT_BUDGET,
    k: int | None = None,
    source: str = "fetched",
    overhead: int = 0,
) -> Assembled:
    """Fill `budget` bytes with the highest-value passages that fit.

    `overhead` is what the renderer will spend on the answer as a whole —
    headers, the policy stamp — charged before any citation is selected, so the
    budget bounds the whole thing rather than just the payload.

    Greedy by **score per byte**, which is the right objective: the question is
    not "what scores highest" but "what is the most answer per byte of the
    caller's window".
    """
    if budget <= 0:
        raise ValueError("budget must be positive")

    candidates = [s for s in scored if s.score > 0]
    if not candidates:
        return Assembled(citations=[], budget=budget, used=overhead, dropped=0)

    # The floor: the best answer by ABSOLUTE score is seated first, so greedy
    # score-per-byte cannot crowd it out with cheaper fragments. Ties on
    # (sha, locator), as everywhere.
    best = min(candidates, key=lambda s: (-s.score, s.sha, s.locator))

    # Everything else, greedy by score per byte — the right objective once the
    # best answer is safe: most answer per byte of the caller's window.
    rest = [s for s in candidates if s is not best]
    rest.sort(key=lambda s: (-(s.score / max(s.nbytes, 1)), s.sha, s.locator))

    per_doc_cap = int(budget * PER_DOC_FRACTION)
    used = overhead
    per_doc: dict[str, int] = {}
    chosen: list[Citation] = []
    dropped = 0

    for s in [best, *rest]:
        if k is not None and len(chosen) >= k:
            dropped += 1
            continue
        citation = Citation(
            doc_id=s.doc_id,
            locator=s.locator,
            sha=s.sha,
            heading=s.passage.heading,
            text=s.passage.text,
            score=s.score,
            source=source,
        )
        spent = per_doc.get(s.doc_id, 0)
        # A document's FIRST citation is exempt from the per-document cap: the
        # cap exists to stop a document dominating, not to stop it appearing.
        capped = s.doc_id in per_doc and spent + citation.nbytes > per_doc_cap
        if used + citation.nbytes > budget or capped:
            dropped += 1
            continue  # skip, don't stop: a smaller passage may still fit
        chosen.append(citation)
        used += citation.nbytes
        per_doc[s.doc_id] = spent + citation.nbytes

    # Present in score order — the caller reads the best answer first, even
    # though selection ran on score-per-byte.
    chosen.sort(key=lambda c: (-c.score, c.sha, c.locator))
    return Assembled(citations=chosen, budget=budget, used=used, dropped=dropped)
