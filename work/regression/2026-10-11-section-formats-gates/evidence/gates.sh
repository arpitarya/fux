set -euo pipefail
S=/private/tmp/claude-501/-Users-arpitarya-my-programs-fux/6534f1ea-c395-4bfa-b95a-268db4052984/scratchpad
FUX=$S/engine/.venv/bin/fux
R=/Users/arpitarya/my_programs/fux
G=/Users/arpitarya/my_programs/fux-lab/arms/runs/w273-gates
EV=$R/work/regression/2026-10-10-section-gain-only/evidence
mkdir -p $G $S/ev
for L in 0.0 0.25 0.5 1.0 2.0; do
  mkdir -p $G/sw-$L
  cp -a /Users/arpitarya/my_programs/fux-lab/arms/runs/w273-base/rung-01000 $G/sw-$L/
  sed -i '' "s/^section_weight          = 0.0/section_weight          = $L/" $G/sw-$L/rung-01000/.fux/tune.toml
  grep "^section_weight" $G/sw-$L/rung-01000/.fux/tune.toml
done
cd $R
python3 tools/quality-controls/golden_run.py --rung rung-01000 --tree $G/sw-0.0/rung-01000 \
  --evidence $S/ev/sw-0.0 --sets 5-claude --arm sw-0.0 --engine-commit b4d961cd --fux $FUX > $S/ev/run.log 2>&1
python3 $EV/g0.py $EV/sw-0.0/rung-01000 $S/ev/sw-0.0 > $S/ev/g0.json
python3 $EV/g3.py --fux $FUX --arms $G --questions work/golden/questions/set-5-claude.jsonl > $S/ev/g3.json
echo DONE
