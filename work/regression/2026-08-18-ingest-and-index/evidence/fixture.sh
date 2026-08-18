#!/usr/bin/env bash
# The fixture behind ADR-DOTFUX / ADR-INGEST / ADR-URL-INGEST /
# ADR-INDEX-LIFECYCLE. Three local documents plus three URLs served by a
# no-network middleware, so every example reproduces offline.
#
#   ./fixture.sh /tmp/fux-ingest-demo && cd /tmp/fux-ingest-demo
#   fux ingest                 # local only, offline
#   fux ingest --refresh-urls  # + the middleware
#
# Requires fux on PATH, or PYTHONPATH=<repo>/src with `python3 -m fux.cli`.
set -euo pipefail
DEMO="${1:-/tmp/fux-ingest-demo}"
HERE="$(cd "$(dirname "$0")" && pwd)"
rm -rf "$DEMO"; mkdir -p "$DEMO/docs" "$DEMO/.fux/sources" "$DEMO/.fux/middleware"
cd "$DEMO"

cat > fux.toml <<'EOF'
[sources]
dirs = ["docs"]

[sources.url]
middleware = ".fux/middleware/demo.py"
urls_file  = ".fux/sources/urls"
meta       = "hashed"          # the default; set "plain" to see readable titles

[sources.url.config]
greeting = "hello"             # the middleware's vocabulary, never fux's
EOF

cp "$HERE/demo-middleware.py" .fux/middleware/demo.py

cat > .fux/sources/urls <<'EOF'
# one URL per line; `#` comments and blank lines are ignored
https://example.invalid/handbook/oncall
https://example.invalid/handbook/deploys
https://example.invalid/gone
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

printf 'binary\x00stuff' > docs/logo.png     # exercises the skip path
: > docs/empty.md                            # exercises the skip path

git init -q .; git config user.email a@b.c; git config user.name t
git add -A; git commit -qm init
echo "fixture ready at $DEMO"
