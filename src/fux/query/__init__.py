"""The query plane — `ask` / `find` / `answer`.

## The three verbs, and what they mean at M2

| verb | what it is | what changes at M4 |
|---|---|---|
| `ask` | the agent-facing default: ranked documents with citations | gains passages re-scored on fetched bytes |
| `find` | ranked documents, terse — one line per hit | unchanged |
| `answer` | the single best answer, assembled from the index | becomes extractive over fetched content |

**`answer` is honest about its ceiling.** The archived engine's `answer` was
extractive TextRank over cached document content; this build commits
statistics, not content, and the refer plane that fetches it is M4. So M2's
`answer` assembles what the index actually holds — the winning document's
title, its heading-derived phrases, and its citation — and says so. The verb
exists now so M4 is an upgrade to it rather than a new command, which is the
expensive thing to retrofit.

## Which path answers

`ask` uses the derived accelerator when one is present and fresh, and the B2
scan otherwise. **That choice can never change a result** — the differential
law (`tools/differential/`, `tests/derive/test_differential.py`) asserts the
two are byte-identical — so it is purely a speed decision. `--scan` forces the
reference path, which is what a bug report should be reproduced against.
"""

from __future__ import annotations

import json as json_mod
from pathlib import Path

from ..config import find_root
from ..errors import FuxError
from .rank import AskResult
from .scan import ask as scan_ask

__all__ = ["AskResult", "cmd_answer", "cmd_ask", "cmd_find", "run_query"]


def run_query(root: Path, query: str, top: int, *, force_scan: bool = False) -> tuple[list[AskResult], str]:
    """Answer via the accelerator when it is usable; return `(results, path)`."""
    if not force_scan:
        from ..derive import accel, format as derive_fmt

        if (derive_fmt.runtime_dir(root) / derive_fmt.STATS_NAME).exists() and accel.is_fresh(root):
            return accel.ask(root, query, top=top), "accelerator"
    return scan_ask(root, query, top=top), "scan"


def _root() -> Path:
    root = find_root()
    if root is None:
        raise FuxError("no fux.toml or .git found — run from inside a configured repo")
    return root


def cmd_ask(args) -> int:
    root = _root()
    results, path = run_query(root, args.query, args.top, force_scan=getattr(args, "scan", False))

    if args.json:
        print(json_mod.dumps({"results": [r.__dict__ for r in results]}, indent=2))
        return 0

    if not results:
        print("No confident matches.")
        return 0

    for r in results:
        print(f"{r.score:.4f}  {r.title}  ({r.loc})")
    if getattr(args, "explain", False):
        print(f"\n[{path}]")
    return 0


def cmd_find(args) -> int:
    """Ranked documents, one per line — the terse listing verb."""
    root = _root()
    results, _ = run_query(root, args.query, args.top, force_scan=getattr(args, "scan", False))

    if args.json:
        print(json_mod.dumps({"results": [r.__dict__ for r in results]}, indent=2))
        return 0

    if not results:
        print("No confident matches.")
        return 0

    for r in results:
        print(r.loc)
    return 0


def cmd_answer(args) -> int:
    """The single best answer the *index* can give — deliberately bounded.

    No model is involved and none ever will be on this path (the `$0` law).
    Until M4's refer plane can fetch the document's bytes, the honest answer is
    the winning document's own extracted structure plus its citation — not a
    fabricated sentence, and not silence.
    """
    root = _root()
    results, _ = run_query(root, args.query, 1, force_scan=getattr(args, "scan", False))

    if not results:
        if args.json:
            print(json_mod.dumps({"answer": None, "citation": None}, indent=2))
        else:
            print("No confident matches.")
        return 0

    best = results[0]
    phrases = _phrases_for(root, best.id)

    if args.json:
        print(
            json_mod.dumps(
                {
                    "answer": {"title": best.title, "phrases": phrases},
                    "citation": {"id": best.id, "loc": best.loc, "score": best.score},
                    "source": "index",
                },
                indent=2,
            )
        )
        return 0

    print(best.title)
    for phrase in phrases:
        print(f"  - {phrase}")
    print(f"\n  -- {best.loc}")
    print("\n(from the index's own structure; passage-level answers arrive with the refer plane, M4)")
    return 0


def _phrases_for(root: Path, doc_id: str) -> list[str]:
    """The winning record's heading-derived phrases, read from its shard alone."""
    from .. import store as store_mod

    path = store_mod.shard_path(root, store_mod.shard_for(doc_id))
    if not path.exists():
        return []
    _, records = store_mod.read_shard(path)
    for record in records:
        if record["id"] == doc_id:
            return list(record.get("phrases", []))
    return []
