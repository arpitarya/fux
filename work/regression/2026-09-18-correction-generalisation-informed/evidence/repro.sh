#!/usr/bin/env sh
# Reproduces the 2026-09-18 informed run. Engine at 7259bab7. Everything outside the repo.
set -e
R="$(cd "$(dirname "$0")/../../../.." && pwd)"     # repo root
W="${TMPDIR:-/tmp}/cg-informed"; rm -rf "$W"; mkdir -p "$W"
uv venv --python 3.12 "$W/venv" >/dev/null
mkdir -p "$W/pkg"; cp -R "$R/src" "$R/node" "$R/pyproject.toml" "$R/hatch_build.py" "$R/README.md" "$R/LICENSE" "$W/pkg/"
uv pip install --python "$W/venv/bin/python" "$W/pkg" >/dev/null
# corpus = records/ + docs/ ONLY. Never work/.
mkdir -p "$W/corpus"; cd "$W/corpus"; git init -q .; git config user.email s@s; git config user.name s
cp -R "$R/records" records; cp -R "$R/docs" docs; git add -A; git commit -qm corpus
"$W/venv/bin/python" -m fux.cli setup >/dev/null; "$W/venv/bin/python" -m fux.cli add records >/dev/null; "$W/venv/bin/python" -m fux.cli add docs >/dev/null; "$W/venv/bin/python" -m fux.cli build >/dev/null
cp -R "$W/corpus" "$W/run-ii"
"$W/venv/bin/python" "$R/tools/quality-controls/correction_generalisation.py" \
  --tree "$W/run-ii" --arm ii \
  --paraphrases "$R/work/regression/2026-09-18-correction-generalisation-informed/evidence/paraphrases-informed-ii.jsonl" \
  --rows-out "$W/rows-ii.jsonl" --json-out "$W/summary-ii.json"
echo "rows: $W/rows-ii.jsonl"
