#!/usr/bin/env bash
# W-278 DoD 5 — the capture, as PRE-REGISTRATION.md §Procedure steps 2–7 fix it.
# Not frozen (it is a driver, not a rule); every step it runs is named there.
#
#   bash capture.sh <engine fux> <engine python> <engine commit> <pre-section fux (dca6aaa4)>
#
# Reads `id` and `question` from work/golden/questions/set-7-claude.jsonl through
# golden_run.py, g3.py, g4.py and latency.py; opens nothing else under
# work/golden/. Prints no question. Opens no key, runs no scorer. Never writes
# to a ladder rung: every arm is a copy.
set -euo pipefail
FUX=$1
PY=$2
COMMIT=$3
PRE=$4
REPO=$(cd "$(dirname "$0")/../../../.." && pwd)
EV=$REPO/work/regression/2026-10-13-section-term-v3/evidence
LAB=$HOME/my_programs/fux-lab
RUNG=$LAB/corpora/golden/rung-01000
BIG=$LAB/corpora/golden/rung-10000
RUNS=$LAB/arms/runs
Q=$REPO/work/golden/questions/set-7-claude.jsonl
cd "$REPO"

for d in s7-base s7 s7-pre s7-g1 s7-lat; do
  [ -e "$RUNS/$d" ] && { echo "refusing: $RUNS/$d exists"; exit 1; }
done
uptime

on() {  # the plane on: fux.toml [index] section_records = true
  sed -i '' 's/^section_records *= *false/section_records = true/' "$1/fux.toml"
  grep -q '^section_records = true$' "$1/fux.toml" || { echo "refusing: no section_records key in $1/fux.toml"; exit 1; }
}

# 2 · the base: copy, doctor --fix (recorded), the plane on, ingest --full
mkdir -p "$RUNS/s7-base"
cp -a "$RUNG" "$RUNS/s7-base/"
B=$RUNS/s7-base/rung-01000
cp -a "$B/.fux" "$EV/.fux-before-doctor"; cp "$B/fux.toml" "$EV/.fux-toml-before"
(cd "$B" && "$FUX" doctor --fix > /dev/null 2>&1 || true)
on "$B"
{ diff -r "$EV/.fux-before-doctor" "$B/.fux" -x index -x runtime; diff "$EV/.fux-toml-before" "$B/fux.toml"; } > "$EV/doctor-fix.diff" || true
rm -rf "$EV/.fux-before-doctor" "$EV/.fux-toml-before"
(cd "$B" && "$FUX" ingest --full --no-progress)

# 3 · the arms: copies of the base, one line changed
mkdir -p "$RUNS/s7"
for L in 0.0 0.5 1.0; do
  mkdir -p "$RUNS/s7/sw-$L"
  cp -a "$B" "$RUNS/s7/sw-$L/"
  sed -i '' "s/^section_weight          = .*/section_weight          = $L/" "$RUNS/s7/sw-$L/rung-01000/.fux/tune.toml"
  grep -c "^section_weight          = $L\$" "$RUNS/s7/sw-$L/rung-01000/.fux/tune.toml"
  diff -r "$B" "$RUNS/s7/sw-$L/rung-01000" -x runtime > "$EV/arm-diff-sw-$L.txt" || true
done

# 4 · G0's before-copy: the pre-section engine; its closed key set refuses
#     `section_weight` and `section_records`, so both go (recorded), then --full
mkdir -p "$RUNS/s7-pre"
cp -a "$RUNG" "$RUNS/s7-pre/"
P=$RUNS/s7-pre/rung-01000
cp "$P/.fux/tune.toml" "$EV/.tune-before"; cp "$P/fux.toml" "$EV/.fuxtoml-before"
python3 - "$P/.fux/tune.toml" "$P/fux.toml" <<'PYEOF'
import re, sys
t, f = sys.argv[1], sys.argv[2]
s = open(t).read()
s = re.sub(r"# Rank a long document by its best section too:.*?\nsection_weight\s*=.*?\n", "", s, flags=re.S)
open(t, "w").write(s)
s = open(f).read()
s = re.sub(r"(?m)^(#[^\n]*\n)*section_records\s*=.*\n", "", s)
open(f, "w").write(s)
PYEOF
{ diff "$EV/.tune-before" "$P/.fux/tune.toml"; diff "$EV/.fuxtoml-before" "$P/fux.toml"; } > "$EV/pre-section-config.diff" || true
rm -f "$EV/.tune-before" "$EV/.fuxtoml-before"
(cd "$P" && "$PRE" ingest --full --no-progress)

# 5 · capture: three arms on the pinned engine, one on the pre-section engine
for L in 0.0 0.5 1.0; do
  python3 tools/quality-controls/golden_run.py --rung rung-01000 --tree "$RUNS/s7/sw-$L/rung-01000" \
    --evidence "$EV/sw-$L/rung-01000" --sets 7-claude --arm "sw-$L" --engine-commit "$COMMIT" --fux "$FUX"
done
python3 tools/quality-controls/golden_run.py --rung rung-01000 --tree "$P" \
  --evidence "$EV/pre-section/rung-01000" --sets 7-claude --arm pre-section --engine-commit dca6aaa4 --fux "$PRE"

# 6 · gates, and G5 (descriptive)
mkdir -p "$EV/g0" "$EV/g3" "$EV/g4" "$EV/g5" "$EV/latency"
python3 "$EV/g0.py" "$EV/pre-section/rung-01000" "$EV/sw-0.0/rung-01000" > "$EV/g0/g0.json"
python3 "$EV/g3.py" --fux "$FUX" --arms "$RUNS/s7" --questions "$Q" > "$EV/g3/g3.json"
"$PY" "$EV/g4.py" --tree "$RUNS/s7/sw-1.0/rung-01000" --questions "$Q" > "$EV/g4/g4.json"
python3 "$EV/g5.py" --tree "$B" --evidence "$EV" > "$EV/g5/g5.json"
mkdir -p "$RUNS/s7-g1"
cp -a "$BIG" "$RUNS/s7-g1/"
G=$RUNS/s7-g1/rung-10000
(cd "$G" && "$FUX" doctor --fix > /dev/null 2>&1 || true)
on "$G"
(cd "$G" && "$FUX" ingest --full --no-progress)
python3 work/regression/2026-10-10-section-records/evidence/g1.py "$G" > "$EV/g1.json"

# 7 · latency, standalone, last: two copies of the G1 copy, one line changed
for L in 0.0 1.0; do
  mkdir -p "$RUNS/s7-lat/sw-$L"
  cp -a "$G" "$RUNS/s7-lat/sw-$L/"
  sed -i '' "s/^section_weight          = .*/section_weight          = $L/" "$RUNS/s7-lat/sw-$L/rung-10000/.fux/tune.toml"
  (cd "$RUNS/s7-lat/sw-$L/rung-10000" && "$FUX" build > /dev/null 2>&1 || true)
done
uptime
python3 "$EV/latency.py" --fux "$FUX" --arms "$RUNS/s7-lat" --questions "$Q" > "$EV/latency/latency.json"
cat "$EV/g0/g0.json" "$EV/g1.json" "$EV/g3/g3.json" "$EV/g4/g4.json" "$EV/latency/latency.json" | grep '"verdict"'
echo CAPTURE-DONE
