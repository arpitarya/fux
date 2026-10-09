"""`stats.json` — the corpus-wide numbers BM25F reads, stored RAW.

**Owned by [SR-RUNTIME-STATS](../../../records/0125_runtime-stats.md)** since 2026-10-05 (W-261, Arpit's
ruling that every `kind: component` record owns a file). A pure move out of
`derive/_build.py`, which still decides WHEN this file is written (after the
planes it describes, in `build()`'s order) — SR-T1-ACCELERATOR's. What is here
is the plane's key set — `n`, `total_flen`, `total_anchor_len` — and its
bytes; a key added here is the veto this record carries on the set growing. Its Node twin is `node/src/derive/stats.mjs`.
"""

from __future__ import annotations

from pathlib import Path

from . import format as fmt

__all__ = ["payload", "write"]


def payload(
    *, n: int, total_flen: list[int], total_anchor_len: int,
    sec_units: int, sec_total_flen: list[int],
) -> dict:
    """The plane's content: raw totals, never a weighted or averaged number, so
    a field weight cannot bake into a derived file.

    `sec_units` and `sec_total_flen` are W-236's: the section `avg_wlen`'s
    count and its raw body and heading totals (SR-SECTIONS decision 5)."""
    return {
        "n": n,
        "total_flen": total_flen,
        "total_anchor_len": total_anchor_len,
        "sec_units": sec_units,
        "sec_total_flen": sec_total_flen,
    }


def write(directory: Path, stats: dict) -> int:
    """`stats.json` for one build. Returns the bytes written."""
    return fmt.write_json(directory / fmt.STATS_NAME, stats)
