#!/usr/bin/env sh
# Baseline of 33 id-queries on three golden rungs. Needs fux-lab's corpora at
# ~/my_programs/fux-lab/corpora/golden/. Everything runs on a COPY, never in fux-lab.
set -e
R="$(cd "$(dirname "$0")/../../../.." && pwd)"; W="${TMPDIR:-/tmp}/id-headroom"; rm -rf "$W"; mkdir -p "$W"
uv venv --python 3.12 "$W/venv" >/dev/null; mkdir -p "$W/pkg"
cp -R "$R/src" "$R/node" "$R/pyproject.toml" "$R/hatch_build.py" "$R/README.md" "$R/LICENSE" "$W/pkg/"
uv pip install --python "$W/venv/bin/python" "$W/pkg" >/dev/null
for RUNG in rung-00100 rung-01000 rung-10000; do
  cp -R "$HOME/my_programs/fux-lab/corpora/golden/$RUNG" "$W/$RUNG"
  ( cd "$W/$RUNG" && "$W/venv/bin/python" -m fux.cli ingest --no-fetch >/dev/null && "$W/venv/bin/python" -m fux.cli build >/dev/null )
  "$W/venv/bin/python" "$(dirname "$0")/probe_idq.py" "$W/$RUNG" "$W/$RUNG.json" | tail -1
done
