import json, subprocess, sys
from pathlib import Path
PG = Path.home()/"my_programs"/"fux-playground"; PY_ = PG/".venv"/"bin"/"python"
rows=[]
for line in Path(sys.argv[1]).read_text().splitlines():
    if not line.strip(): continue
    d=json.loads(line)
    p=subprocess.run([str(PY_),"-m","fux.cli","ask",d["q"],"--json","--top","3","--band"],
                     cwd=PG,capture_output=True,text=True)
    out=json.loads(p.stdout); c=out.get("confidence") or {}
    rows.append((d["id"], c.get("band"), c.get("answerable"), round(c.get("separation") or 0,3),
                 [r["loc"].split("/")[-1] for r in out["results"][:2]]))
print(f"{'id':<5}{'band':<12}{'answerable':<12}{'sep':>7}  top-2")
for r in rows: print(f"{r[0]:<5}{str(r[1]):<12}{str(r[2]):<12}{r[3]:>7}  {r[4]}")
from collections import Counter
print("\nbands:", dict(Counter(r[1] for r in rows)))
print("answerable=False:", sum(1 for r in rows if r[2] is False), "/", len(rows))
