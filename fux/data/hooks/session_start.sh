#!/usr/bin/env bash
# SessionStart → inject the compact Tier-1 INDEX (plan §8). $0, deterministic.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
. "$DIR/_common.sh"
# Non-blocking hook: a failing/missing fux must not trip `set -e` into breaking the
# session — fail-open. The strict exit-2 path lives only in stop.sh.
fux_run context || true
