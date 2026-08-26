"""Which of a document's headings answer the query — a display-only selection.

## What this is, and what it deliberately is not

`ask` cites a **document**. `answer` cites a **span** — `docs/mesh.md:L10-L13`
— and it can only do that because it fetched the bytes and chunked them
([ADR-ANSWER](../../../docs/adr/0006_answer.md)). `ask` is offline by default
(L4), holds statistics rather than text (L2), and therefore has nothing to
count lines in.

**Headings are the span-level signal `ask` can honestly give.** A record's
`phrases` are its headings, taken from the document at ingest by
`ingest/extract.py` and already committed — so naming the ones that match the
query costs **no new plane, no positions, no fetch and no byte of index**.

**Why not line numbers on `ask`.** A line range computed at ingest describes
the document as it was then; edit the file and it points somewhere wrong while
looking exactly as right. A heading survives a reflow, an inserted paragraph
and a re-wrap. The staleness exposure here is *identical to `title`*, which
every `ask` result has always carried.

## The selection rule

1. Analyze the query once; analyze each phrase (`tokenize`, the same analyzer
   both sides of every match share, so `Rollbacks` matches `rollback`).
2. Score a phrase by the count of **distinct** query terms it contains — a
   heading covering two of the asked-about terms beats one repeating a single
   term five times.
3. Drop phrases scoring zero. **No match means no headings**, never "the first
   three": inventing relevance is the failure the extracted-mode law exists to
   prevent.
4. Sort by `(-matches, position in the document)`. Ties break on document
   order, so the output is a deterministic function of the record (L3) with no
   set-iteration dependence.
5. Cap at `MAX_HEADINGS`.

## Two things this must never become

- **It must never touch the sort.** This runs on the *already-unified* result
  list after `run_query` returns, exactly like `_resolve_title` (P5), so
  whichever candidate generator answered, both resolve identically and there is
  no seam for the differential law to break through. Nothing here computes or
  adjusts a BM25F score, and nothing here may.
- **It must never read the working tree.** That is `query/rerank.py`'s job and
  the reason ADR-RERANK is carved out of ADR-ASK's directory claim. This reads
  one committed record and nothing else.

A `hashed` record carries no `phrases` at all — `store/writer.py` refuses to
write display text for one (L5) — so it yields nothing here by construction
rather than by a special case.
"""

from __future__ import annotations

from .tokenize import tokenize

#: How many matched headings a single result may show. Three, because the
#: point is to aim a reader at a section, not to reproduce the outline —
#: `ingest/extract.py` commits up to twelve.
MAX_HEADINGS = 3

__all__ = ["MAX_HEADINGS", "headings_for"]


def headings_for(record: dict | None, query: str, *, limit: int = MAX_HEADINGS) -> list[str]:
    """The record's headings that match `query`, best first, at most `limit`.

    Empty for a missing record, a record with no `phrases` (a `hashed` one, or
    a document with no headings), or a query no heading matches.
    """
    if not record:
        return []
    phrases = record.get("phrases") or []
    if not phrases:
        return []

    wanted = set(tokenize(query))
    if not wanted:
        return []

    scored: list[tuple[int, int, str]] = []
    for position, phrase in enumerate(phrases):
        if not isinstance(phrase, str):  # a record is data, not a promise
            continue
        matches = len(wanted & set(tokenize(phrase)))
        if matches:
            # `position` ascending is the tie-break, so the key sorts directly.
            scored.append((-matches, position, phrase))

    scored.sort()
    return [phrase for _, _, phrase in scored[:limit]]
