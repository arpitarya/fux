#!/usr/bin/env bash
# W-233 — build both arms on three rungs, gates G2/G3, ranks, costs.
# The before arm is the commit that froze the pre-registration (cca32152),
# run from a worktree through the same interpreter via PYTHONPATH.
set -euo pipefail
REPO=/Users/arpitarya/my_programs/fux
S=/private/tmp/claude-501/-Users-arpitarya-my-programs-fux/f2e0d102-f3ac-4d83-9e32-7b6c5deca5c3/scratchpad
WT=$S/w233-before
EV=$REPO/work/regression/2026-09-28-identifier-families/evidence
RUNS=$HOME/my_programs/fux-lab/arms/runs
PY=$REPO/.venv/bin/python
[ -d "$WT" ] || git -C "$REPO" worktree add -q --detach "$WT" cca32152
cat > "$S/before-fux" <<W
#!/bin/sh
PYTHONPATH=$WT/src exec $PY -m fux.cli "\$@"
W
chmod +x "$S/before-fux"
BEFORE=$S/before-fux
AFTER=$REPO/.venv/bin/fux
# One commit stamp for every copy, so two arms' `mtime` agree and G3 compares bytes.
export GIT_AUTHOR_DATE="2026-09-28T00:00:00+0000" GIT_COMMITTER_DATE="2026-09-28T00:00:00+0000"
cd "$REPO"
for rung in rung-00100 rung-01000 rung-10000; do
  echo "=== $rung: before ==="
  $PY tools/quality-controls/arm_corpus.py --rung $rung --arm w233-before --fux "$BEFORE" | tail -3
  echo "=== $rung: after (file empty = the inert state) ==="
  $PY tools/quality-controls/arm_corpus.py --rung $rung --arm w233-after --fux "$AFTER" | tail -3
  if [ $rung = rung-01000 ]; then
    if diff -rq "$RUNS/w233-before/$rung/.fux/index" "$RUNS/w233-after/$rung/.fux/index" >/dev/null; then
      echo "G3 PASS: empty identifiers.toml -> byte-identical .fux/index on $rung" | tee "$EV/g3-$rung.txt"
    else
      echo "G3 FAIL" | tee "$EV/g3-$rung.txt"; diff -rq "$RUNS/w233-before/$rung/.fux/index" "$RUNS/w233-after/$rung/.fux/index" | head -5 | tee -a "$EV/g3-$rung.txt"
    fi
  fi
  for arm in w233-after w233-after2; do
    if [ $arm = w233-after2 ]; then
      $PY tools/quality-controls/arm_corpus.py --rung $rung --arm $arm --fux "$AFTER" | tail -1
    fi
    ( cd "$RUNS/$arm/$rung" && "$AFTER" identifiers --write --json > "$S/written-$arm-$rung.json" && "$AFTER" ingest --no-progress | tail -1 )
  done
  cp "$S/written-w233-after-$rung.json" "$EV/written-$rung.json"
  cp "$RUNS/w233-after/$rung/.fux/identifiers.toml" "$EV/identifiers-$rung.toml"
  if diff -rq "$RUNS/w233-after/$rung/.fux/index" "$RUNS/w233-after2/$rung/.fux/index" >/dev/null; then
    echo "G2 PASS: two from-scratch after-arm builds byte-identical on $rung" | tee "$EV/g2-$rung.txt"
  else
    echo "G2 FAIL on $rung" | tee "$EV/g2-$rung.txt"
  fi
  echo "=== $rung: ranks ==="
  PYTHONPATH=$WT/src $PY "$EV/rank_variants.py" "$EV/variants-$rung.jsonl" "$RUNS/w233-before/$rung" "$EV/before-$rung.jsonl"
  $PY "$EV/rank_variants.py" "$EV/variants-$rung.jsonl" "$RUNS/w233-after/$rung" "$EV/after-$rung.jsonl"
  du -sk "$RUNS/w233-before/$rung/.fux/index" "$RUNS/w233-after/$rung/.fux/index" | tee "$EV/bytes-$rung.txt"
done
echo DONE
