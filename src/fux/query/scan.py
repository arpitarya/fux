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
from ..store import TF_FIELDS
from .bm25f import DEFAULT_SCORING, Scoring, derive_wlen
from .tokenize import tokenize

#: The byte-level oracle, now over per-field counts (W-76 Phase 1).
#:
#: `wlen` used to be committed and could be read with one integer capture.
#: It is now DERIVED from `flen` at the weights in force, so this pass parses
#: the array and applies `derive_wlen` — the same function the scorer, the
#: accelerator's bound and the refer plane use, so the four cannot drift.
#:
#: Still a raw-bytes read rather than a JSON parse: this runs on every line in
#: the corpus, candidate or not, and parsing every record to sum a length is
#: what the prefilter exists to avoid.
_FLEN_RE = re.compile(rb'"flen":\[([0-9,\s]*)\]')


#: W-76 Phase 2. Same reasoning as `_FLEN_RE`: read from bytes on every line,
#: candidate or not, rather than parsing the corpus to find one integer.
_MTIME_RE = re.compile(rb'"mtime":(\d+)')


def _flen_from_line(line: bytes) -> list[int] | None:
    m = _FLEN_RE.search(line)
    if m is None:
        return None
    inner = m.group(1).strip()
    if not inner:
        return []
    return [int(part) for part in inner.split(b",")]

__all__ = ["AskResult", "ask", "query_term_hashes", "scan_candidates"]


def query_term_hashes(query: str) -> list[str]:
    """Query terms as index hashes, deduped, order preserved.

    Order is load-bearing: `rank()` sums BM25F contributions in this order, so
    both candidate generators must derive it identically from the same string.
    """
    return list(dict.fromkeys(store_mod.term_hash(t) for t in tokenize(query)))


def scan_candidates(
    root: Path, query_hashes: list[str], *, scoring: Scoring = DEFAULT_SCORING
) -> tuple[list[dict], dict[str, int], Corpus]:
    """The B2 pass: candidate records, `df`, and the corpus statistics."""
    patterns = {h: f'"{h}"'.encode("ascii") for h in query_hashes}

    total_docs = 0
    # Per-field token-count totals, summed raw and weighted ONCE at the end.
    # Summing `derive_wlen` per record would give the same number today and
    # would silently bake the weights into a running total the moment anything
    # here started caching it — the accelerator's stats plane made exactly that
    # mistake (ADR-TUNE, 2026-08-24).
    total_flen = [0] * len(TF_FIELDS)
    newest_mtime = 0
    df: dict[str, int] = dict.fromkeys(query_hashes, 0)
    candidates: list[dict] = []

    for path in store_mod.iter_shard_paths(root):
        _, lines = store_mod.raw_record_lines(path)
        for line in lines:
            total_docs += 1
            flen = _flen_from_line(line)
            if flen is not None:
                for i, count in enumerate(flen):
                    total_flen[i] += count
            mt = _MTIME_RE.search(line)
            if mt is not None:
                value = int(mt.group(1))
                if value > newest_mtime:
                    newest_mtime = value
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

    return (
        candidates,
        df,
        Corpus(
            n=total_docs,
            total_wlen=derive_wlen(total_flen, scoring),
            newest_mtime=newest_mtime,
        ),
    )


def ask(
    root: Path,
    query: str,
    top: int = 5,
    *,
    archived_weight: float = 1.0,
    archived_dirs: frozenset[str] = frozenset(),
    weighting=None,
    scoring: Scoring = DEFAULT_SCORING,
) -> list[AskResult]:
    query_hashes = query_term_hashes(query)
    if not query_hashes:
        return []
    candidates, df, corpus = scan_candidates(root, query_hashes, scoring=scoring)
    return rank(
        candidates, query_hashes, df, corpus, top,
        archived_weight=archived_weight, archived_dirs=archived_dirs,
        weighting=weighting, scoring=scoring,
    )
