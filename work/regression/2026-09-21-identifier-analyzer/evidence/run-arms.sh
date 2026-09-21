#!/usr/bin/env bash
# W-205 part 2 — build both arms, probe, control, compare.
set -euo pipefail
REPO=/Users/arpitarya/my_programs/fux
WT=/private/tmp/claude-501/-Users-arpitarya-my-programs-fux/534a962e-d81a-4d48-839b-be0a32b7086b/scratchpad/w205
RUN=$REPO/work/regression/2026-09-21-identifier-analyzer
EV=$RUN/evidence
BEFORE_FUX=$REPO/.venv/bin/fux
AFTER_FUX=$WT/.venv/bin/fux
cd "$REPO"

for rung in rung-00100 rung-01000 rung-10000; do
  for arm in before after; do
    fux=$BEFORE_FUX; [ "$arm" = after ] && fux=$AFTER_FUX
    echo "=== build $arm / $rung ==="
    .venv/bin/python tools/quality-controls/arm_corpus.py \
      --rung "$rung" --arm "w205-$arm" --fux "$fux"
  done
done

for rung in rung-00100 rung-01000 rung-10000; do
  for arm in before after; do
    fux=$BEFORE_FUX; [ "$arm" = after ] && fux=$AFTER_FUX
    echo "=== probe $arm / $rung ==="
    .venv/bin/python tools/quality-controls/identifier_probe.py \
      --queries "$EV/id-queries.jsonl" --rung "$rung" \
      --tree "$HOME/my_programs/fux-lab/arms/runs/w205-$arm/$rung" \
      --fux "$fux" --out "$EV/$arm-$rung.json" | tail -9
  done
done

echo "=== control: 60 set-1 questions on rung-01000, both arms ==="
for arm in before after; do
  fux=$BEFORE_FUX; [ "$arm" = after ] && fux=$AFTER_FUX
  .venv/bin/python "$EV/control_60.py" \
    --tree "$HOME/my_programs/fux-lab/arms/runs/w205-$arm/rung-01000" \
    --fux "$fux" --out "$EV/control-$arm.json"
done

for rung in rung-00100 rung-01000 rung-10000; do
  .venv/bin/python "$EV/compare_arms.py" --rung "$rung" \
    --before "$EV/before-$rung.json" --after "$EV/after-$rung.json" \
    --out "$EV/compare-$rung.json"
done
echo "PART 2 ARMS DONE"
