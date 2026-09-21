#!/usr/bin/env bash
set -euo pipefail
REPO=/Users/arpitarya/my_programs/fux
BEFORE=/private/tmp/claude-501/-Users-arpitarya-my-programs-fux/534a962e-d81a-4d48-839b-be0a32b7086b/scratchpad/p1before/.venv/bin/fux
AFTER=$REPO/.venv/bin/fux
EV=$REPO/work/regression/2026-09-21-frontmatter-reachable/evidence
LAB=$HOME/my_programs/fux-lab
cd "$REPO"
for rung in rung-00100 rung-01000; do
  for arm in before after; do
    fux=$BEFORE; [ "$arm" = after ] && fux=$AFTER
    echo "=== build $arm / $rung ==="
    .venv/bin/python tools/quality-controls/arm_corpus.py --rung "$rung" --arm "p1-$arm" --fux "$fux" | tail -3
    echo "=== ENDPOINT $arm / $rung ==="
    .venv/bin/python "$EV/reach.py" --tree "$LAB/arms/runs/p1-$arm/$rung" --fux "$fux" --out "$EV/reach-$arm-$rung.json"
  done
done
echo "=== NO-HARM 1: the 43 id-queries on rung-01000 ==="
for arm in before after; do
  fux=$BEFORE; [ "$arm" = after ] && fux=$AFTER
  .venv/bin/python tools/quality-controls/identifier_probe.py \
    --queries "$REPO/work/regression/2026-09-21-identifier-analyzer/evidence/id-queries.jsonl" \
    --rung rung-01000 --tree "$LAB/arms/runs/p1-$arm/rung-01000" --fux "$fux" \
    --out "$EV/idq-$arm.json" | tail -2
done
echo "=== NO-HARM 2: 60 set-1 questions on rung-01000 ==="
for arm in before after; do
  fux=$BEFORE; [ "$arm" = after ] && fux=$AFTER
  .venv/bin/python "$REPO/work/regression/2026-09-21-identifier-analyzer/evidence/control_60.py" \
    --tree "$LAB/arms/runs/p1-$arm/rung-01000" --fux "$fux" --out "$EV/control-$arm.json"
done
echo "PART 1 ARMS DONE"
