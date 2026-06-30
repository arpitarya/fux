#!/usr/bin/env bash
# PostToolUse(Edit|Write) → remind if an edited file's governing rule drifted.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
. "$DIR/_common.sh"
# Non-blocking hook: fail-open so a failing/missing fux never breaks the session.
fux_run hook-touch || true
