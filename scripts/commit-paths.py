#!/usr/bin/env python3
"""Commit exactly the paths you name — and say out loud what you are leaving.

🔴 **The gate for a failure class this repo has now recorded twice**
([SR-WORK-SESSION](../records/0060_WORK-session.md) decision 13):

1. **2026-09-15, W-184's session** — `git add X && git commit` takes the
   **whole index**, and on a shared tree the index already holds another
   session's staged work. Ten commits used `git commit -- X`; two did not.
2. **2026-09-15, W-177's session** — the same defect with one extra step, which
   is why the first lesson did not prevent it. The rule *"commit with explicit
   pathspecs"* was followed to the letter: the pathspec list was **built from
   `git status`**, so it was explicit, complete, and swept in three files
   another session had staged. **An explicit pathspec derived from the tree is
   not an explicit pathspec** — it is `git commit -a` wearing a disguise.

**What this tool does that a pathspec cannot.** `git commit -- <paths>` is
silent about everything it leaves behind and silent about everything you named
that is not actually dirty. Both silences have cost a commit:

- naming too much takes another session's work (occurrence 1 and 2);
- naming too little omits a restamp your own change requires, and the working
  tree stays green while HEAD goes red
  ([`work/LESSONS.md`](../work/LESSONS.md) §2026-09-15, cause 2).

So this **refuses** rather than warning, in both directions, and the only way
past it is to name what you are leaving — which makes it a decision in the
shell history instead of an accident.

    scripts/commit-paths.py -F msg.txt -- src/fux/cli.py tests/test_cli.py
    scripts/commit-paths.py -m "fix: …" --leave-behind work/golden/questions \\
        -- src/fux/cli.py

⚠ **It is a tool, not a hook, and that is honest rather than ideal.** A
`pre-commit` hook cannot know which dirty paths belong to which session — that
is exactly the thing no mechanism in a shared checkout can see. What it *can*
do is make the leaving explicit, and that is what this is.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "--no-optional-locks", *args], text=True, capture_output=True, check=True
    ).stdout


def dirty_paths(root: Path) -> set[str]:
    """Every path `git status` would show, renames counted at BOTH ends.

    A rename is two paths to git and one edit to a person; missing the old one
    leaves a delete uncommitted and the tree half-renamed.
    """
    out: set[str] = set()
    data = _git("status", "--porcelain", "-z").split("\0")
    i = 0
    while i < len(data):
        rec = data[i]
        if not rec:
            i += 1
            continue
        status, path = rec[:2], rec[3:]
        if status[0] == "R":
            i += 1
            out.add(data[i])
        out.add(path)
        i += 1
    return out


def _covered(path: str, named: set[str]) -> bool:
    """A named directory covers the paths under it, the way a pathspec does."""
    if path in named:
        return True
    return any(path.startswith(n.rstrip("/") + "/") for n in named)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="commit-paths.py",
        description="commit exactly the named paths, refusing on anything unaccounted for",
    )
    ap.add_argument("-m", "--message")
    ap.add_argument("-F", "--file", help="read the commit message from this file")
    ap.add_argument(
        "--leave-behind",
        action="append",
        default=[],
        metavar="PATH",
        help="a dirty path this commit deliberately does not take; repeatable",
    )
    ap.add_argument("--dry-run", action="store_true", help="print the plan; commit nothing")
    ap.add_argument("paths", nargs="+", help="after `--`: the paths to commit")
    args = ap.parse_args(argv)

    if not args.message and not args.file:
        ap.error("one of -m/--message or -F/--file is required")

    root = Path(_git("rev-parse", "--show-toplevel").strip())
    dirty = dirty_paths(root)
    named = set(args.paths)
    leaving = set(args.leave_behind)

    # Direction 1 — you named something that is not dirty. Usually a typo, and
    # a typo'd pathspec commits less than you think and reports success.
    phantom = sorted(p for p in named if not any(_covered(d, {p}) for d in dirty))
    if phantom:
        print(
            "these paths are not dirty, so naming them commits nothing:\n  "
            + "\n  ".join(phantom),
            file=sys.stderr,
        )
        return 1

    # Direction 2 — the tree holds something you did not name. On a shared
    # checkout this is another session's work, and it is the one this exists for.
    unaccounted = sorted(
        p for p in dirty if not _covered(p, named) and not _covered(p, leaving)
    )
    if unaccounted:
        print(
            f"{len(unaccounted)} dirty path(s) are neither named nor left behind:\n  "
            + "\n  ".join(unaccounted)
            + "\n\nName them, or pass --leave-behind for each. On a shared checkout "
            "these are usually ANOTHER SESSION'S staged work, and taking them is "
            "how a commit message stops describing its own commit.",
            file=sys.stderr,
        )
        return 1

    if leaving:
        print("leaving behind, deliberately:", file=sys.stderr)
        for p in sorted(leaving):
            print(f"  {p}", file=sys.stderr)

    # ⚠ **`git commit -- <path>` refuses an UNTRACKED path** ("pathspec … did
    # not match any file(s) known to git"), so a new file has to reach the index
    # first. `git add -- <named>` is safe here precisely because the accounting
    # above has already run: it adds what the caller named and nothing else, and
    # `--only` below keeps everything else in the index out of the commit.
    cmd = ["git", "commit"]
    cmd += ["-F", args.file] if args.file else ["-m", args.message]
    cmd += ["--only", "--", *sorted(named)]
    if args.dry_run:
        print("git add --", *sorted(named))
        print(" ".join(cmd))
        return 0
    add = subprocess.run(["git", "add", "--", *sorted(named)])
    if add.returncode != 0:
        return add.returncode
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    raise SystemExit(main())
