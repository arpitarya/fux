#!/bin/sh
# Reproduces every number in ../report.md and ../VERDICT.md.
#
#   ./reproduce.sh <fux-repo-root>
#
# Starts a mock HTTP server on 127.0.0.1 and reaches it through the consumer
# fetcher `fux setup` generates. No external network: the only socket opened is
# to loopback, so this runs on an air-gapped machine.
#
# The engine measured is the WORKING TREE, not the published wheel — the refer
# plane is unreleased. The report records the commit sha.
set -eu
REPO="${1:-$(cd "$(dirname "$0")/../../../.." && pwd)}"
exec "$REPO/.venv/bin/python" "$REPO/tools/refer-bench/run.py" --pairs 20
