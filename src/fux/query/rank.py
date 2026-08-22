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
from .bm25f import score_record


@dataclass(frozen=True)
class AskResult:
    id: str
    title: str
    loc: str
    score: float


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


def _is_archived_loc(loc: str, archived_dirs: frozenset[str]) -> bool:
    """`loc` falls under one of `archived_dirs` — a directory entry or an
    exact single-file entry, mirroring how `gitdir.walk_sources` resolves an
    entry against the filesystem."""
    return any(loc == d or loc.startswith(f"{d}/") for d in archived_dirs)


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

    `archived_weight`/`archived_dirs` are ADR-DIR-LIST decision 11's demotion:
    a document under a declared-archived directory has its score multiplied by
    the weight. At the shipped default (`1.0`) this is skipped outright, so a
    corpus with no configured weight scores and orders byte-identically to one
    with the property computed at all — decision 6's veto, held.
    """
    if corpus.n == 0:
        return []
    avg_wlen = corpus.avg_wlen
    demote = archived_weight != 1.0 and archived_dirs

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
        if demote and _is_archived_loc(record["loc"], archived_dirs):
            s *= archived_weight
        if s > 0:
            scored.append((record, s))

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
        )
        for record, s in scored[:top]
    ]
