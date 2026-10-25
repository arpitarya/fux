#!/usr/bin/env sh
# W-298 step 1 — reproduce. Needs: git, node/npm (to fetch the pack), uv, a fux checkout at $FUX_TREE.
# Numbers are a function of (pack version, fux commit, intents.tsv). Nothing else.
set -e
FUX_TREE=${FUX_TREE:-$PWD}             # fux checkout at commit 658bc91 (main, 2026-10-25)
W=$(mktemp -d); cd "$W"
npm pack @codelaw/rules-js@0.1.0 >/dev/null
mkdir -p repo/node_modules/@codelaw && tar xzf codelaw-rules-js-0.1.0.tgz
mv package repo/node_modules/@codelaw/rules-js
cd repo && git init -q && git -c user.email=s@l -c user.name=s commit -q --allow-empty -m init
uv run --project "$FUX_TREE" fux setup --no-agents --no-hooks >/dev/null
printf 'paths:\n  include:\n    - node_modules/@codelaw/rules-js/rules\n' >> .fux/sources.yaml
uv run --project "$FUX_TREE" fux ingest
# then: python3 run.py  (edit REPO/FUX at its top) — reads intents.tsv, writes rows.tsv, prints "ask: N/20 in top 5"
