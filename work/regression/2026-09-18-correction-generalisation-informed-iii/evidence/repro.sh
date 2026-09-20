#!/bin/bash
# Re-obtain the corpus and re-run arm (iii), informed. Nothing here touches the fux repo.
set -euo pipefail
uv venv --python 3.12 "$HOME/fuxvenv"; . "$HOME/fuxvenv/bin/activate"
uv pip install <a copy of this repo's src/ + pyproject.toml + hatch_build.py + node/>   # fux 3.0.0-alpha.1
curl -sL -o gh.tgz https://codeload.github.com/github/docs/tar.gz/refs/heads/main
mkdir -p gh && tar xzf gh.tgz -C gh --wildcards '*/content/*'
mkdir -p corpus/docs
for a in actions codespaces repositories issues pull-requests authentication billing pages organizations; do
  cp -r gh/docs-main/content/$a corpus/docs/
done   # -> 1006 documents
cd corpus && git init -q && fux setup && fux ingest --no-fetch && fux build
# the harness, with the three W-175 defects patched (see report.md §The harness was patched)
python cg_patched.py --tree "$PWD" --arm iii \
  --paraphrases evidence/paraphrases-informed-iii.jsonl \
  --rows-out evidence/rows-iii.jsonl --json-out evidence/summary-iii.json
