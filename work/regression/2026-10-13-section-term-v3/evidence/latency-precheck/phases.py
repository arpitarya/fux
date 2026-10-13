import json, sys, time, dataclasses, statistics
from pathlib import Path
from fux import tune as tune_mod
from fux.query import scan, rank as rank_mod
from fux.query import identifiers as ids_mod
root = Path(sys.argv[1]); qs = [json.loads(l)["question"] for l in open(sys.argv[2]) if l.strip()][:40]
tune = tune_mod.load(root, enabled=True); on = tune.scoring; off = dataclasses.replace(on, section=0.0)
ids = ids_mod.for_root(root)
orig_attach = scan._attach_sections
t_attach = []
def timed_attach(*a):
    t = time.perf_counter(); orig_attach(*a); t_attach.append(time.perf_counter() - t)
scan._attach_sections = timed_attach
orig_gain = rank_mod._section_gain
t_gain = [0.0]
def timed_gain(*a):
    t = time.perf_counter(); r = orig_gain(*a); t_gain[0] += time.perf_counter() - t; return r
rank_mod._section_gain = timed_gain
res = {"off": [], "on": [], "attach": [], "gain": [], "ncand": [], "nsec": []}
for q in qs:
    h = scan.query_term_hashes(q, ids)
    for sc, key in ((off, "off"), (on, "on")):
        t_gain[0] = 0.0
        t = time.perf_counter(); r = scan.ask(root, q, 10, scoring=sc); res[key].append(time.perf_counter() - t)
    res["attach"].append(t_attach[-1]); res["gain"].append(t_gain[0])
    c, _, _ = scan.scan_candidates(root, h, scoring=off)
    res["ncand"].append(len(c)); res["nsec"].append(sum(1 for x in c if x.get("nsec")))
for k, v in res.items():
    print(k, round(statistics.median(v) * (1000 if k not in ("ncand", "nsec") else 1), 1))
