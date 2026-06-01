#!/usr/bin/env bash
# Shared launcher: prefer the installed `fux` binary, else fall back to the
# module. Keeps hooks working even when the console script isn't on PATH.
# Usage: source this file, then: fux_run <subcommand>
fux_run() {
  if command -v fux >/dev/null 2>&1; then
    fux "$@"
  else
    PY="${FUX_PYTHON:-$(command -v python3.14 || command -v python3 || command -v python)}"
    "$PY" -m fux "$@"
  fi
}
