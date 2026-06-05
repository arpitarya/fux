#!/usr/bin/env bash
# SessionStart → inject the compact Tier-1 INDEX (plan §8). $0, deterministic.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
. "$DIR/_common.sh"
fux_run context
