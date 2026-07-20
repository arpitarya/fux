"""Shared CLI helper."""
from __future__ import annotations

from pathlib import Path

from fux import paths
from fux.errors import FuxError


def root() -> Path:
    found = paths.find_project_root()
    if found is None:
        raise FuxError(f"no .fux/ in {Path.cwd()} — run `fux init` first")
    return found


def self_root() -> Path:
    """The shipped self-knowledge bundle (a pre-built footprint mirror).

    Reads fux's *own* graph/rules instead of the project's — so `--self` works in
    any repo, even one with no `.fux/`. Raises if `fux self-build` was never run."""
    bundle = paths.bundled_data_dir() / "self"
    if not (bundle / ".fux" / "out" / "graph.json").exists():
        raise FuxError("no self-knowledge bundle — run `fux self-build` first")
    return bundle


def scope_root(args) -> Path:
    """Pick the project root, or the self bundle when `--self` is passed."""
    return self_root() if getattr(args, "self", False) else root()
