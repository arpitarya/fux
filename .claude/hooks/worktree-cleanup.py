#!/usr/bin/env python3
"""Remove a git worktree only when nothing in it can be lost — SR-WORK-CLEANUP.

    python3 .claude/hooks/worktree-cleanup.py            # every worktree's verdict
    python3 .claude/hooks/worktree-cleanup.py --apply    # remove the safe ones

Nothing is lost when all four hold (decision 1):

    (a) its HEAD is already in `main` — every commit merged;
    (b) it has no modified, staged, deleted or untracked file;
    (c) every ignored file in it is build output (BUILD_OUTPUT below);
    (d) no live process holds its lock.

Cleaning is `git worktree remove` — never `--force` — then `git branch -d` —
never `-D` — then `git worktree prune` (decision 2). Git refuses either one if a
check here was wrong, so a bug in this file cannot lose data. A red worktree is
never touched; `now-ledger.py` files it for Arpit (decision 3). Cleanup never
merges (decision 4).

Importable: `now-ledger.py` loads `verdicts()` and `clean()` at SessionEnd.
Stdlib only.
"""
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

#: What an ignored path may be, by any one of its components, for (c) to hold.
#: The list grows only by Arpit's ruling (SR-WORK-CLEANUP, Consequences).
BUILD_OUTPUT = frozenset({
    "target", "node_modules", "dist", "build", ".venv", "venv", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".nox", ".coverage",
    "htmlcov", ".eggs", ".cache", ".turbo", ".next", ".parcel-cache", "runtime",
    ".DS_Store",
})


def git(*argv: str, cwd: Path = ROOT, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *argv], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", check=check)


@dataclass
class Worktree:
    path: Path
    head: str = ""
    branch: str = ""  # short name, "" when detached
    locked: str | None = None  # the lock reason; None when unlocked
    reasons: list[str] = field(default_factory=list)
    stale_lock: bool = False

    @property
    def safe(self) -> bool:
        return not self.reasons


def worktrees(root: Path = ROOT) -> list[Worktree]:
    """Every worktree but the main one, from `git worktree list --porcelain`."""
    out = git("worktree", "list", "--porcelain", cwd=root).stdout
    found: list[Worktree] = []
    for block in out.strip().split("\n\n"):
        wt = None
        for line in block.splitlines():
            key, _, value = line.partition(" ")
            if key == "worktree":
                wt = Worktree(Path(value))
            elif wt is None:
                continue
            elif key == "HEAD":
                wt.head = value
            elif key == "branch":
                wt.branch = value.removeprefix("refs/heads/")
            elif key == "locked":
                wt.locked = value
        if wt is not None:
            found.append(wt)
    main = Path(git("rev-parse", "--show-toplevel", cwd=root).stdout.strip() or root).resolve()
    return [w for w in found if w.path.resolve() != main]


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _lock_pid(reason: str) -> int | None:
    for token in reason.replace("=", " ").replace(":", " ").split():
        if token.isdigit():
            return int(token)
    return None


def check(wt: Worktree, root: Path = ROOT, main_ref: str = "main") -> Worktree:
    """Fill `wt.reasons` with every way removing it could lose something."""
    if not wt.path.is_dir():
        wt.reasons.append("its directory is gone (prune will drop it)")
        return wt
    if wt.head and git("merge-base", "--is-ancestor", wt.head, main_ref, cwd=root).returncode != 0:
        wt.reasons.append(f"HEAD {wt.head[:8]} is not in {main_ref}")
    status = git("status", "--porcelain", "--ignored", "--untracked-files=all", cwd=wt.path)
    if status.returncode != 0:
        wt.reasons.append("git status failed: " + status.stderr.strip()[:120])
        return wt
    dirty, ignored = [], []
    for line in status.stdout.splitlines():
        code, path = line[:2], line[3:]
        if code == "!!":
            if not any(part in BUILD_OUTPUT for part in Path(path.rstrip("/")).parts):
                ignored.append(path)
        elif line.strip():
            dirty.append(path)
    if dirty:
        wt.reasons.append(f"{len(dirty)} modified/untracked file(s), e.g. {dirty[0]}")
    if ignored:
        wt.reasons.append(f"{len(ignored)} ignored non-build file(s), e.g. {ignored[0]}")
    if wt.locked is not None:
        pid = _lock_pid(wt.locked)
        if pid is None:
            wt.reasons.append(f"locked, naming no pid ({wt.locked or 'no reason'})")
        elif _pid_alive(pid):
            wt.reasons.append(f"locked by live pid {pid}")
        else:
            wt.stale_lock = True  # decision 10: lifted as part of the removal
    return wt


def verdicts(root: Path = ROOT, paths: set[Path] | None = None) -> list[Worktree]:
    """Every (or each named) worktree, checked."""
    out = []
    for wt in worktrees(root):
        if paths is not None and wt.path.resolve() not in {p.resolve() for p in paths}:
            continue
        out.append(check(wt, root))
    return out


def clean(wt: Worktree, root: Path = ROOT) -> str | None:
    """Remove one SAFE worktree. Returns None on success, else what git said."""
    if not wt.safe:
        return "not safe: " + "; ".join(wt.reasons)
    if wt.stale_lock:
        git("worktree", "unlock", str(wt.path), cwd=root)
    done = git("worktree", "remove", str(wt.path), cwd=root)  # never --force
    if done.returncode != 0:
        return done.stderr.strip()
    if wt.branch:
        git("branch", "-d", wt.branch, cwd=root)  # never -D; a refusal keeps the branch
    git("worktree", "prune", cwd=root)
    return None


def main(argv: list[str]) -> int:
    apply = "--apply" in argv
    found = verdicts()
    if not found:
        print("no worktrees besides the main one")
        return 0
    for wt in found:
        if wt.safe:
            if apply:
                err = clean(wt)
                print(f"  removed  {wt.path}" if err is None else f"  kept     {wt.path} — git: {err}")
            else:
                print(f"  safe     {wt.path}")
        else:
            print(f"  RED      {wt.path} — " + "; ".join(wt.reasons))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
