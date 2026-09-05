#!/usr/bin/env python3
"""W-107 Phase 0 — how far apart are Python and Node, and does it flip an order?

Three questions, in the order they matter:
  1. how many scores differ at all (bit-for-bit)?
  2. how many differ after `round(9)` — the tolerance option (b) proposes?
  3. how many QUERIES have a different top-5 ordering — the only failure a
     caller can see?

The sort key is `rank.py`'s: `(-round(score, 9), id)`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

rows = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

total = differ = differ_r9 = 0
max_ulp_rel = 0.0
flipped, flipped_r9 = [], []
per_query = []

for row in rows:
    d = 0
    for doc in row["docs"]:
        total += 1
        if doc["py"] != doc["node"]:
            differ += 1
            d += 1
            if doc["py"]:
                max_ulp_rel = max(max_ulp_rel, abs(doc["py"] - doc["node"]) / abs(doc["py"]))
        if round(doc["py"], 9) != round(doc["node"], 9):
            differ_r9 += 1

    def top5(key):
        ordered = sorted(row["docs"], key=lambda x: (-round(x[key], 9), x["id"]))
        return [x["id"] for x in ordered[:5]]

    def top5_exact(key):
        ordered = sorted(row["docs"], key=lambda x: (-x[key], x["id"]))
        return [x["id"] for x in ordered[:5]]

    same_r9 = top5("py") == top5("node")
    same_exact = top5_exact("py") == top5_exact("node")
    if not same_exact:
        flipped.append(row["q"])
    if not same_r9:
        flipped_r9.append(row["q"])
    per_query.append((row["q"], len(row["docs"]), d, same_exact, same_r9))

print(f"documents scored          : {total}")
print(f"scores differing bit-for-bit: {differ}  ({differ/total*100:.3f} %)")
print(f"scores differing at round(9): {differ_r9}  ({differ_r9/total*100:.3f} %)")
print(f"max relative difference     : {max_ulp_rel:.3e}")
print(f"queries with a different top-5 (exact sort)   : {len(flipped)}")
print(f"queries with a different top-5 (round(9) sort): {len(flipped_r9)}")
if flipped:
    print("  flipped:", flipped[:10])

with open(sys.argv[2], "w", encoding="utf-8", newline="") as f:
    f.write("query,n_docs,n_scores_differing,top5_same_exact,top5_same_round9\n")
    for q, nd, d, se, sr in per_query:
        f.write(f'"{q}",{nd},{d},{int(se)},{int(sr)}\n')
print(f"per-query rows -> {sys.argv[2]}")
