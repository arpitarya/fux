import json,subprocess,sys
py=sys.executable; T=sys.argv[1]; out_path=sys.argv[2]
rows=[json.loads(l) for l in open('$(dirname $0)/id-queries.jsonl')]
def ask(q,top):
    r=subprocess.run([py,"-m","fux.cli","ask",q,"--json","--top",str(top)],cwd=T,capture_output=True,text=True)
    try: return json.loads(r.stdout)
    except Exception: return None
out=[]
for r in rows:
    d=ask(r["question"],20); locs=[x["loc"] for x in (d.get("results") or [])] if d else []
    rank=(locs.index(r["primary"])+1) if r["primary"] in locs else None
    anyrel=next((i+1 for i,l in enumerate(locs) if l in r["relevant"]),None)
    d2=ask(r["identifier"],20); locs2=[x["loc"] for x in (d2.get("results") or [])] if d2 else []
    rank2=(locs2.index(r["primary"])+1) if r["primary"] in locs2 else None
    out.append({**{k:r[k] for k in ("id","identifier","question","primary","relevant")},"rank_primary_q":rank,"rank_anyrelevant_q":anyrel,"rank_primary_bare":rank2,"n_results":len(locs),"top3":locs[:3]})
    print(f"{r['id']} {r['identifier']:16} q:{str(rank):>4} anyrel:{str(anyrel):>4} bare:{str(rank2):>4} n={len(locs):>2}  {[l.split('/')[-1][:20] for l in locs[:3]]}")
json.dump(out,open(out_path,'w'),indent=1)
h3=sum(1 for o in out if o["rank_primary_q"] and o["rank_primary_q"]<=3); h1=sum(1 for o in out if o["rank_primary_q"]==1)
a3=sum(1 for o in out if o["rank_anyrelevant_q"] and o["rank_anyrelevant_q"]<=3); b3=sum(1 for o in out if o["rank_primary_bare"] and o["rank_primary_bare"]<=3)
print(f"\n{T.split('/')[-1]}: primary hit@1 {h1}/33 · primary hit@3 {h3}/33 · any-relevant hit@3 {a3}/33 · bare-id hit@3 {b3}/33 · improvement headroom (primary not in top-3) {33-h3}")
