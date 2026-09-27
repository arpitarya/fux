#!/usr/bin/env python3
"""W-168 step 4 — the precondition pool, from the frozen tags and a FILED score.

The score is `score.py`'s own output on the 2026-09-24 generation-2 capture
(`2026-09-24-golden-gen2-rung-01000/scores/single/rung-01000/set-3-u.json`),
which carries ids, ranks and flags only (L11's scoring carve-out). No key is
opened. Writes counts and ids to `pool.json`; never a question, never an answer.

    .venv/bin/python work/regression/2026-09-27-mined-expansion/evidence/pool.py
"""

from __future__ import annotations

import json
import pathlib

EV = pathlib.Path(__file__).resolve().parent
ROOT = EV.parents[3]
SCORES = ROOT / "work/regression/2026-09-24-golden-gen2-rung-01000/scores/single/rung-01000/set-3-u.json"


def main() -> None:
    tags = {r["id"]: r["tagged"] for r in map(json.loads, (EV / "tags-set-3-u.jsonl").read_text().splitlines())}
    rows = {r["id"]: r for r in json.loads(SCORES.read_text())["rows"]}
    assert set(tags) == set(rows), "the tags and the scores name different questions"
    out: dict = {}
    for name, keep in (("tagged", True), ("untagged", False), ("all", None)):
        ids = sorted(i for i in tags if keep is None or tags[i] == keep)
        ans = [i for i in ids if not rows[i]["answered_unanswerable"]]
        out[name] = {
            "questions": len(ids),
            "answerable": len(ans),
            "hit@1": sum(bool(rows[i]["hit@1"]) for i in ans),
            "pool": sorted(i for i in ans if not rows[i]["hit@1"] and rows[i]["hit@10"]),
            "not_in_top10": sum(not rows[i]["hit@10"] for i in ans),
        }
        out[name]["pool_size"] = len(out[name]["pool"])
    (EV / "pool.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    for name, v in out.items():
        print(f"{name:9} questions {v['questions']:3} answerable {v['answerable']:3} hit@1 {v['hit@1']:3} "
              f"pool {v['pool_size']:3} not-in-top10 {v['not_in_top10']:3}")


if __name__ == "__main__":
    main()
