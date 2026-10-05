#!/bin/sh
# W-264 DoD 1: interleaved delta ingests, shipped (HEAD a9090e1f) vs memoised _compile (worktree).
# Same rung copy, same venv, fresh process each; A B B A per pair-of-pairs.
W=/Users/arpitarya/my_programs/fux/.claude/worktrees/agent-a784bf5bbd26d64bb
D=/private/tmp/claude-501/-Users-arpitarya-my-programs-fux/02683e45-83d7-4582-a731-ac5270c49b6a/scratchpad/w264
row() {
  "$W/.venv/bin/python" -c "import json,sys,os; r=json.loads(sys.stdin.read().splitlines()[-1]); s={x['name']:x['s'] for x in r['segments']}; print(json.dumps({'id':'$1-$2','arm':'$1','repeat':$2,'total_s':r['total_s'],'redact_s':s.get('redact'),'non_extract_s':r['non_extract_s'],'reused':r['reused'],'changed':r['changed'],'index_sha256':r['index_sha256'],'loadavg':r['loadavg']}))"
}
for i in 1 2 3 4; do
  if [ $((i % 2)) -eq 1 ]; then order="shipped memoised"; else order="memoised shipped"; fi
  for arm in $order; do
    if [ "$arm" = shipped ]; then T="$D/shipped/tools/quality-controls/ingest_split.py"; else T="$W/tools/quality-controls/ingest_split.py"; fi
    "$W/.venv/bin/python" "$T" one "$D/gen3" --delta | row "$arm" "$i" | tee -a "$D/abab.jsonl"
  done
done
