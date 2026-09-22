#!/usr/bin/env python3
"""W-168 step 5's precondition: the pool RM3 could win at rank 1 — counted
before the build, from the frozen tags and the filed 2026-09-22 scores.

Reads only `id`, `hit@1` and `hit@10` from the scores file. It does not read
the `answerable`-bearing columns: a question that hits at 10 has a relevant
document, so it is answerable by construction.

    python3 work/regression/2026-09-23-rm3/evidence/pool.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tools" / "quality-controls"))

from resolution import smallest_detectable  # noqa: E402
from verdict import ALPHA  # noqa: E402

SCORES = ROOT / "work/regression/2026-09-22-golden-set-2u-rung-01000/scores/single/rung-01000/set-2-u.json"
TAGS = HERE / "tags-set-2-u.jsonl"


def main() -> int:
    tags = {r["id"]: r["rm3_underspecified"]
            for r in map(json.loads, TAGS.read_text(encoding="utf-8").splitlines()) if r}
    rows = {r["id"]: r for r in json.loads(SCORES.read_text(encoding="utf-8"))["rows"]}
    if set(tags) != set(rows):
        sys.exit(f"refusing: tags and scores disagree on ids ({len(tags)} vs {len(rows)})")

    def count(pred, tagged):
        return sum(1 for i, r in rows.items() if tags[i] is tagged and pred(r))

    out = {}
    for label, tagged in (("tagged", True), ("untagged", False)):
        out[label] = {
            "n": sum(1 for i in rows if tags[i] is tagged),
            "hit@1": count(lambda r: r["hit@1"], tagged),
            "reorderable_miss": count(lambda r: r["hit@10"] and not r["hit@1"], tagged),
            "never_retrieved": count(lambda r: not r["hit@10"], tagged),
        }
    pool = out["tagged"]["reorderable_miss"]
    need = smallest_detectable(pool, ALPHA) if pool else None
    out["pool"] = pool
    out["net_needed_if_whole_pool_flips"] = need
    out["smallest_clearing_wins_zero_losses"] = 6 if pool >= 6 else None
    out["stop"] = pool < 6
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
