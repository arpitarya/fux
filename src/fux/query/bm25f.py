"""BM25F scoring — weighted-tf-then-saturate once, never per-field BM25
summed (CLAUDE.md law). Ported from `archive/v0.26/src/fux/index/bm25f.py`,
adapted to the M1 schema: two fields (`heading`, `body`) — the archived
third `path` field is dropped (ADR-RECORD). Defaults: heading=3.0, body=1.0,
k1=1.2, b=0.75, matching the archived non-path weights.

Corpus statistics (`df`, `n`, `avg_wlen`) are inputs here, never derived
inside this module — `query/scan.py` computes them in the same pass as the
byte-prefilter scan (compare doc §5: "never stored").
"""

from __future__ import annotations

import math

HEADING_WEIGHT = 3.0
BODY_WEIGHT = 1.0
K1 = 1.2
B = 0.75


def idf(df: int, n: int) -> float:
    return math.log((n - df + 0.5) / (df + 0.5) + 1)


def score_record(
    terms: dict[str, list[int]],
    wlen: int,
    query_hashes: list[str],
    df: dict[str, int],
    n: int,
    avg_wlen: float,
) -> float:
    """Sum of each matched query term's weight-then-saturate contribution."""
    if n <= 0 or avg_wlen <= 0:
        return 0.0
    total = 0.0
    for h in query_hashes:
        tf = terms.get(h)
        if tf is None:
            continue
        tf_heading, tf_body = tf[0], tf[1]
        wtf = HEADING_WEIGHT * tf_heading + BODY_WEIGHT * tf_body
        if wtf == 0:
            continue
        denom = wtf + K1 * (1 - B + B * wlen / avg_wlen)
        total += idf(df.get(h, 0), n) * wtf * (K1 + 1) / denom
    return total
