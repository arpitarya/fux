"""Sweep coverage sharpness x weight. A passage missing a query term is not
'80% as good' -- the missing term may be the discriminating one."""
import json, pathlib, sys
from fux.query.scan import ask
from fux.query.analyzer import analyze
from fux.query import rerank
from fux.refer.chunk import chunk

ROOT = pathlib.Path("/tmp/pg")
GOLD = [json.loads(l) for l in (ROOT/"goldens/queries.jsonl").read_text().splitlines() if l.strip()]

TEXT = {p.name: (ROOT/"docs"/p.name).read_text() for p in (ROOT/"docs").iterdir()}
CHUNKS = {k: [analyze(c.text) for c in chunk(v)] for k, v in TEXT.items()}

def doc_boost(qt, loc, power):
    best = 0.0
    for terms in CHUNKS[loc.split("/")[-1]]:
        cov, span, adj = rerank.signals(qt, terms)
        if cov <= 0: continue
        s = (cov ** power) * (0.55 + 0.30*span + 0.15*adj)
        if s > best: best = s
    return best

BASE = {}
for g in GOLD:
    BASE[g["id"]] = ask(ROOT, g["q"], top=20)

def evaluate(power, weight):
    ok = 0
    for g in GOLD:
        qt = analyze(g["q"])
        scored = [(r.score * (1 + weight*doc_boost(qt, r.loc, power)), r) for r in BASE[g["id"]]]
        scored.sort(key=lambda p: (-round(p[0], 9), p[1].id))
        locs = [r.loc for _, r in scored[:5]]
        if g["doc"] in locs and locs.index(g["doc"]) + 1 <= g.get("max_rank", 1):
            ok += 1
    return ok

print("        w=0.6  w=1.0  w=1.5  w=2.0  w=3.0")
for power in (1, 2, 3, 4):
    row = "  ".join(f"{evaluate(power, w):5d}" for w in (0.6, 1.0, 1.5, 2.0, 3.0))
    print(f"cov^{power}   {row}")
