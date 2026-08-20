"""The refer plane — rank in the index, fetch from the source, cite a fresh sha.

This is the half of "index-and-refer" that the index is *for*. The committed
plane holds statistics and never content (L2), so an answer that quotes a
document has to go and get it — from the git checkout, or from the system that
owns it through the consumer's fetcher.

## The shape of one call

```
   ranked doc ids            fetch (git / consumer fetcher)
   from `ask`      ------->  bytes  ------->  chunk  ------->  rescore
                               |                                  |
                               v                                  v
                          verify sha                         assemble under
                        (current/stale)                       a byte budget
```

Six modules, one each:

| module | question it answers |
|---|---|
| `source` | where do this document's bytes come from? |
| `freshness` | may I fetch at all, and was the index still right? |
| `arc` | have I already got these bytes? |
| `chunk` | which spans of this document are citable? |
| `rescore` | which of those spans answer *this* query? |
| `assemble` | which of those fit the caller's window? |

## Three properties the plane promises

**1. It cannot invent.** Every citation is a verbatim span of bytes that came
from the source, with the sha those bytes hashed to. No model is on this path
and none ever will be.

**2. Offline degradation is honest.** A `file:` source keeps full function with
no network at all. An external source that cannot be reached returns a
**declared** staleness — `unverified` — and never stale bytes presented as
fresh. The three-state verdict (`current` / `stale` / `unverified`) exists so
nothing downstream can collapse "we did not look" into "we looked and it was
fine".

**3. The policy travels with the answer.** A bundle records the freshness
policy it was produced under, per citation, because a replay that silently used
a different policy is indistinguishable from a replay that reproduced.

## What is not here yet

**R4 is unmeasured** — the cold/warm latency prediction runs in `fux-lab`, and
`fux-lab` does not exist (W-56). So this plane is built and unproven, and
ADR-REFER says so rather than claiming a gate it did not pass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import arc as arc_mod
from . import freshness as freshness_mod
from .assemble import DEFAULT_BUDGET, Assembled, assemble
from .chunk import chunk
from .freshness import Policy, Verdict, verify
from .rescore import ScoredPassage, rescore
from .source import FetchError, Fetched, fetch_document

__all__ = [
    "Bundle",
    "Cited",
    "Policy",
    "refer",
    "DEFAULT_BUDGET",
]


@dataclass(frozen=True)
class Cited:
    """One document the plane looked at, and what it found out about it."""

    doc_id: str
    loc: str
    verdict: Verdict
    strategy: str
    note: str = ""

    def as_record(self) -> dict:
        return {
            "id": self.doc_id,
            "loc": self.loc,
            "freshness": self.verdict.label,
            "indexed_sha": self.verdict.indexed_sha,
            "fetched_sha": self.verdict.fetched_sha,
            "strategy": self.strategy,
            "note": self.note or self.verdict.note,
        }


@dataclass
class Bundle:
    """An assembled answer, plus everything needed to reproduce or audit it."""

    assembled: Assembled
    documents: list[Cited] = field(default_factory=list)
    policy: dict = field(default_factory=dict)

    def as_record(self) -> dict:
        return {
            "citations": [
                {
                    "id": c.doc_id,
                    "locator": c.locator,
                    "sha": c.sha,
                    "heading": c.heading,
                    "text": c.text,
                    "score": c.score,
                    "source": c.source,
                }
                for c in self.assembled.citations
            ],
            "documents": [d.as_record() for d in self.documents],
            "budget": {
                "bytes": self.assembled.budget,
                "used": self.assembled.used,
                "dropped": self.assembled.dropped,
            },
            "policy": self.policy,
        }


def refer(
    root: Path,
    query: str,
    candidates: list[tuple[str, str, str]],
    *,
    policy: Policy | None = None,
    budget: int = DEFAULT_BUDGET,
    k: int | None = None,
    cache: arc_mod.ARC | None = None,
    fetcher=None,
) -> Bundle:
    """Fetch, verify, re-score and assemble. `candidates` is `(id, loc, sha)`.

    The candidates come from the ranker — this plane does not decide *which*
    documents answer the query, only which of their passages do and which of
    those fit.
    """
    policy = policy or Policy()
    decision = freshness_mod.decide(policy)

    documents: list[Cited] = []
    fetched: list[tuple[str, str, str, list]] = []

    for doc_id, loc, indexed_sha in candidates:
        result, cited = _obtain(root, doc_id, loc, indexed_sha, decision, cache, fetcher)
        documents.append(cited)
        if result is None:
            continue
        text = result.content.decode("utf-8", errors="replace")
        fetched.append((doc_id, loc, result.sha, chunk(text)))

    scored: list[ScoredPassage] = rescore(query, fetched)
    assembled = assemble(scored, budget=budget, k=k, source="fetched")
    return Bundle(assembled=assembled, documents=documents, policy=policy.as_record())


def _obtain(root, doc_id, loc, indexed_sha, decision, cache, fetcher):
    """Get one document's bytes, and record honestly what happened.

    **The `never` branch still reads a `file:` document.** Reading the local
    checkout is not a fetch — no network, no cost, no policy question — and
    refusing it would make `--audit` unable to quote the very repository it is
    auditing. What `never` forbids is going *out*.
    """
    from .source import GIT, resolve

    strategy = resolve(doc_id)
    if strategy != GIT and not decision.fetch:
        return None, Cited(doc_id, loc, verify(indexed_sha, None, decision.reason), strategy)

    key = (loc, indexed_sha)
    if cache is not None:
        hit = cache.get(key)
        if hit is not None:
            # A hit is keyed by content address, so it IS the indexed bytes —
            # which is why the verdict below is the *same* verdict a fetch
            # would have produced, note included.
            #
            # **The note must not say "cache hit".** A first draft did, and the
            # differential test caught it: a caller diffing two runs would see
            # a difference caused purely by cache state, which is precisely
            # what the differential law forbids. How the bytes were obtained is
            # instrumentation and lives on the cache object (`ARC.hits`); the
            # bundle records what was learned about the *document*.
            return (
                Fetched(doc_id, loc, hit, indexed_sha, strategy),
                Cited(doc_id, loc, verify(indexed_sha, indexed_sha), strategy),
            )

    try:
        result = fetch_document(root, doc_id, loc, fetcher=fetcher)
    except FetchError as exc:
        # Honest degradation: declared unverified, never stale-as-fresh.
        return None, Cited(doc_id, loc, verify(indexed_sha, None, str(exc)), strategy, str(exc))

    if cache is not None:
        cache.put((loc, result.sha), result.content)
    return result, Cited(doc_id, loc, verify(indexed_sha, result.sha), strategy)
