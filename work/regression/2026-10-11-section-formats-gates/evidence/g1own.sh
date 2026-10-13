set -uo pipefail
S=/private/tmp/claude-501/-Users-arpitarya-my-programs-fux/6534f1ea-c395-4bfa-b95a-268db4052984/scratchpad
FUX=$S/engine/.venv/bin/fux
R=/Users/arpitarya/my_programs/fux
L=/Users/arpitarya/my_programs/fux-lab/arms/runs
mkdir -p $L/w273-g1 $S/ev
cp -a $L/gain-g1/rung-10000 $L/w273-g1/
(cd $L/w273-g1/rung-10000 && $FUX ingest --full > $S/ev/g1-ingest.log 2>&1)
python3 $R/work/regression/2026-10-10-section-records/evidence/g1.py $L/w273-g1/rung-10000 > $S/ev/g1.json
cmp $S/ev/g1.json $R/work/regression/2026-10-10-section-gain-only/evidence/g1.json && echo G1-IDENTICAL
(cd $S/own && $FUX ingest --full --no-fetch > $S/ev/own-ingest.log 2>&1 || $FUX ingest --full > $S/ev/own-ingest2.log 2>&1)
echo DONE
