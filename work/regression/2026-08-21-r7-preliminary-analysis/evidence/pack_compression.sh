#!/usr/bin/env bash
# R7 preliminary analysis — real git-pack compression ratio on the repo's own
# committed index, measured in isolation (source docs excluded, so the number
# is about the index alone, not the corpus it indexes).
#
# Run from the repo root:
#     bash work/regression/2026-08-21-r7-preliminary-analysis/evidence/pack_compression.sh
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
TMPD="$(mktemp -d)"
trap 'rm -rf "$TMPD"' EXIT

cp -r "$ROOT/.fux/index" "$TMPD/index"
cd "$TMPD"

RAW=$(find index -name "*.jsonl" -exec stat -f "%z" {} + | awk '{s+=$1} END{print s}')

git init -q
git add index
git -c user.email=t@t -c user.name=t commit -q -m "index only"
git gc -q --aggressive

PACKFILE=$(find .git/objects/pack -name "*.pack")
PACKED=$(stat -f "%z" "$PACKFILE")

echo "raw bytes:    $RAW"
echo "packed bytes: $PACKED"
python3 -c "print(f'ratio: {$RAW/$PACKED:.3f}x')"
