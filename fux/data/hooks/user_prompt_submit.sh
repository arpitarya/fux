#!/usr/bin/env bash
# UserPromptSubmit (optional) → inject only the rules relevant to the prompt.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
. "$DIR/_common.sh"
# Non-blocking hook: fail-open so a failing/missing fux never breaks the session.
fux_run hook-recall || true
