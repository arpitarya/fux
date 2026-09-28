#!/usr/bin/env python3
"""Rank every frozen variant query against ONE arm tree, in process.

Run with THAT arm's interpreter (the before arm sets PYTHONPATH to its worktree),
so the engine under test is the one that built the tree. Writes one JSON row per
query: the rank of the primary in the top 20, and the top 3 locators. Asks
`fux.api.open(tree).ask(q, top=20, band=False, sections=False)` — `run_query`,
the path `fux ask` takes.
"""
import json
import sys
from pathlib import Path

queries, tree, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
import fux
from fux import api

ix = api.open(tree)
rows = []
for line in queries.read_text(encoding="utf-8").splitlines():
    q = json.loads(line)
    got = ix.ask(q["query"], top=20, band=False, sections=False)
    locs = [r.loc for r in got.results]
    rank = locs.index(q["primary"]) + 1 if q["primary"] in locs else None
    rows.append({**q, "rank": rank, "top3": locs[:3]})
out.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
print(f"{fux.__file__}  {len(rows)} queries  hit@1={sum(r['rank'] == 1 for r in rows)}")
