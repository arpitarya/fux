"""The single scorer and the single sort — shared by both candidate generators.

**This module is why the differential law is achievable.** Floating-point
addition is not associative, so a term-major accelerator that accumulated each
document's score term-by-term would produce different low-order bits than the
doc-major scan, and `--json` output would differ even though nothing was
logically wrong. The fix is structural rather than careful: the accelerator
generates *candidates and statistics*, never scores. Both paths call `rank()`,
which sums each document's contributions in query-hash order exactly once.

The differential law then reduces to a claim that can actually be tested:
**the candidate set and the corpus statistics are identical.** Everything
downstream is one code path.

See `work/adr/0005_derived-accelerator.md`.
"""

from __future__ import annotations

from dataclasses import dataclass

from .. import store as store_mod
from ..ingest.gitdir import is_archived_loc
from .bm25f import score_record


@dataclass(frozen=True)
class AskResult:
    id: str
    title: str
    loc: str
    score: float
    #: The document is retired (ADR-ARCHIVED-CONTENT decisions 1 and 3).
    #: **Never part of the sort key** — decision 2 fixes the order as
    #: byte-identical at the default weight, and this field is what a reader is
    #: told, not what the scorer computes.
    archived: bool = False


@dataclass(frozen=True)
class Corpus:
    """The statistics BM25F needs, derived per query and never stored.

    `n` counts every record line; `total_wlen` sums the `wlen` of the records
    that have one. A record without `wlen` therefore contributes to the
    denominator and not the numerator — that is `scan.py`'s behaviour, and the
    accelerator's build asserts it reproduces the same two integers.
    """

    n: int
    total_wlen: int

    @property
    def avg_wlen(self) -> float:
        return self.total_wlen / self.n


def _record_is_archived(record: dict, archived_dirs: frozenset[str]) -> bool:
    """Is this document retired?

    **The record property wins** (ADR-ARCHIVED-CONTENT decision 1): a record
    states the rule it was written under, which is the whole reason the property
    exists rather than being recomputed by every reader.

    **The declaration is the fallback**, for one specific and temporary case: an
    index committed before the property shipped carries no `archived` key, and
    re-ingesting the world is not a precondition for the marker being correct.
    Both inputs are *declarations* — the record's own, or the `archived=true`
    line in `.fux/sources/dirs` — so neither path ever derives currency from a
    path convention, which is what ADR-DIR-LIST forbids.
    """
    if record.get("archived"):
        return True
    return bool(archived_dirs) and is_archived_loc(record["loc"], archived_dirs)


def rank(
    candidates: list[dict],
    query_hashes: list[str],
    df: dict[str, int],
    corpus: Corpus,
    top: int,
    *,
    archived_weight: float = 1.0,
    archived_dirs: frozenset[str] = frozenset(),
) -> list[AskResult]:
    """Score, sort, truncate. The only place any of the three happens.

    A candidate is any record whose raw line matched at least one query term;
    scoring can still return 0 (a matched hash with zero weighted tf), and those
    are dropped rather than ranked — `ask` says "no confident matches" instead
    of listing a document it scored at zero.

    `archived_weight`/`archived_dirs` are ADR-ARCHIVED-CONTENT decision 6's demotion:
    a document declared archived has its score multiplied by the weight. **At the
    shipped default (`1.0`) the multiply is skipped outright**, so a corpus with
    no configured weight scores and orders byte-identically — ADR-ARCHIVED-CONTENT
    decision 2's veto, held, and asserted by
    `tests/query/test_scan.py::test_the_marker_does_not_move_the_ranking`.

    **Every result carries `archived` regardless of the weight** (decision 3).
    The flag is computed for all candidates, never enters the sort key, and is
    what the marker and the disclaimer read. Telling a reader a document is
    retired and reordering because it is retired are two different decisions,
    and only the second one is configurable.
    """
    if corpus.n == 0:
        return []
    avg_wlen = corpus.avg_wlen
    demote = archived_weight != 1.0

    scored = []
    for record in candidates:
        s = score_record(
            record.get("terms", {}),
            record.get("wlen", 0),
            query_hashes,
            df,
            corpus.n,
            avg_wlen,
        )
        archived = _record_is_archived(record, archived_dirs)
        if demote and archived:
            s *= archived_weight
        if s > 0:
            scored.append((record, s, archived))

    # Deterministic tie-break on id — a score tie must never depend on the order
    # candidates were generated in, which is the one thing the two paths differ
    # in by construction (shard order vs postings order).
    scored.sort(key=lambda pair: (-round(pair[1], 9), pair[0]["id"]))

    return [
        AskResult(
            id=record["id"],
            title=store_mod.display_title(record),
            loc=record["loc"],
            score=s,
            archived=archived,
        )
        for record, s, archived in scored[:top]
    ]
