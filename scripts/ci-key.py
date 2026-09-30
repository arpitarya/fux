#!/usr/bin/env python3
"""The FULL-stage verdict key: a digest of every path that can change a FULL
verdict — W-243 step 2, SR-WORK-RELEASE decision 14.

Three callers, one implementation — the `check-version-parity.py` shape:

    python scripts/ci-key.py tree [REV]        # the tree half of the key
    python scripts/ci-key.py cell CELL         # a FULL job's whole key
    python scripts/ci-key.py skips [N]         # how many of the last N commits
                                               # would have skipped FULL
    pytest tests/test_ci_key.py                # every push

🔴 **An EXCLUDE list, never an include list** (Arpit, 2026-09-30). Everything
in the tree counts as code unless `inert` names it, so a new top-level folder
is code by default — it can cost speed, never correctness.

⚠ **Inert does not mean untested.** About two thirds of the unit suite reads
`records/`, `work/` or `docs/`. Excluding them is safe only because FAST runs
the whole suite on every push, the nightly run never reads a verdict, and a
release commit always touches `node/` (the version bump) and so always gets a
fresh FULL run. What the exclusion can do is let an OS-only failure caused by
a documentation change sit until the nightly run — it cannot let one ship.

Stdlib and `git` only: it runs before anything is installed.
"""

from __future__ import annotations

import hashlib
import os
import platform
import shutil
import subprocess
import sys

#: Bumped when the key's shape changes, so an old verdict never matches a new
#: meaning.
SCHEMA = "ci-full-v1"

#: Directories whose every path is inert.
INERT_DIRS = ("work/", "docs/")

#: Files inert wherever they sit.
INERT_FILES = ("CHANGELOG.md",)

#: `*.md` is inert everywhere EXCEPT under these: Markdown here is a template
#: `fux setup` writes, a fixture, or source a test asserts on byte-for-byte.
CODE_ROOTS = ("src/", "node/", "tests/", "tests_e2e/")


def inert(path: str) -> bool:
    """True when `path` cannot change a FULL verdict (the exclude list)."""
    if path.startswith(INERT_DIRS) or path in INERT_FILES:
        return True
    return path.endswith(".md") and not path.startswith(CODE_ROOTS)


def git(*argv: str) -> str:
    return subprocess.run(
        ["git", *argv], capture_output=True, text=True, encoding="utf-8", check=True
    ).stdout


def tree_digest(rev: str = "HEAD") -> str:
    """sha256 over `mode type sha<TAB>path` for every non-inert blob at `rev`.

    Git's own blob ids, so the digest is a property of the commit and not of
    the checkout — line-ending translation or a stray build file cannot move it.
    """
    h = hashlib.sha256()
    for line in git("ls-tree", "-r", "--full-tree", "-z", rev).split("\0"):
        if not line:
            continue
        path = line.split("\t", 1)[1]
        if not inert(path):
            h.update(line.encode("utf-8") + b"\n")
    return h.hexdigest()


def runtime() -> str:
    """The runner half: OS, image, and the resolved Python and Node versions.

    `ImageOS`/`ImageVersion` are set on every GitHub-hosted runner; a runner
    image update changes them and so misses every stored verdict.
    """
    node = shutil.which("node")
    node_v = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip() if node else "none"
    parts = [
        platform.system(), platform.machine(),
        os.environ.get("ImageOS", "?"), os.environ.get("ImageVersion", "?"),
        platform.python_version(), node_v,
    ]
    return "|".join(parts)


def cell_key(cell: str, rev: str = "HEAD") -> str:
    env = hashlib.sha256(runtime().encode("utf-8")).hexdigest()[:16]
    return f"{SCHEMA}-{tree_digest(rev)[:32]}-{cell}-{env}"


def verdict_key(rev: str = "HEAD") -> str:
    """The aggregate verdict `publish.yml` looks for: every FULL cell green on
    this tree, each either run fresh or skipped on its own cell key."""
    return f"{SCHEMA}-{tree_digest(rev)[:32]}-all"


def skips(n: int) -> tuple[int, list[str]]:
    """Of the last `n` non-merge commits, how many share their parent's tree
    digest — i.e. would have found a verdict and skipped FULL."""
    revs = git("rev-list", "--no-merges", f"-{n}", "HEAD").split()
    rows, hit = [], 0
    for rev in revs:
        same = tree_digest(rev) == tree_digest(f"{rev}^")
        hit += same
        rows.append(f"{rev[:8]} {'SKIP' if same else 'run '} {git('log', '-1', '--format=%s', rev).strip()[:70]}")
    return hit, rows


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("tree", "cell", "verdict", "skips"):
        print(__doc__, file=sys.stderr)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "tree":
        print(tree_digest(*rest[:1]))
    elif cmd == "cell":
        if not rest:
            print("cell needs a CELL name", file=sys.stderr)
            return 2
        print(cell_key(rest[0]))
    elif cmd == "verdict":
        print(verdict_key(*rest[:1]))
    else:
        hit, rows = skips(int(rest[0]) if rest else 40)
        print(*rows, sep="\n")
        print(f"would skip FULL: {hit} of {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
