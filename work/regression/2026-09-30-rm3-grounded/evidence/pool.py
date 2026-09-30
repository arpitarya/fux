#!/usr/bin/env python3
"""W-237 — the pool, from Arpit's score of the 2026-09-27 capture. Counts only.

Reads `scores/single/rung-01000/set-4-claude.json` — ids, ranks and booleans,
the output [L11](../../../../records/0013_LAW-11-sealed-answer-key.md) decision 13
lets a session read — and the frozen tag. It opens no key and runs no scorer,
and it prints counts, never an id.

    python3 work/regression/2026-09-30-rm3-grounded/evidence/pool.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SCORE = ROOT / "work/regression/2026-09-27-golden-set-4-rung-01000/scores/single/rung-01000/set-4-claude.json"


def main() -> int:
    tags = {r["id"]: r["rm3_grounded"] for r in map(json.loads, (HERE / "tags-set-4-claude.jsonl").read_text(encoding="utf-8").splitlines()) if r}
    rows = {r["id"]: r for r in json.loads(SCORE.read_text(encoding="utf-8"))["rows"]}
    assert set(rows) == set(tags), "the score's ids are not the tagged set's"
    tagged = [i for i, t in tags.items() if t]
    out = {
        "questions": len(tags),
        "tagged": len(tagged),
        "pool_miss@1_hit@10": sum(1 for i in tagged if rows[i]["hit@10"] and not rows[i]["hit@1"]),
        "pool_miss@1_primary_in_top10": sum(
            1 for i in tagged if not rows[i]["hit@1"] and rows[i]["primary_rank"] is not None and rows[i]["primary_rank"] <= 10),
        "tagged_hit@1": sum(1 for i in tagged if rows[i]["hit@1"]),
        "set_hit@1": sum(1 for i in tags if rows[i]["hit@1"]),
    }
    (HERE / "pool.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
