#!/bin/sh
# Reproduces every number in ../report.md. Offline, no lab, ~2 minutes.
#
#   ./profile.sh /tmp/fux-cost <fux-repo-root>
#
# Builds synthetic corpora, profiles a full ingest, then times full vs delta.
set -eu
WORK="${1:-/tmp/fux-cost}"
REPO="${2:-$(cd "$(dirname "$0")/../../../.." && pwd)}"
PY="$REPO/.venv/bin/python"
FUX="$REPO/.venv/bin/fux"

for N in 1000 5000; do
  DIR="$WORK/corpus-$N"
  rm -rf "$DIR"; mkdir -p "$DIR/docs"; cd "$DIR"; git init -q
  "$PY" - "$N" <<'PY'
import sys
from pathlib import Path
n = int(sys.argv[1])
def doc(i, r=0):
    body = " ".join(f"term{i}{j}{r}" for j in range(40))
    return (f"---\ntitle: Document {i}\ntype: runbook\n---\n\n# Document {i}\n\n"
            f"Revision {r}. {body}\n\nSee [document {(i+1)%97}](doc-{(i+1)%97}.md).\n")
for i in range(n):
    Path(f"docs/doc-{i}.md").write_text(doc(i))
PY
  "$FUX" setup >/dev/null
  "$FUX" ingest >/dev/null
  echo "== corpus $N: cProfile of a FULL ingest =="
  "$PY" -c "
import cProfile,pstats,sys,io
sys.path.insert(0,'$REPO/src')
from pathlib import Path
from fux.ingest.run import run
pr=cProfile.Profile(); pr.enable(); run(Path('.'), full=True); pr.disable()
s=io.StringIO(); pstats.Stats(pr,stream=s).sort_stats('cumulative').print_stats(12); print(s.getvalue())
"
  echo "== corpus $N: full vs delta, and byte-identity =="
  "$PY" -c "
import sys,time,hashlib
sys.path.insert(0,'$REPO/src')
from pathlib import Path
from fux.ingest.run import run
from fux.store import iter_shard_paths
d=lambda: {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in iter_shard_paths(Path('.'))}
t=time.perf_counter(); run(Path('.'), full=True); full=time.perf_counter()-t; a=d()
t=time.perf_counter(); r=run(Path('.')); delta=time.perf_counter()-t; b=d()
print(f'full {full:.3f}s  delta {delta:.3f}s  speedup {full/delta:.1f}x  reused {r.reused_count}')
print('byte-identical:', a==b)
"
done
