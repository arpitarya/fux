import json, sys, pathlib
root = pathlib.Path.home()/"my_programs/fux-lab/corpora/golden"
for rung in sorted(p for p in root.iterdir() if p.is_dir()):
    d=t=w=0; kinds={}
    for f in sorted((rung/".fux/index").glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip(): continue
            o=json.loads(line)
            if "_format" in o: continue
            d+=1
            for e in (o.get("edges") or []):
                t+=1
                kinds[e.get("kind","?")]=kinds.get(e.get("kind","?"),0)+1
                if e.get("at") or e.get("al"): w+=1
    print(f"{rung.name:<12} docs {d:6}  edges {t:6}  anchor-bearing {w:6}   kinds={kinds}")
