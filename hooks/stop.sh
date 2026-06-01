#!/usr/bin/env bash
# Stop → validate schema/refs/staleness/conflicts; honour strictness mode.
# exit 2 hard-blocks (only when the project opts into `strict`). plan §8.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
. "$DIR/_common.sh"
fux_run hook-check
