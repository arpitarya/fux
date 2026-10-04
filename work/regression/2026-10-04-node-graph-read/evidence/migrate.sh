#!/bin/bash
# W-259: throwaway copies of the fux-lab v7 rungs, migrated to this engine.
# Reads ~/my_programs/fux-lab only via cp -R; every write lands in the scratchpad.
# S was the session scratchpad on 2026-10-04; any empty directory serves.
set -euo pipefail
S=${S:?set S to a scratch directory}
PY=${PY:-$(git -C "$(dirname "$0")" rev-parse --show-toplevel)/.venv/bin/python}
for r in rung-01000 rung-10000; do
  src=~/my_programs/fux-lab/scratch/shared-runtime/$r-v7
  dst=$S/$r
  rm -rf "$dst"
  cp -R "$src" "$dst"
  cd "$dst"
  echo "== $r doctor --fix"; FUX_NO_SPAWN=1 $PY -m fux doctor --fix > $S/$r.doctor.log 2>&1 || true
  echo "== $r ingest --full"; ( time FUX_NO_SPAWN=1 $PY -m fux ingest --full ) > $S/$r.ingest.log 2>&1
  echo "== $r build"; ( time FUX_NO_SPAWN=1 $PY -m fux build ) > $S/$r.build.log 2>&1
  $PY -c "from pathlib import Path; from fux.derive import accel; print('$r fresh:', accel.is_fresh(Path('.')))"
done
