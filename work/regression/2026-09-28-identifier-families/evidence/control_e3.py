#!/usr/bin/env python3
"""E3 — the prose control: 60 RETIRED set-1 questions, rank-1 document per arm.

Every other id of `work/golden/retired/set-1/questions.jsonl` in file order,
capped at 60 (W-205's rule, PRE-REGISTRATION §5). Question text only; retired
data carries no golden claim, and the endpoint (did rank 1 change?) needs no
answer. Run with the ARM's interpreter.
"""
import json
import sys
from pathlib import Path

tree, out = Path(sys.argv[1]), Path(sys.argv[2])
REPO = Path(__file__).resolve().parents[4]
qs = [json.loads(l) for l in (REPO / "work/golden/retired/set-1/questions.jsonl").read_text("utf-8").splitlines() if l.strip()]
sample = qs[::2][:60]
from fux import api

ix = api.open(tree)
rows = []
for q in sample:
    got = ix.ask(q["question"], top=5, band=False, sections=False)
    rows.append({"id": q["id"], "top1": got.results[0].loc if got.results else None})
out.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
print(f"{len(rows)} control questions")
