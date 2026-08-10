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
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .. import store as store_mod
from .bm25f import score_record
from .tokenize import tokenize

_WLEN_RE = re.compile(rb'"wlen":(\d+)')


@dataclass(frozen=True)
class AskResult:
    id: str
    title: str
    loc: str
    score: float


def ask(root: Path, query: str, top: int = 5) -> list[AskResult]:
    query_hashes = list(dict.fromkeys(store_mod.term_hash(t) for t in tokenize(query)))
    if not query_hashes:
        return []
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
            matched = [h for h, pattern in patterns.items() if pattern in line]
            if not matched:
                continue
            for h in matched:
                df[h] += 1
            candidates.append(json.loads(line))

    if total_docs == 0:
        return []
    avg_wlen = total_wlen / total_docs

    scored = []
    for record in candidates:
        s = score_record(record.get("terms", {}), record.get("wlen", 0), query_hashes, df, total_docs, avg_wlen)
        if s > 0:
            scored.append((record, s))

    # Deterministic tie-break on id — a score tie must never depend on scan order.
    scored.sort(key=lambda pair: (-round(pair[1], 9), pair[0]["id"]))

    return [
        AskResult(id=record["id"], title=record.get("title", record.get("title_h", "")), loc=record["loc"], score=s)
        for record, s in scored[:top]
    ]
