"""W-221 — RM3's first pass (the LEXICAL top 10) vs the list `ask` shows (GRAPH-BOOSTED).

Run from the repo root with fux's own venv:

    .venv/bin/python work/regression/2026-09-23-rm3/evidence/first_pass_check.py

Reads the `rm3-0.0` arm copy (tune identical to the rung's; `ask_boost = true`)
and the released `set-2-u` questions — ids and text only. **No key, no score.**

Per question: one `run_query` at `rm3_weight = 0.0`. Its `trace_out["window"]`
is the un-expanded lexical candidate list at `depth` — byte for byte the call
RM3's first pass makes (`query/__init__.py`, the `rm3_weight > 0` branch), so
`window[:10]` is RM3's feedback set. The returned list is the graph-boosted top
10. Both lists are then fed to `rm3.feedback_terms`, the boosted ten carrying
their lexical first-pass scores (the only score `P(q|d)` is defined on).
"""
import json
from pathlib import Path

from fux.query import _tune, run_query
from fux.query.rm3 import feedback_terms
from fux.query.scan import query_term_hashes

ROOT = Path.home() / "my_programs/fux-lab/arms/runs/rm3-0.0/rung-01000"
REPO = Path(__file__).resolve().parents[4]
EV = Path(__file__).resolve().parent

qs = [json.loads(l) for l in open(REPO / "work/golden/questions/set-2-u.jsonl")]
tags = {r["id"]: r["rm3_underspecified"] for r in map(json.loads, open(EV / "tags-set-2-u.jsonl"))}
cap = {r["id"]: r["ranked"] for r in map(json.loads, open(EV / "rm3-0.0/rung-01000/predictions-set-2-u.jsonl"))}
tune = _tune(ROOT)
strip = lambda i: i.removeprefix("file:")

with open(EV / "first-pass-check.jsonl", "w") as out:
    for q in qs:
        trace: dict = {}
        final, _ = run_query(ROOT, q["question"], 10, trace_out=trace, tune=tune)
        window = trace["window"]
        by_id = {r.id: r for r in window}
        lex, boo = window[:10], [by_id[r.id] for r in final]  # KeyError = a boosted doc outside the window
        qh = query_term_hashes(q["question"])
        L, B = [strip(r.id) for r in lex], [strip(r.id) for r in final]
        tl = feedback_terms(ROOT, lex, qh, tune.scoring)
        tb = feedback_terms(ROOT, boo, qh, tune.scoring)
        kind = "identical" if L == B else "reordered" if set(L) == set(B) else "membership"
        out.write(json.dumps({
            "id": q["id"], "tagged": tags[q["id"]], "kind": kind,
            "doc_overlap": len(set(L) & set(B)), "rank1_same": L[0] == B[0],
            "boosted_matches_capture": B == cap[q["id"]][:10],
            "term_overlap": len(set(tl) & set(tb)), "terms_identical": tl == tb,
            "lexical": L, "boosted": B,
        }, sort_keys=True) + "\n")
