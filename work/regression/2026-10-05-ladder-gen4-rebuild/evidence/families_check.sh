#!/usr/bin/env bash
# W-228 DoD 11 on the generation-4 ladder: run the `families` lens on scratch
# copies of golden rungs and check its misfits against planted-misfits.tsv.
#
#   bash families_check.sh <fux-worktree> <scratch-dir> <rung>...
#
# `--top 1000`: the named lists are cut at `[report] top` (20) and the counts
# are not, so above rung-01000 a planted misfit can be counted but unlisted.
# Each rung is COPIED (the kept ladder is never touched), `fux inspect --json`
# runs twice and the two `families` sections must be byte-equal, then
# check_planted.py scores the misfit list against the committed answer list.
# Reads the rungs and work/golden/planted-misfits.tsv only — never
# work/golden/questions/, never a key.
set -euo pipefail
wt=$(cd "$1" && pwd); out=$2; shift 2
here=$(cd "$(dirname "$0")" && pwd)
lab=${FUX_LAB:-$HOME/my_programs/fux-lab/corpora/golden}
py=$wt/.venv/bin/python
mkdir -p "$out"
for r in "$@"; do
  rm -rf "${out:?}/$r"; cp -R "$lab/$r" "$out/$r"
  for i in 1 2; do
    (cd "$out/$r" && PYTHONPATH="$wt/src" "$py" -m fux inspect --json --top 1000 2>/dev/null) \
      | "$py" -c 'import json,sys; print(json.dumps(json.load(sys.stdin)["families"],indent=1,sort_keys=True,ensure_ascii=False))' \
      > "$out/families-$r.run$i.json"
  done
  cmp "$out/families-$r.run1.json" "$out/families-$r.run2.json"
  cp "$out/families-$r.run1.json" "$out/families-$r.json"
  "$py" "$here/check_planted.py" "$wt/work/golden/planted-misfits.tsv" "$out/families-$r.json" "$r"
done
