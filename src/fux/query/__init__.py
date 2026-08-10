"""The query plane — `fux ask`: B2 byte-prefilter scan + BM25F, with
citations. Lexical only this milestone (dense/graph lanes are M2/M3).
"""

from __future__ import annotations

import json as json_mod

from ..config import find_root
from ..errors import FuxError
from .scan import ask


def cmd_ask(args) -> int:
    root = find_root()
    if root is None:
        raise FuxError("no fux.toml or .git found — run from inside a configured repo")

    results = ask(root, args.query, top=args.top)

    if args.json:
        print(json_mod.dumps({"results": [r.__dict__ for r in results]}, indent=2))
        return 0

    if not results:
        print("No confident matches.")
        return 0

    for r in results:
        print(f"{r.score:.4f}  {r.title}  ({r.loc})")
    return 0
