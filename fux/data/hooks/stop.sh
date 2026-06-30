#!/usr/bin/env bash
# Stop → validate schema/refs/staleness/conflicts; honour strictness mode.
# exit 2 hard-blocks (only when the project opts into `strict`). plan §8.
# NOTE: this hook deliberately omits `set -e` and does NOT guard fux_run with
# `|| true` — its exit code is the blocking signal: hook-check returns 0/2 (the
# Python guard makes a crash impossible), and that 2 must pass straight through.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
. "$DIR/_common.sh"
fux_run hook-check
