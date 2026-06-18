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


def user_name(root: Path) -> str | None:
    """The configured git author name — the default `fux ratify --by` ratifier."""
    return _run(["config", "user.name"], root) or None


def hooks_dir(root: Path) -> Path | None:
    """Resolve the repo's git hooks dir (honours core.hooksPath / worktrees)."""
    rel = _run(["rev-parse", "--git-path", "hooks"], root)
    return (root / rel) if rel else None


def changed_files(root: Path) -> list[str]:
    """Repo-relative paths changed in the working tree (staged + unstaged + new).

    Uses `diff --name-only HEAD` (tracked) + `ls-files --others` (untracked) — clean
    one-path-per-line output, no porcelain column parsing.
    """
    tracked = _run(["diff", "--name-only", "HEAD"], root) or ""
    untracked = _run(["ls-files", "--others", "--exclude-standard"], root) or ""
    files = {ln.strip() for ln in (tracked + "\n" + untracked).splitlines() if ln.strip()}
    return sorted(files)


def last_commit_date(path: Path, root: Path) -> str | None:
    """ISO date (YYYY-MM-DD) of the last commit touching ``path``."""
    rel = path.resolve()
    out = _run(["log", "-1", "--format=%cs", "--", str(rel)], root)
    return out or None


def file_history(path: Path, root: Path, limit: int = 30) -> list[tuple[str, str, str]]:
    """(date, short-hash, subject) for each commit touching ``path``, newest first.

    Follows renames so a rule's reasoning history survives a file move (plan §17.24).
    """
    out = _run(["log", f"-{limit}", "--follow", "--format=%cs%x09%h%x09%s",
                "--", str(path.resolve())], root)
    rows: list[tuple[str, str, str]] = []
    for ln in (out or "").splitlines():
        parts = ln.split("\t", 2)
        if len(parts) == 3:
            rows.append((parts[0], parts[1], parts[2]))
    return rows


def current_branch(root: Path) -> str | None:
    """The checked-out branch name (None on detached HEAD or non-repo)."""
    b = _run(["rev-parse", "--abbrev-ref", "HEAD"], root)
    return b if b and b != "HEAD" else None


def default_branch(root: Path) -> str:
    """The remote's default branch (the protected one), falling back to 'main'."""
    ref = _run(["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"], root)
    return ref.rsplit("/", 1)[-1] if ref else "main"


def has_remote(root: Path) -> bool:
    return bool(_run(["remote"], root))


def open_pr_branch(root: Path, branch: str, paths_: list[str], message: str,
                   title: str, body: str) -> tuple[bool, str]:
    """Switch to a NEW branch, commit ``paths_``, push, and open a PR — never
    committing to the protected branch (§2g). Deterministic git/gh only, no model.

    Returns (ok, info). ok=False with a reason if any step fails (e.g. branch
    exists, no remote, gh missing) so the caller can fall back to printing manual
    commands. The ratification write has already happened on disk; this only
    routes it through the gated PR path.
    """
    if _run(["switch", "-c", branch], root) is None:
        return False, f"could not create branch '{branch}' (already exists?)"
    add = subprocess.run(["git", "add", "--", *paths_], cwd=root,
                         capture_output=True, text=True)
    if add.returncode != 0:
        return False, f"git add failed: {add.stderr.strip()}"
    if _run(["commit", "-m", message], root) is None:
        return False, "git commit failed (nothing staged?)"
    if _run(["push", "-u", "origin", branch], root) is None:
        return False, f"git push failed for '{branch}'"
    try:
        pr = subprocess.run(
            ["gh", "pr", "create", "--base", default_branch(root), "--head", branch,
             "--title", title, "--body", body],
            cwd=root, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        return False, f"gh pr create unavailable: {e}"
    if pr.returncode != 0:
        return False, f"gh pr create failed: {pr.stderr.strip()}"
    return True, pr.stdout.strip()


def diff_since(path: Path, since: str, root: Path, limit: int = 2000) -> str | None:
    """Patch for ``path`` from the state at ``since`` (YYYY-MM-DD) to HEAD."""
    rel = str(path.resolve())
    base = _run(["rev-list", "-1", f"--before={since} 23:59:59", "HEAD", "--", rel], root)
    args = ["diff", f"{base}..HEAD", "--", rel] if base else ["log", "-p", "--", rel]
    out = _run(args, root)
    if not out:
        return None
    return out if len(out) <= limit else out[:limit] + "\n… (truncated)"
