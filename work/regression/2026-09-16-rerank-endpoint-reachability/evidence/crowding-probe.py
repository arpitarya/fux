"""Can the `answer` path be de-contaminated by post-filtering? Measure, do not assume."""
import json, subprocess, sys, random
from pathlib import Path
ROOT = Path("/Users/arpitarya/my_programs/fux")

def run(*a):
    o = subprocess.run([sys.executable, "-m", "fux.cli", *a], cwd=ROOT, capture_output=True, text=True)
    try: return json.loads(o.stdout)
    except Exception: return None

rows = [json.loads(l) for l in (ROOT/"work/regression/2026-09-15-rerank-quality/evidence/contests-screened.jsonl").read_text().splitlines() if l.strip()]
random.seed(19)
sample = random.sample(rows, 30)

from collections import Counter
tally = Counter()
npass = []
for c in sample:
    p = run("answer", c["query"], "--json")
    ps = ((p or {}).get("answer") or {}).get("passages") or []
    npass.append(len(ps))
    docs = {(x.get("loc") or "").split(":")[0] for x in ps}
    tally["runs"] += 1
    if not ps: tally["empty"] += 1
    if c["source"] in docs: tally["source_present"] += 1
    if docs and docs <= {c["source"]}: tally["source_ONLY"] += 1
    if c["target"] in docs: tally["target_present"] += 1
print(f"n = {tally['runs']}   passages per answer: min {min(npass)} max {max(npass)} mean {sum(npass)/len(npass):.1f}")
for k in ("empty", "source_present", "source_ONLY", "target_present"):
    print(f"  {k:<16} {tally[k]:>3}/{tally['runs']}")
