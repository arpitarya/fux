#!/usr/bin/env bash
# W-204 phase B — v1.0.0 and v2.0.1 on all eight rungs, three sets, both verbs.
# HEAD's rows are phase A's and are NOT re-run.
set -euo pipefail
REPO=/Users/arpitarya/my_programs/fux
LAB=$HOME/my_programs/fux-lab
EV=$REPO/work/regression/2026-09-21-golden-three-engines/evidence
RUNGS="rung-seed rung-00100 rung-00200 rung-00500 rung-01000 rung-02000 rung-05000 rung-10000"
cd "$REPO"
for arm in v1 v2; do
  FUX=$LAB/arms/$arm/bin/fux
  BAND=""; VER="2.0.1"
  if [ "$arm" = v1 ]; then BAND="--no-band"; VER="1.0.0"; fi
  for rung in $RUNGS; do
    echo "=== $arm / $rung — build ==="
    .venv/bin/python tools/quality-controls/arm_corpus.py \
      --rung "$rung" --arm "$arm" --fux "$FUX" | tail -4
    echo "=== $arm / $rung — run ==="
    .venv/bin/python tools/quality-controls/golden_run.py \
      --rung "$rung" --sets 1,2,3 --fux "$FUX" $BAND --arm "$arm" \
      --tree "$LAB/arms/runs/$arm/$rung" \
      --evidence "$EV/$arm/$rung" --engine-commit "fux-engine==$VER" | tail -2
  done
done
echo "PHASE B ARMS DONE"
