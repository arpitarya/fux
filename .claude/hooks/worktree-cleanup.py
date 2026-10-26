#!/usr/bin/env python3
"""Worktree cleanup — SR-WORK-CLEANUP decisions 1-6 and 10.

A worktree is removed only when nothing in it can be lost: its HEAD is in
`main`, it has no modified/staged/deleted/untracked file, every ignored file is
build output, and no live process holds its lock. Removal is `git worktree
remove` then `git branch -d` then `git worktree prune` — never forced, so git
itself refuses if a check here was wrong.

    python3 .claude/hooks/worktree-cleanup.py            # report every verdict
    python3 .claude/hooks/worktree-cleanup.py --apply    # remove the safe ones
    python3 .claude/hooks/worktree-cleanup.py --apply PATH...   # only these

Imported by now-ledger.py at SessionEnd (SR-WORK-NOW decision 4).
"""
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Decision 1(c): the only ignored files a removal may take with it. Grows only
# by the decider's ruling.
BUILD_OUTPUT = {
    "target", "node_modules", "dist", "build", ".venv", "venv", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".nox", ".cache",
    ".turbo", ".next", ".parcel-cache", "coverage", ".coverage", ".lockmaster",
    "htmlcov", ".eggs", "runtime", ".codelaw",  # fux's and codelaw's rulings, joined in the kit (W-09)
    ".DS_Store",
}


def git(*args, cwd=ROOT):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr.strip()


def worktrees():
    """Every worktree but the main one: dicts of path, head, branch, locked."""
    _, out, _ = git("worktree", "list", "--porcelain")
    trees, cur = [], {}
    for line in out.splitlines() + [""]:
        if not line:
            if cur:
                trees.append(cur)
            cur = {}
            continue
        key, _, val = line.partition(" ")
        if key == "worktree":
            cur = {"path": val, "head": "", "branch": "", "locked": None}
        elif key == "HEAD":
            cur["head"] = val
        elif key == "branch":
            cur["branch"] = val.removeprefix("refs/heads/")
        elif key == "locked":
            cur["locked"] = val
    main = str(ROOT)
    return [t for t in trees if os.path.realpath(t["path"]) != os.path.realpath(main)]


def pid_alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def lock_state(reason):
    """None (unlocked), 'stale' (pid dead, decision 10) or 'live' (red)."""
    if reason is None:
        return None
    m = re.search(r"pid[ :=]*(\d+)", reason)
    if m and not pid_alive(int(m.group(1))):
        return "stale"
    return "live"


def verdict(t):
    """(safe, reasons) for one worktree — decision 1's four checks."""
    path, reasons = t["path"], []
    if not Path(path).is_dir():
        return True, ["already gone"]
    if not t["head"]:
        reasons.append("no HEAD")
    elif git("merge-base", "--is-ancestor", t["head"], "main")[0] != 0:
        reasons.append(f"HEAD {t['head'][:8]} is not in main")
    _, st, _ = git("status", "--porcelain", "--untracked-files=all", cwd=path)
    if st.strip():
        n = len(st.splitlines())
        reasons.append(f"{n} modified, staged, deleted or untracked file{'s' * (n != 1)}")
    _, ig, _ = git("status", "--porcelain", "--ignored", "--untracked-files=normal", cwd=path)
    for line in ig.splitlines():
        if line.startswith("!! "):
            rel = line[3:].rstrip("/")
            if not any(part in BUILD_OUTPUT for part in Path(rel).parts):
                reasons.append(f"ignored `{rel}` is not build output")
    if lock_state(t["locked"]) == "live":
        reasons.append(f"locked by a live process or no pid ({t['locked'] or 'no reason'})")
    return not reasons, reasons


def clean(t):
    """Remove one safe worktree. Returns (ok, message). Never forces."""
    path = t["path"]
    if lock_state(t["locked"]) == "stale":
        git("worktree", "unlock", path)
    if Path(path).is_dir():
        code, _, err = git("worktree", "remove", path)
        if code != 0:
            return False, f"git refused to remove {path}: {err}"
    if t["branch"] and t["branch"] != "main":
        code, _, err = git("branch", "-d", t["branch"])
        if code != 0:
            return False, f"removed {path}; git refused to delete branch {t['branch']}: {err}"
    git("worktree", "prune")
    return True, f"removed {path}" + (f" and branch {t['branch']}" if t["branch"] else "")


def sweep(paths=None, apply=False):
    """Check (and with apply, clean) the worktrees, optionally only `paths`.
    Returns (cleaned, red): lists of (path, message-or-reasons)."""
    want = {os.path.realpath(p) for p in paths} if paths else None
    cleaned, red = [], []
    for t in worktrees():
        if want is not None and os.path.realpath(t["path"]) not in want:
            continue
        safe, reasons = verdict(t)
        if not safe:
            red.append((t["path"], reasons))
        elif apply:
            ok, msg = clean(t)
            (cleaned if ok else red).append((t["path"], msg if ok else [msg]))
        else:
            cleaned.append((t["path"], "safe to remove"))
    if apply:
        git("worktree", "prune")
    return cleaned, red


def main(argv):
    apply = "--apply" in argv
    paths = [a for a in argv if not a.startswith("--")] or None
    cleaned, red = sweep(paths, apply)
    for path, msg in cleaned:
        print(f"ok   {path} — {msg}")
    for path, reasons in red:
        print(f"RED  {path} — " + "; ".join(reasons))
    if not cleaned and not red:
        print("no worktrees besides main")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
