#!/usr/bin/env bash
# The W-54 fixture: the URL path, exercised offline, end to end.
#
# Successor to `work/regression/2026-08-18-ingest-and-index/evidence/fixture.sh`,
# which reproduces the PRE-W-54 surface (`[sources.url] middleware`,
# `[sources] dirs`) and is kept as that run's evidence, not updated in place.
#
# This repo does not exercise the URL path — there is no `.fux/sources/urls`
# and `[sources.url]` is commented out in `fux.toml`. `pytest -q tests`
# therefore says nothing about four of W-54's five defects. This fixture is
# what says something.
#
# What it covers, one case per defect:
#   1. a hashed URL record that ingests AND BUILDS (exit 0, manifest present)
#   2. a fragment-bearing URL surviving the round trip
#   3. two URLs differing only by fragment producing two records
#   4. a fresh tree ingesting URLs with no hand-written fetcher
#   5. per-line `meta=plain` loosening the L5 floor for one document only
#
#   ./fixture.sh /tmp/fux-w54-demo && cd /tmp/fux-w54-demo
#
# Requires fux on PATH, or PYTHONPATH=<repo>/src with `python3 -m fux.cli`.
set -euo pipefail
DEMO="${1:-/tmp/fux-w54-demo}"
HERE="$(cd "$(dirname "$0")" && pwd)"
FUX="${FUX:-fux}"

rm -rf "$DEMO"; mkdir -p "$DEMO/docs"
cd "$DEMO"
git init -q .; git config user.email a@b.c; git config user.name t

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

cat > docs/pruning.md <<'EOF'
---
type: ADR
title: Pruning was measured and failed
---

# Pruning was measured and failed

The pruning gate ran twice. The committed index carries full postings,
permanently.
EOF

# --- case 4: a fresh tree, and NO hand-written fetcher anywhere -------------
# `fux setup` writes fux.toml, both source lists and both fetchers. Nothing
# below copies a fetcher in from this repo except the offline stand-in, which
# REPLACES the shipped http.py so the run needs no network.
"$FUX" setup

test -f .fux/fetchers/http.py || { echo "FAIL: setup wrote no http.py"; exit 1; }
test -f .fux/fetchers/cdp.py  || { echo "FAIL: setup wrote no cdp.py";  exit 1; }

cp "$HERE/demo-fetcher.py" .fux/fetchers/http.py     # offline stand-in
cp "$HERE/demo-fetcher.py" .fux/fetchers/cdp.py      # same pages, other route

cat > fux.toml <<'EOF'
[sources]

[sources.url]
fetcher   = ".fux/fetchers/http.py"
urls_file = ".fux/sources/urls"
meta      = "hashed"           # the L5 floor; a line may loosen it

[sources.url.config]
greeting = "hello"             # the fetcher's vocabulary, never fux's

[index]
shards = 256
EOF

# --- the committed source lists, both on the one grammar -------------------
cat > .fux/sources/dirs <<'EOF'
# one entry per line; the loader dedupes and sorts
docs
EOF

# `fux url` writes these, but a hand-made list must load too (decision 13),
# so the fixture writes some by hand and some through the command.
cat > .fux/sources/urls <<'EOF'
# one URL per line. `#` is a comment at line start or after whitespace --
# NOT inside a URL, which is the whole of W-49.

# cases 2 and 3: a fragment survives, and two URLs differing only by fragment
# are two documents.
https://example.invalid/handbook#oncall    fetch=http meta=hashed
https://example.invalid/handbook#deploys   fetch=http meta=hashed

# a hand-written line: every attribute absent, so every default applies.
https://example.invalid/handbook/oncall

# case 5: one public document opts out of hashing. The source-wide floor
# stays `hashed` for everything else.
https://example.invalid/public/api          fetch=http meta=plain

# a fetch that fails is a skip, never a deletion.
https://example.invalid/gone
EOF

# case 2 again, through the managing verb rather than by hand.
"$FUX" url https://example.invalid/handbook/deploys --cdp

git add -A; git commit -qm init
echo "fixture ready at $DEMO"
