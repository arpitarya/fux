"""Git helpers for staleness detection — $0, deterministic (plan §10.2)."""
from __future__ import annotations

import subprocess
from pathlib import Path


def _run(args: list[str], cwd: Path) -> str | None:
    try:
        out = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                             text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def is_repo(root: Path) -> bool:
    return _run(["rev-parse", "--is-inside-work-tree"], root) == "true"


def last_commit_date(path: Path, root: Path) -> str | None:
    """ISO date (YYYY-MM-DD) of the last commit touching ``path``."""
    rel = path.resolve()
    out = _run(["log", "-1", "--format=%cs", "--", str(rel)], root)
    return out or None
