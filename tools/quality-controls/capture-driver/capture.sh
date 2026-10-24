#!/usr/bin/env bash
# TEMPLATE capture driver (W-281) — copy this directory into the next run's
# `evidence/`, set the five RUN-SPECIFIC lines below, and adapt steps 4-5 to the
# run's arms. Based on W-278's capture (2026-10-13-section-term-v3/evidence/
# capture.sh), whose step order it keeps. NOT frozen (a driver, not a rule);
# every step it runs must be named in the run's PRE-REGISTRATION §Procedure.
#
#   bash capture.sh <engine fux> <engine python> <engine commit> <pre-section fux>
#
# What W-281 changes against W-278's serial driver — schedule only:
#   DoD 2  G1's rung-10000 copy + `ingest --full` + g1.py start in the BACKGROUND
#          at the top and are joined before latency.
#   DoD 3  one frozen g3.py process per treatment arm, side by side
#          (g3_one_arm.py imports the frozen file UNCHANGED; its hash is intact).
#   DoD 4  latency runs LAST and ALONE: every background job joined, `uptime`
#          recorded, nothing else of ours running (L13 d3, SR-WORK-SESSION d12).
#   DoD 5  every step's wall time is appended to $EV/capture-timing.tsv.
# Never edit g0.py g3.py g4.py latency.py decide.py: they are hashed in the
# pre-registration. Reads `id` and `question` through the released question
# file only; opens nothing else under work/golden/.
set -euo pipefail
FUX=$1
PY=$2
COMMIT=$3
PRE=$4
HERE=$(cd "$(dirname "$0")" && pwd)

# ---- RUN-SPECIFIC (edit these five) -------------------------------------
RUNDIR=${RUNDIR:?set RUNDIR=work/regression/<date>-<slug>}   # the run's folder
SET=${SET:-set-7-claude}                                      # released question file stem
SETID=${SETID:-7-claude}                                      # golden_run.py --sets value
PFX=${PFX:-s7}                                                # scratch-dir prefix under arms/runs
TREATMENTS=${TREATMENTS:-"sw-1.0 sw-0.5"}                     # g3's frozen treatments (baseline sw-0.0 is implicit)
# ---------------------------------------------------------------------------

REPO=$(cd "$HERE/../../../.." && pwd)
EV=$REPO/$RUNDIR/evidence
LAB=$HOME/my_programs/fux-lab
RUNG=$LAB/corpora/golden/rung-01000
BIG=$LAB/corpora/golden/rung-10000
RUNS=$LAB/arms/runs
Q=$REPO/work/golden/questions/$SET.jsonl
TIMING=$EV/capture-timing.tsv
cd "$REPO"

for d in $PFX-base $PFX $PFX-pre $PFX-g1 $PFX-lat; do
  [ -e "$RUNS/$d" ] && { echo "refusing: $RUNS/$d exists"; exit 1; }
done
mkdir -p "$EV"
: > "$TIMING"
uptime

# step NAME CMD...  — run CMD (a shell function or command), log wall seconds.
step() {
  local name=$1 t0; shift
  t0=$(date +%s)
  "$@"
  printf '%s\t%s\t%s\t%s\n' "$name" "$t0" "$(date +%s)" "$(( $(date +%s) - t0 ))" >> "$TIMING"
}

on() {  # the plane on: fux.toml [index] section_records = true
  sed -i '' 's/^section_records *= *false/section_records = true/' "$1/fux.toml"
  grep -q '^section_records = true$' "$1/fux.toml" || { echo "refusing: no section_records key in $1/fux.toml"; exit 1; }
}

# ---- DoD 2 · G1 in the background from the very top ----------------------
g1_job() {
  mkdir -p "$RUNS/$PFX-g1"
  cp -a "$BIG" "$RUNS/$PFX-g1/"
  local G=$RUNS/$PFX-g1/rung-10000
  (cd "$G" && "$FUX" doctor --fix > /dev/null 2>&1 || true)
  on "$G"
  (cd "$G" && "$FUX" ingest --full --no-progress)
  python3 work/regression/2026-10-10-section-records/evidence/g1.py "$G" > "$EV/g1.json"
}
step g1_bg_total g1_job > "$EV/g1-bg.log" 2>&1 &
G1_PID=$!
G=$RUNS/$PFX-g1/rung-10000

# 2 · the base: copy, doctor --fix (recorded), the plane on, ingest --full
base_job() {
  mkdir -p "$RUNS/$PFX-base"
  cp -a "$RUNG" "$RUNS/$PFX-base/"
  local B=$RUNS/$PFX-base/rung-01000
  cp -a "$B/.fux" "$EV/.fux-before-doctor"; cp "$B/fux.toml" "$EV/.fux-toml-before"
  (cd "$B" && "$FUX" doctor --fix > /dev/null 2>&1 || true)
  on "$B"
  { diff -r "$EV/.fux-before-doctor" "$B/.fux" -x index -x runtime; diff "$EV/.fux-toml-before" "$B/fux.toml"; } > "$EV/doctor-fix.diff" || true
  rm -rf "$EV/.fux-before-doctor" "$EV/.fux-toml-before"
  (cd "$B" && "$FUX" ingest --full --no-progress)
}
step base_ingest base_job
B=$RUNS/$PFX-base/rung-01000

