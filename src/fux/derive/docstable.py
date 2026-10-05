"""`docs.jsonl` — the docidx-ordered doc table every derived structure joins against.

**Owned by [SR-DOCS-TABLE](../../../records/0122_docs-table.md)** since 2026-10-05 (W-261, Arpit's
ruling that every `kind: component` record owns a file). A pure move out of
`derive/_build.py`, which still decides WHEN this file is written (after the
planes it describes, in `build()`'s order) — SR-T1-ACCELERATOR's. What is here
is the table's bytes: one sorted-key JSON object per document, in docidx
order; the fields are `[runtime] docs_fields`, carried and never derived. Its Node twin is `node/src/derive/docstable.mjs`.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import format as fmt

__all__ = ["write"]


def write(directory: Path, docs: list[dict]) -> int:
    """`docs.jsonl`: one docidx-ordered row per document. Returns the bytes."""
    payload = b"".join(
        json.dumps(doc, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8") + b"\n"
        for doc in docs
    )
    path = directory / fmt.DOCS_NAME
    path.write_bytes(payload)
    return len(payload)
