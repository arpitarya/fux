"""Shared CLI helper."""
from __future__ import annotations

from pathlib import Path

from fux import paths


def root() -> Path:
    found = paths.find_project_root()
    if found is None:
        raise SystemExit("fux: no .fux/ footprint found here. Run `fux init` first.")
    return found
