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


def hooks_dir(root: Path) -> Path | None:
    """Resolve the repo's git hooks dir (honours core.hooksPath / worktrees)."""
    rel = _run(["rev-parse", "--git-path", "hooks"], root)
    return (root / rel) if rel else None


def last_commit_date(path: Path, root: Path) -> str | None:
    """ISO date (YYYY-MM-DD) of the last commit touching ``path``."""
    rel = path.resolve()
    out = _run(["log", "-1", "--format=%cs", "--", str(rel)], root)
    return out or None


def diff_since(path: Path, since: str, root: Path, limit: int = 2000) -> str | None:
    """Patch for ``path`` from the state at ``since`` (YYYY-MM-DD) to HEAD."""
    rel = str(path.resolve())
    base = _run(["rev-list", "-1", f"--before={since} 23:59:59", "HEAD", "--", rel], root)
    args = ["diff", f"{base}..HEAD", "--", rel] if base else ["log", "-p", "--", rel]
    out = _run(args, root)
    if not out:
        return None
    return out if len(out) <= limit else out[:limit] + "\n… (truncated)"
