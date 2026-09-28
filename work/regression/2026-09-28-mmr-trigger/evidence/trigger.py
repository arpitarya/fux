#!/usr/bin/env python3
"""W-168 step 7 — how often could the ruled MMR swap fire? Key-free.

The ruled design (Arpit, 2026-09-28): if the top 5 all lie in one graph
community, #5 is swapped for the best-ranked document of another community.
This counts, from a captured hand-off and the arm tree's own graph plane:

- `fires`     — questions whose top 5 share one community;
- `ceiling`   — of those, how many have another community's document in ranks
                6–10 of the returned ten (the candidate depth Arpit ruled).

A document with no edge is absent from the graph plane; `graph/community.py`
defines an unlinked document as its own community, so it gets a singleton label.
It reads the hand-off (engine output) and the arm's index. It opens no key.

    .venv/bin/python work/regression/2026-09-28-mmr-trigger/evidence/trigger.py \
        ~/my_programs/fux-lab/arms/runs/ip-0.1/rung-01000 \
        work/regression/2026-09-28-intent-prior/evidence/ip-0.1/rung-01000/handoff-set-4-claude.jsonl
"""
import collections
import json
import sys
from pathlib import Path

import fux.api as api
from fux import store

tree, handoff = Path(sys.argv[1]), Path(sys.argv[2])
plane = api.open(tree)._plane()
by = {}
for p in store.iter_shard_paths(tree):
    for r in store.read_shard(p)[1]:
        by[r["id"]] = r
        by[r.get("loc")] = r


def community(x: str) -> str:
    r = by.get(x)
    c = plane.community_of(r["id"]) if r else None
    return c if c is not None else "solo:" + x


OUT = Path(__file__).resolve().parent / "per-query.jsonl"
rows = [json.loads(line) for line in handoff.read_text(encoding="utf-8").splitlines() if line.strip()]
fires, ceiling, spread, per = [], [], collections.Counter(), []
for row in rows:
    ranked = [x for x in row.get("ranked") or [] if x]
    top = [community(x) for x in ranked[:5]]
    spread[len(set(top))] += 1
    fired = len(top) == 5 and len(set(top)) == 1
    swappable = fired and any(community(x) != top[0] for x in ranked[5:10])
    if fired:
        fires.append(row["id"])
    if swappable:
        ceiling.append(row["id"])
    per.append({"id": row["id"], "communities_top5": len(set(top)), "fires": fired, "swappable_6_10": swappable})
OUT.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in per), encoding="utf-8")
print(f"questions={len(rows)} fires={len(fires)} ceiling@6-10={len(ceiling)}")
print("distinct communities in the top 5:", dict(sorted(spread.items())))
print(f"graph: {len(plane.communities)} linked documents in {len(set(plane.communities.values()))} communities")
print("fires:", " ".join(fires))
print("ceiling:", " ".join(ceiling))
