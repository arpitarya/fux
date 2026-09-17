"""What actually takes rank 1 on the contests the ON arm broke? Diagnosis, not an arm."""
import json, subprocess, sys, re
from pathlib import Path
TREE = Path("/private/tmp/claude-501/-Users-arpitarya-my-programs-fux/bfdf0f61-9b1d-4f48-97d7-5a4381f3dc8b/scratchpad/lab")
ROWS = Path("/Users/arpitarya/my_programs/fux/work/regression/2026-09-16-rerank-quality-b2/evidence/per-contest-rows.jsonl")

def set_w(v):
    p = TREE/".fux"/"tune.toml"; t = p.read_text()
    t = re.sub(r"^rerank_weight\s*=.*$", f"rerank_weight = {v}", t, flags=re.M)
    p.write_text(t)

def ask(q):
    o = subprocess.run([sys.executable,"-m","fux.cli","ask",q,"--json","--top","10"],
                       cwd=TREE, capture_output=True, text=True)
    try: return [r.get("loc") for r in (json.loads(o.stdout).get("results") or [])]
    except Exception: return []

rows=[json.loads(l) for l in ROWS.read_text().splitlines() if l.strip()]
worse=[r for r in rows if r["ask_off"] and not r["ask_on"]]
orig = (TREE/".fux"/"tune.toml").read_text()
out=[]
try:
    set_w(1.0)
    for r in worse:
        locs = [l for l in ask(r["query"]) if l != r["source"]]
        out.append({**r, "won_on": locs[0] if locs else None})
finally:
    (TREE/".fux"/"tune.toml").write_text(orig)

from collections import Counter
# Is the winner ANOTHER document that cites the same target? Approximate it by
# asking whether the winner is a `work/` or `docs/` file (a citer) vs a record
# (a peer of the target).
kinds = Counter()
for r in out:
    w = r["won_on"] or "(nothing)"
    t = r["target"]
    if w == t: kinds["the target itself (?!)"] += 1
    elif w.startswith("records/") and t.startswith("records/"): kinds["another RECORD"] += 1
    elif w.startswith(("work/","docs/","CLAUDE","README")): kinds["a citing-side doc (work/ docs/)"] += 1
    else: kinds[f"other: {w.split('/')[0]}/"] += 1
print(f"{len(out)} contests the ON arm broke\n")
for k,v in kinds.most_common(): print(f"  {v:>3}  {k}")
print("\nexamples:")
for r in out[:8]:
    print(f"  {r['query'][:52]!r:<56} -> {r['won_on']}   (truth {r['target']})")
json.dump(out, open("/private/tmp/claude-501/-Users-arpitarya-my-programs-fux/bfdf0f61-9b1d-4f48-97d7-5a4381f3dc8b/scratchpad/whowon.json","w"), indent=2)
