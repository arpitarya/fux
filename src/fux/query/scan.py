"""`fux ask` — the B2 byte-prefilter scan over committed shards + BM25F.

Every shard line is read as raw bytes; a line is `json.loads`'d only if it
passes a substring check against the query's term hashes (B2, index-format
compare doc §2/§7) — full JSON parsing is the thing this scan exists to
avoid on the common case (a shard full of documents that don't match).

Corpus statistics (`df`, `n`, `avg_wlen`) are derived in this same pass and
never stored: `n`/`avg_wlen` need every document's `wlen`, which is pulled
via a cheap byte-level regex (not a full parse) so non-candidate lines still
never pay for `json.loads`; `df` falls out of the same substring check that
finds candidates, at no extra cost.

**This is the reference implementation of `ask`.** It answers a fresh clone
with no build step, and it is the oracle the derived accelerator
(`fux.derive`) is asserted byte-for-byte against. When the two disagree, this
one is right by definition — which is why scoring and sorting live in
`rank.py` and are shared rather than duplicated here.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .. import store as store_mod
from .rank import AskResult, Corpus, rank
from .tokenize import tokenize

_WLEN_RE = re.compile(rb'"wlen":(\d+)')

__all__ = ["AskResult", "ask", "query_term_hashes", "scan_candidates"]


def query_term_hashes(query: str) -> list[str]:
    """Query terms as index hashes, deduped, order preserved.

    Order is load-bearing: `rank()` sums BM25F contributions in this order, so
    both candidate generators must derive it identically from the same string.
    """
    return list(dict.fromkeys(store_mod.term_hash(t) for t in tokenize(query)))


def scan_candidates(root: Path, query_hashes: list[str]) -> tuple[list[dict], dict[str, int], Corpus]:
    """The B2 pass: candidate records, `df`, and the corpus statistics."""
    patterns = {h: f'"{h}"'.encode("ascii") for h in query_hashes}

    total_docs = 0
    total_wlen = 0
    df: dict[str, int] = dict.fromkeys(query_hashes, 0)
    candidates: list[dict] = []

    for path in store_mod.iter_shard_paths(root):
        _, lines = store_mod.raw_record_lines(path)
        for line in lines:
            total_docs += 1
            m = _WLEN_RE.search(line)
            if m:
                total_wlen += int(m.group(1))
            # The substring check is a prefilter only: a query hash can appear
            # as a literal 16-hex string somewhere outside `terms` (a title,
            # an id, a sha — anything quoted) without the document actually
            # containing that term. Once a line is worth parsing at all, `df`
            # is counted from the parsed record's own `terms` keys, which is
            # exact, rather than from the raw substring match, which is not.
            # Getting this wrong is exactly the class of bug derive/build.py's
            # `_assert_invariants` tripwire exists to catch on the accelerator
            # side — this is the same fix on the scan side, at the root.
            if not any(pattern in line for pattern in patterns.values()):
                continue
            record = json.loads(line)
            record_terms = record.get("terms", {})
            for h in query_hashes:
                if h in record_terms:
                    df[h] += 1
            candidates.append(record)

    return candidates, df, Corpus(n=total_docs, total_wlen=total_wlen)


def ask(
    root: Path,
    query: str,
    top: int = 5,
    *,
    archived_weight: float = 1.0,
    archived_dirs: frozenset[str] = frozenset(),
) -> list[AskResult]:
    query_hashes = query_term_hashes(query)
    if not query_hashes:
        return []
    candidates, df, corpus = scan_candidates(root, query_hashes)
    return rank(
        candidates, query_hashes, df, corpus, top,
        archived_weight=archived_weight, archived_dirs=archived_dirs,
    )
