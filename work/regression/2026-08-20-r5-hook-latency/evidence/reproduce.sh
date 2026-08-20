#!/bin/sh
# Reproduces every number in ../report.md and ../VERDICT.md.
#
#   ./reproduce.sh <fux-repo-root>
#
# Offline. Builds throwaway git repositories, wires each with
# `fux hooks --install`, and drives git itself — nothing is mocked. Expect
# ~35 min: the 100 000-document corpus is the long pole, and R5's verdict is
# read from it.
#
# The engine measured is the WORKING TREE, not the published wheel — the
# maintenance plane is unreleased. The report records the commit sha.
set -eu
REPO="${1:-$(cd "$(dirname "$0")/../../../.." && pwd)}"

# R5 and R6, against tools/maintenance-bench/PRE-REGISTRATION.md
"$REPO/.venv/bin/python" "$REPO/tools/maintenance-bench/run.py" \
  --sizes 1000 10000 100000 --repeats 5

# The attribution behind report.md §3 — where the failing 44 s goes.
# Run with no hook installed, so each part is timed alone and nothing is
# double-counted.
"$REPO/.venv/bin/python" "$REPO/tools/maintenance-bench/attribute.py" \
  --sizes 1000 10000 100000 --repeats 3
