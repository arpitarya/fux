"""Print every question's `ask --json` and `fux_search` payloads, one JSON line each.

Run under EITHER engine (`PYTHONPATH=<its src>`): the pre-W-300 engine ignores
`scope`, which is what makes the same script the byte-equality gate's two arms.

    python payloads.py <root> <questions.tsv> [scope]
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from types import SimpleNamespace


def main() -> int:
    root, questions = Path(sys.argv[1]), Path(sys.argv[2])
    scope = sys.argv[3] if len(sys.argv) > 3 else None
    from fux import mcp
    from fux.query import build_ask

    with questions.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    for row in rows:
        args = SimpleNamespace(
            query=row["question"], top=10, also=None, expand=None, fast=None, scan=True, why=False,
            related=None, sections=True, band=True, max_headings=3, explain=None, no_tune=False,
        )
        call = {"query": row["question"], "k": 10}
        if scope is not None:
            args.scope = scope
            call["scope"] = scope
        ask = build_ask(root, args, compose=True, with_related=True).payload()
        search = mcp._search(root, call, top=10, max_headings=3)
        print(json.dumps({"id": row["id"], "ask": ask, "search": search}, sort_keys=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
