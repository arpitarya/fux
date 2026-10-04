"""Walk this repository from its root without entering the sealed key's tree.

🔴 **W-244 (L11 decision 9).** Seven repo tests walked the root with
`ROOT.rglob(...)` and dropped unwanted paths AFTER the walk had listed them. On
2026-10-03 the same shape in `fux ingest` listed `work/golden/`, the sealed
answer key's parent, while the tree was LOCKED. Filtering the output does not
stop a walk reading, and no hook sees a walk a program does on its own, so the
directory is **never entered**: `os.walk` drops it from descent before listing
it.

`tests/test_walks_skip_golden.py` fails when a test walks the root or `work/`
any other way.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Repo-relative directories no test walk enters (ruled 2026-10-03, W-244).
NEVER_ENTER = frozenset({"work/golden"})


def _walk(root: Path, start: "str | None", skip_parts: frozenset):
    top = root if start is None else root / start
    for dirpath, dirnames, filenames in os.walk(top):
        here = Path(dirpath)
        rel = here.relative_to(root).as_posix()
        keep = []
        for name in dirnames:
            child = name if rel == "." else f"{rel}/{name}"
            if child in NEVER_ENTER or name in skip_parts:
                continue
            keep.append(name)
        dirnames[:] = sorted(keep)
        yield here, dirnames, sorted(filenames)


def repo_files(
    root: Path = ROOT,
    *,
    start: "str | None" = None,
    suffixes: "tuple[str, ...] | None" = None,
    skip_parts=frozenset(),
):
    """Every file under `root` (or `root/start`), with `suffixes` if given."""
    for here, _, filenames in _walk(root, start, frozenset(skip_parts)):
        for name in filenames:
            if suffixes is None or name.endswith(suffixes):
                yield here / name


def repo_dirs(name: str, root: Path = ROOT, *, skip_parts=frozenset()):
    """Every directory called `name` under `root`."""
    for here, dirnames, _ in _walk(root, None, frozenset(skip_parts)):
        for child in dirnames:
            if child == name:
                yield here / child
