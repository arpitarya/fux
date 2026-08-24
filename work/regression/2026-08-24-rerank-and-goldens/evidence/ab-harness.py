"""Per-query A/B: which goldens the reranker FIXED and which it BROKE."""
import json, re, pathlib, subprocess, sys

ROOT = pathlib.Path("/tmp/pg")
GOLD = [json.loads(l) for l in (ROOT/"goldens/queries.jsonl").read_text().splitlines() if l.strip()]

def set_weight(w):
    p = ROOT/"fux.toml"
    t = re.sub(r"\n\[ranking\][^\[]*", "\n", p.read_text())
    p.write_text(t.rstrip() + f"\n\n[ranking]\nrerank_weight = {w}\n")

def ranks(w):
    set_weight(w)
    out = {}
    for g in GOLD:
        proc = subprocess.run([sys.executable, "-m", "fux.cli", "ask", g["q"], "--json", "--top", "5"],
                              cwd=ROOT, capture_output=True, text=True)
        locs = [r["loc"] for r in json.loads(proc.stdout)["results"]]
        out[g["id"]] = (locs.index(g["doc"]) + 1 if g["doc"] in locs else None, g.get("max_rank", 1))
    return out

base, rer = ranks(0.0), ranks(float(sys.argv[1]))
ok = lambda v: v[0] is not None and v[0] <= v[1]
fixed  = [q for q in base if not ok(base[q]) and ok(rer[q])]
broke  = [q for q in base if ok(base[q]) and not ok(rer[q])]
still  = [q for q in base if not ok(base[q]) and not ok(rer[q])]
print(f"baseline pass {sum(ok(v) for v in base.values())}/50 -> rerank pass {sum(ok(v) for v in rer.values())}/50")
print(f"FIXED  {len(fixed)}: {fixed}")
print(f"BROKE  {len(broke)}: {broke}")
print(f"still failing {len(still)}: {still}")
for q in still:
    print(f"   {q}: rank {base[q][0]} -> {rer[q][0]} (want <= {base[q][1]})")
