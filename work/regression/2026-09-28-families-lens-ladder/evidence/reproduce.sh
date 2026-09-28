#!/usr/bin/env bash
# Re-derive the `families` lens numbers on two golden rungs, on scratch copies.
#
#   bash reproduce.sh <fux-worktree> <scratch-dir> [-after]
#
# At a2ce3fc6 it reproduces families-<rung>.json. With the lens change of
# ANALYSIS §3 applied, pass `-after` to reproduce families-<rung>-after.json.
#
# The rungs in fux-lab are never modified: each is copied, its missing config
# keys are written by `fux doctor --fix` (the rungs predate them), the
# inspect.toml filed beside this script is dropped in, and `fux inspect --json`
# runs twice so the determinism claim is re-checked, not asserted.
# Reads the rungs only — never work/golden/questions/, never a key.
set -euo pipefail
wt=$(cd "$1" && pwd); out=$2; suffix=${3:-}; here=$(cd "$(dirname "$0")" && pwd)
lab=${FUX_LAB:-$here/../../../../../fux-lab/corpora/golden}   # the kept ladder
py=${FUX_PY:-$wt/.venv/bin/python}
mkdir -p "$out"
for r in rung-seed rung-01000; do
  rm -rf "$out/$r"; cp -R "$lab/$r" "$out/$r"
  cp "$here/inspect.toml" "$out/$r/.fux/inspect.toml"
  (cd "$out/$r" && PYTHONPATH="$wt/src" "$py" -m fux doctor --fix >/dev/null 2>&1)
  for i in 1 2; do
    (cd "$out/$r" && PYTHONPATH="$wt/src" "$py" -m fux inspect --json 2>/dev/null) \
      | "$py" -c 'import json,sys; print(json.dumps(json.load(sys.stdin)["families"],indent=1,sort_keys=True,ensure_ascii=False))' \
      > "$out/families-$r.run$i.json"
  done
  cmp "$out/families-$r.run1.json" "$out/families-$r.run2.json"
  cmp "$out/families-$r.run1.json" "$here/families-$r$suffix.json" && echo "$r$suffix: reproduces"
done
