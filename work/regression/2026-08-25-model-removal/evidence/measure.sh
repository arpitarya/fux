#!/usr/bin/env bash
# The harness, verbatim. Two worktrees, one variable.
set -euo pipefail
BASE=/tmp/fuxbase      # git worktree add --detach <HEAD-with-model>
NEW=/tmp/fuxwork       # the tree with the model removed

for T in "$BASE" "$NEW"; do
  cd "$T"
  s=$(date +%s.%N); uv run --project "$T" fux ingest --full >/dev/null 2>&1; e=$(date +%s.%N)
  echo "$T ingest: $(echo "$e - $s" | bc) s"
  python3 -c "
import glob,os,json
tot=sum(os.path.getsize(f) for f in glob.glob('.fux/index/*.jsonl'))
n=v=0
for f in glob.glob('.fux/index/*.jsonl'):
    for line in open(f):
        if line.strip():
            r=json.loads(line); n+=1; v+=len(r.get('vectors') or [])
print(f'  index {tot:,} B, {n} records, {v} chunk vectors')"
  uv build --wheel -o "/tmp/wh_$(basename $T)" >/dev/null 2>&1
  ls -l "/tmp/wh_$(basename $T)"/*.whl | awk '{print "  wheel", $5, "B"}'
done

# The differential law -- note the NON-EMPTY assertion. Without it two failing
# invocations both return "" and the check passes while proving nothing.
cd "$NEW"
for q in "differential law" "index format canonical" "how does enrichment work" \
         "supersession ranking" "merge driver conflict" "bm25f field weights"; do
  b=$(uv run fux ask "$q" --json --top 5 --scan)
  c=$(uv run fux ask "$q" --json --top 5 --fast)
  n=$(printf '%s' "$b" | python3 -c "import sys,json;print(len(json.load(sys.stdin).get('results',[])))")
  [ "$n" -ge 1 ] || { echo "EMPTY (vacuous!) $q"; exit 1; }
  [ "$b" = "$c" ] && echo "IDENTICAL n=$n   $q" || { echo "DIVERGED $q"; exit 1; }
done
