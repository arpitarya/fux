#!/bin/sh
# W-300's L13 run. From the repository root, with fux's own .venv.
# The pre-W-300 engine is main @ 9688d479, extracted beside the run.
set -eu
OLD="$(mktemp -d)"
git archive 9688d479 src | tar -x -C "$OLD"
PYTHONPATH=src .venv/bin/python work/regression/2026-10-25-w300-merged-query/evidence/run.py \
    "$OLD/src" work/regression/2026-10-25-w300-merged-query/evidence
# ⚠ Run it with nothing else writing .fux/index: G0c compares two engines over
# THIS repository's committed index, and a re-ingest between the two arms (a
# post-commit hook does one) makes them disagree for a reason that is not the
# engine — which is what voided the first run (evidence/run1-void/).
