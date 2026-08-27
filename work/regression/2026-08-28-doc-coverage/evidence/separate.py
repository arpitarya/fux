"""Do `doc_coverage` values separate real goldens from decoys?

Run from the fux-playground checkout, with the decoy set path as argv[1].
No threshold is applied here — it prints the two distributions and lets a
reader see whether a cut exists.
"""
import json, statistics, subprocess, sys

PY_ = ".venv/bin/python"


def probe(q):
    p = subprocess.run([PY_, "-m", "fux.cli", "ask", q, "--json", "--top", "5", "--band"],
                       capture_output=True, text=True)
    return json.loads(p.stdout).get("confidence") or {}


rows = []
for kind, path in (("golden", "goldens/queries.jsonl"), ("decoy", sys.argv[1])):
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        g = json.loads(line)
        c = probe(g["q"])
        rows.append((kind, g["id"], c.get("band"), c.get("doc_coverage"), bool(c.get("missing"))))

# Only rows that REACH the clause: anything with a missing term is already
# `partial` and never gets as far as a doc_coverage test.
for kind in ("golden", "decoy"):
    v = [r[3] for r in rows if r[0] == kind and r[3] is not None and not r[4]]
    if v:
        print(f"{kind:8} n={len(v):3}  min={min(v):.3f}  median={statistics.median(v):.3f}  max={max(v):.3f}")
    else:
        print(f"{kind:8} n=  0  (none reach the clause)")
