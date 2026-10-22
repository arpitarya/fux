#!/usr/bin/env bash
# SR guard — refuse a commit that changes an SR-owned component without
# staging its OWNING record and every record that DESCRIBES it.
#
# Install once, as a `commit-msg` hook (the escape hatch is read from the
# message, which does not exist yet at `pre-commit` time):
#
#     ln -sf ../../scripts/sr-guard.sh .git/hooks/commit-msg
#
# Escape hatch, on its own line of the commit message:
#
#     no SR affected
#
# That is a claim written into git history under your name, not a silent skip.
#
# 🔴 ONE implementation. The judging is `tests/sr_lib.py` — the same function
# `tests/test_sr_freshness.py` replays over every commit in CI, so the hook and
# the gate cannot disagree (codelaw's single guard, taken 2026-10-21). This
# file only finds a Python and hands it the message. The rule is
# SR-WORK-OWNERSHIP decisions 2a and 3; nothing here states it.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
msg_file="${1:?sr-guard.sh must run as a commit-msg hook, invoked with the message file path as \$1}"
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"
exec "$PY" "$ROOT/tests/sr_lib.py" guard "$msg_file"
