#!/bin/sh
# Reproduces every number in ../report.md and ../VERDICT.md.
#
#   ./reproduce.sh <fux-repo-root>
#
# Offline. Builds throwaway git repositories at 1k / 10k / 100k documents,
# wires each with `fux hooks --install`, and drives git itself. Expect ~30 min:
# the 100k corpus alone is 100 000 files written, added and ingested.
#
# The engine measured is the WORKING TREE, not the published wheel — the
# maintenance plane is unreleased. The report records the commit sha.
set -eu
REPO="${1:-$(cd "$(dirname "$0")/../../../.." && pwd)}"
exec "$REPO/.venv/bin/python" "$REPO/tools/maintenance-bench/run.py" \
  --sizes 1000 10000 100000 --repeats 5