# 3 · the arms: copies of the base, one line changed
arms_job() {
  mkdir -p "$RUNS/$PFX"
  for L in 0.0 0.5 1.0; do
    mkdir -p "$RUNS/$PFX/sw-$L"
    cp -a "$B" "$RUNS/$PFX/sw-$L/"
    sed -i '' "s/^section_weight          = .*/section_weight          = $L/" "$RUNS/$PFX/sw-$L/rung-01000/.fux/tune.toml"
    grep -c "^section_weight          = $L\$" "$RUNS/$PFX/sw-$L/rung-01000/.fux/tune.toml"
    diff -r "$B" "$RUNS/$PFX/sw-$L/rung-01000" -x runtime > "$EV/arm-diff-sw-$L.txt" || true
  done
}
step arms_copy arms_job

# 4 · G0's before-copy: the pre-section engine (its closed key set refuses the
#     new keys, so both go — recorded — then --full). Run-specific: adapt.
pre_job() {
  mkdir -p "$RUNS/$PFX-pre"
  cp -a "$RUNG" "$RUNS/$PFX-pre/"
  local P=$RUNS/$PFX-pre/rung-01000
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
}
step pre_ingest pre_job
P=$RUNS/$PFX-pre/rung-01000

# 5 · capture: three arms on the pinned engine, one on the pre-section engine
capture_job() {
  for L in 0.0 0.5 1.0; do
    python3 tools/quality-controls/golden_run.py --rung rung-01000 --tree "$RUNS/$PFX/sw-$L/rung-01000" \
      --evidence "$EV/sw-$L/rung-01000" --sets "$SETID" --arm "sw-$L" --engine-commit "$COMMIT" --fux "$FUX"
  done
  python3 tools/quality-controls/golden_run.py --rung rung-01000 --tree "$P" \
    --evidence "$EV/pre-section/rung-01000" --sets "$SETID" --arm pre-section --engine-commit dca6aaa4 --fux "$PRE"
}
step golden_run capture_job

# 6 · gates, and G5 (descriptive)
mkdir -p "$EV/g0" "$EV/g3" "$EV/g4" "$EV/g5" "$EV/latency"
step g0 bash -c "python3 '$EV/g0.py' '$EV/pre-section/rung-01000' '$EV/sw-0.0/rung-01000' > '$EV/g0/g0.json'"

# DoD 3 · G3: one frozen g3.py per treatment arm, side by side, then merged
g3_all() {
  local pids=() arm
  for arm in $TREATMENTS; do
    python3 "$HERE/g3_one_arm.py" run "$EV/g3.py" "$arm" --fux "$FUX" --arms "$RUNS/$PFX" --questions "$Q" \
      > "$EV/g3/g3-$arm.json" &
    pids+=($!)
  done
  local pid rc=0
  for pid in "${pids[@]}"; do wait "$pid" || rc=1; done
  [ $rc -eq 0 ] || { echo "refusing: a g3 arm process failed"; return 1; }
  python3 "$HERE/g3_one_arm.py" merge $(for arm in $TREATMENTS; do printf '%s ' "$EV/g3/g3-$arm.json"; done) > "$EV/g3/g3.json"
}
step g3_parallel g3_all

step g4 bash -c "'$PY' '$EV/g4.py' --tree '$RUNS/$PFX/sw-1.0/rung-01000' --questions '$Q' > '$EV/g4/g4.json'"
step g5 bash -c "python3 '$EV/g5.py' --tree '$B' --evidence '$EV' > '$EV/g5/g5.json'"

# DoD 2 · join G1 before anything else (and certainly before latency)
t0=$(date +%s)
wait "$G1_PID" || { echo "refusing: the G1 background job failed — see $EV/g1-bg.log"; exit 1; }
printf '%s\t%s\t%s\t%s\n' g1_join_wait "$t0" "$(date +%s)" "$(( $(date +%s) - t0 ))" >> "$TIMING"
[ -s "$EV/g1.json" ] || { echo "refusing: g1.json missing or empty"; exit 1; }

# 7 · DoD 4 · latency, standalone, last: two copies of the G1 copy, one line changed
lat_prep() {
  for L in 0.0 1.0; do
    mkdir -p "$RUNS/$PFX-lat/sw-$L"
    cp -a "$G" "$RUNS/$PFX-lat/sw-$L/"
    sed -i '' "s/^section_weight          = .*/section_weight          = $L/" "$RUNS/$PFX-lat/sw-$L/rung-10000/.fux/tune.toml"
    (cd "$RUNS/$PFX-lat/sw-$L/rung-10000" && "$FUX" build > /dev/null 2>&1 || true)
  done
}
step latency_prep lat_prep
# nothing of ours may still be running; record the load the timed calls see
jobs -r | grep -q . && { echo "refusing: a background job is still running"; exit 1; }
echo "latency starts: $(uptime)" | tee -a "$EV/latency/uptime-before.txt"
step latency python3 "$EV/latency.py" --fux "$FUX" --arms "$RUNS/$PFX-lat" --questions "$Q" > "$EV/latency/latency.json"
echo "latency ended: $(uptime)" | tee -a "$EV/latency/uptime-before.txt"

cat "$EV/g0/g0.json" "$EV/g1.json" "$EV/g3/g3.json" "$EV/g4/g4.json" "$EV/latency/latency.json" | grep '"verdict"'
awk -F'\t' '{s+=$4} END {print "serial-sum of logged steps (s):", s}' "$TIMING"
echo CAPTURE-DONE
