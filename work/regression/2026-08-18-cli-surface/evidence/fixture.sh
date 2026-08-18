#!/usr/bin/env bash
# The fixture behind ADR-CLI's examples. Three documents, deterministic.
# Rebuilds the corpus every run, so the transcript is reproducible.
#
#   ./fixture.sh /tmp/fux-cli-demo && cd /tmp/fux-cli-demo && fux ingest
#
# Requires fux on PATH (`pip install -e .` from the repo root) or
# PYTHONPATH=<repo>/src with `python3 -m fux.cli` in place of `fux`.
set -euo pipefail
DEMO="${1:-/tmp/fux-cli-demo}"
rm -rf "$DEMO"; mkdir -p "$DEMO/docs"; cd "$DEMO"

cat > fux.toml <<'EOF'
[sources]
dirs = ["docs"]
EOF

cat > docs/pruning.md <<'EOF'
---
type: ADR
title: Pruning was measured and failed
---

# Pruning was measured and failed

The pruning gate ran twice. The second run gated on recall@20 and the best
selector landed 35.9 points below the unpruned baseline at 6 percent
retention. The committed index therefore carries full postings, permanently.
EOF

cat > docs/index-format.md <<'EOF'
---
type: Compare Doc
title: The committed index format
---

# The committed index format

The committed index is sharded doc-major JSONL under the fux directory. Each
line is one document record, written through a single canonical encoder:
sorted keys, compact separators, no floats, no nulls, NFC text.
EOF

cat > docs/refer.md <<'EOF'
---
type: Paper
title: The refer plane
---

# The refer plane

Answers rank in the committed index, then fetch the cited documents from the
system that owns them, re-score passages on the fetched bytes, and cite a
fresh sha. Content is never copied into the index.
EOF

git init -q .; git config user.email a@b.c; git config user.name t
git add -A; git commit -qm init
echo "fixture ready at $DEMO"
