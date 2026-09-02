#!/bin/bash
# W-102's leak, both arms, from a scratch repo. $1 = "pre" (PYTHONPATH at the
# pre-fix tree) or "head". $2 = the pre-fix worktree's src, for "pre".
set -u
FUXPY="${FUXPY:?path to a python that can import fux}"
run() { if [ "$1" = pre ]; then PYTHONPATH="$2" $FUXPY -m fux "${@:3}"; else $FUXPY -m fux "${@:3}"; fi; }
rm -rf .fux/index .fux/runtime
run "$@" ingest --full | tail -2
echo "-- q1 the address (must NOT match: it is in an enrichment BODY)"
run "$@" find "ops-oncall corp.example"
echo "-- q2 enrichment vocabulary (MUST match: the feature still works)"
run "$@" find "escalate restart window"
echo "-- q3 the frontmatter address (must NOT match: frontmatter is never indexed)"
run "$@" find "reviewer audit.invalid"
echo "-- q4 the document's own body (MUST match: unaffected)"
run "$@" find "alpha service restarts nightly"
