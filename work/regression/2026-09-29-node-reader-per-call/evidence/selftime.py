import json,sys,glob,collections
p=json.load(open(glob.glob(sys.argv[1]+"/*.cpuprofile")[0]))
nodes={n["id"]:n for n in p["nodes"]}
dt=collections.Counter()
for s,d in zip(p["samples"],p["timeDeltas"]):
    cf=nodes[s]["callFrame"]; dt[(cf["functionName"] or "(anon)", cf["url"].split("/")[-1], cf["lineNumber"]+1)]+=d
tot=sum(dt.values())
print("total ms", tot/1000)
for k,v in dt.most_common(12): print(round(v/1000), k)
