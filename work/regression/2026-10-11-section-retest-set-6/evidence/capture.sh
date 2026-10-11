#!/usr/bin/env bash
# W-270 DoD 5 — the capture, as PRE-REGISTRATION.md §Procedure steps 2–7 fix it.
# Not frozen (it is a driver, not a rule); every step it runs is named there.
#
#   bash capture.sh <engine fux (b4d961cd)> <pre-section fux (dca6aaa4)>
#
# Reads `id` and `question` from work/golden/questions/set-6-claude.jsonl through
# golden_run.py, g3.py and latency.py; opens nothing else under work/golden/.
# Opens no key, runs no scorer. Never writes to a ladder rung: every arm is a copy.
set -euo pipefail
FUX=$1
PRE=$2
REPO=$(cd "$(dirname "$0")/../../../.." && pwd)
EV=$REPO/work/regression/2026-10-11-section-retest-set-6/evidence
LAB=$HOME/my_programs/fux-lab
RUNG=$LAB/corpora/golden/rung-01000
BIG=$LAB/corpora/golden/rung-10000
RUNS=$LAB/arms/runs
Q=$REPO/work/golden/questions/set-6-claude.jsonl
cd "$REPO"

for d in s6-base s6 s6-pre s6-g1 s6-lat; do
  [ -e "$RUNS/$d" ] && { echo "refusing: $RUNS/$d exists"; exit 1; }
done
uptime

# 2 · the base: copy, doctor --fix (recorded), ingest --full
mkdir -p "$RUNS/s6-base"
cp -a "$RUNG" "$RUNS/s6-base/"
cp -a "$RUNS/s6-base/rung-01000/.fux" "$EV/.fux-before-doctor"
(cd "$RUNS/s6-base/rung-01000" && "$FUX" doctor --fix > /dev/null 2>&1 || true)
diff -r "$EV/.fux-before-doctor" "$RUNS/s6-base/rung-01000/.fux" -x index -x runtime > "$EV/doctor-fix.diff" || true
rm -rf "$EV/.fux-before-doctor"
(cd "$RUNS/s6-base/rung-01000" && "$FUX" ingest --full --no-progress)

# 3 · the arms: copies of the base, one line changed
mkdir -p "$RUNS/s6"
for L in 0.0 2.0 4.0; do
  mkdir -p "$RUNS/s6/sw-$L"
  cp -a "$RUNS/s6-base/rung-01000" "$RUNS/s6/sw-$L/"
  sed -i '' "s/^section_weight          = .*/section_weight          = $L/" "$RUNS/s6/sw-$L/rung-01000/.fux/tune.toml"
  grep -c "^section_weight          = $L\$" "$RUNS/s6/sw-$L/rung-01000/.fux/tune.toml"
  diff -r "$RUNS/s6-base/rung-01000" "$RUNS/s6/sw-$L/rung-01000" -x runtime > "$EV/arm-diff-sw-$L.txt" || true
done

# 4 · G0's before-copy: the pre-section engine, its closed key set refuses
#     `section_weight`, so the key and its comment go (recorded), then --full
mkdir -p "$RUNS/s6-pre"
cp -a "$RUNG" "$RUNS/s6-pre/"
T=$RUNS/s6-pre/rung-01000/.fux/tune.toml
cp "$T" "$EV/.tune-before"
python3 - "$T" <<'PY'
import re, sys
p = sys.argv[1]; s = open(p).read()
s = re.sub(r"# Rank a long document by its best section too:.*?\nsection_weight\s*=.*?\n", "", s, flags=re.S)
open(p, "w").write(s)
PY
diff "$EV/.tune-before" "$T" > "$EV/pre-section-tune.diff" || true
rm -f "$EV/.tune-before"
(cd "$RUNS/s6-pre/rung-01000" && "$PRE" ingest --full --no-progress)

# 5 · capture: three arms on the pinned engine, one on the pre-section engine
for L in 0.0 2.0 4.0; do
  python3 tools/quality-controls/golden_run.py --rung rung-01000 --tree "$RUNS/s6/sw-$L/rung-01000" \
    --evidence "$EV/sw-$L/rung-01000" --sets 6-claude --arm "sw-$L" --engine-commit b4d961cd --fux "$FUX"
done
python3 tools/quality-controls/golden_run.py --rung rung-01000 --tree "$RUNS/s6-pre/rung-01000" \
  --evidence "$EV/pre-section/rung-01000" --sets 6-claude --arm pre-section --engine-commit dca6aaa4 --fux "$PRE"

# 6 · gates
mkdir -p "$EV/g0" "$EV/g3" "$EV/latency"
python3 "$EV/g0.py" "$EV/pre-section/rung-01000" "$EV/sw-0.0/rung-01000" > "$EV/g0/g0.json"
python3 "$EV/g3.py" --fux "$FUX" --arms "$RUNS/s6" --questions "$Q" > "$EV/g3/g3.json"
mkdir -p "$RUNS/s6-g1"
cp -a "$BIG" "$RUNS/s6-g1/"
(cd "$RUNS/s6-g1/rung-10000" && "$FUX" doctor --fix > /dev/null 2>&1 || true; "$FUX" ingest --full --no-progress)
python3 work/regression/2026-10-10-section-records/evidence/g1.py "$RUNS/s6-g1/rung-10000" > "$EV/g1.json"

# 7 · latency, standalone, last: two copies of the G1 copy, one line changed
for L in 0.0 2.0; do
  mkdir -p "$RUNS/s6-lat/sw-$L"
  cp -a "$RUNS/s6-g1/rung-10000" "$RUNS/s6-lat/sw-$L/"
  sed -i '' "s/^section_weight          = .*/section_weight          = $L/" "$RUNS/s6-lat/sw-$L/rung-10000/.fux/tune.toml"
  (cd "$RUNS/s6-lat/sw-$L/rung-10000" && "$FUX" build > /dev/null 2>&1 || true)
done
uptime
python3 "$EV/latency.py" --fux "$FUX" --arms "$RUNS/s6-lat" --questions "$Q" > "$EV/latency/latency.json"
cat "$EV/g0/g0.json" "$EV/g1.json" "$EV/g3/g3.json" "$EV/latency/latency.json" | grep '"verdict"'
echo CAPTURE-DONE
