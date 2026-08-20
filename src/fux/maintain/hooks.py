"""Git hooks and the merge-driver wiring — `fux hooks`.

## Which hook, and why not `pre-commit`

**`post-commit` re-indexes, `post-merge` re-indexes, `post-checkout` rebuilds
the derived plane.** The interesting choice is the first one, and the rejected
alternative is `pre-commit`.

`pre-commit` looks better: it would re-index and stage the index inside the
same commit, so the committed index and the committed content would always
agree. **It reads the working tree, not the staged tree.** With `git add -p`,
or with any unstaged edit sitting beside a staged one, a pre-commit hook
indexes bytes that are not being committed — and writes that index *into* the
commit. The result is an index that describes a state no commit ever had, which
is worse than an index that is one commit behind, because it is wrong rather
than late.

The usual workaround is `git stash --keep-index` around the hook. It is
fragile, it loses work when it fails, and losing a user's uncommitted edits to
keep an index tidy is not a trade this project makes.

So: **the committed index lags by at most one commit, and that lag is visible**
— `fux doctor` reports a stale index, and the hook prints what changed. Late
and honest beats current and wrong.

## The hooks chain rather than clobber

An existing hook is **never overwritten**. If one is present and was not
written by fux, installation refuses and says so: silently replacing a repo's
`post-commit` is how a team loses their own tooling to a tool they installed to
help.

## Nothing here is committed to the consumer's repo

`.git/hooks/` is not tracked by git, by design, so a hook cannot arrive with a
clone. That is a property of git and not something to route around — a tool
that installed itself on clone would be executing code a reviewer never saw.
`fux doctor` reports when hooks are absent; installing them stays a decision.
"""

from __future__ import annotations

import stat
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from ..errors import FuxError

__all__ = ["install", "status", "uninstall", "HOOKS", "MERGE_DRIVER_NAME"]

MERGE_DRIVER_NAME = "fux-index"

#: The marker that says fux wrote this file. Its absence on an existing hook is
#: what makes installation refuse rather than clobber.
MARKER = "# installed by `fux hooks --install`"

_PREAMBLE = f"""#!/bin/sh
{MARKER} — safe to delete, or run `fux hooks --uninstall`
#
# Re-indexing is best-effort: a hook that fails must never block a commit, a
# merge or a checkout. It reports and gets out of the way.
set -u
command -v fux >/dev/null 2>&1 || exit 0
"""

HOOKS: dict[str, str] = {
    # The committed index is derived from the COMMITTED tree, which is why this
    # runs after the commit rather than before it. See the module docstring.
    "post-commit": _PREAMBLE + """
fux ingest 2>&1 | sed 's/^/fux: /' || exit 0
if ! git diff --quiet -- .fux/index 2>/dev/null; then
  echo "fux: the index changed — commit .fux/index to keep it in step"
fi
""",
    # A merge brings in both content and (possibly merge-driver-resolved) index
    # lines. Re-ingesting derives the index from the merged CONTENT, which is
    # the authority; it also repairs anything the driver had to refuse.
    "post-merge": _PREAMBLE + """
fux ingest 2>&1 | sed 's/^/fux: /' || exit 0
""",
    # A checkout changes which committed index is present. Nothing needs
    # re-deriving from content — only the gitignored runtime plane.
    "post-checkout": _PREAMBLE + """
fux build >/dev/null 2>&1 || exit 0
""",
}


@dataclass
class HookReport:
    installed: list[str] = field(default_factory=list)
    kept: list[str] = field(default_factory=list)
    refused: list[str] = field(default_factory=list)
    merge_driver: str = ""


def _hooks_dir(root: Path) -> Path:
    """`.git/hooks`, resolving a worktree's `.git` file to its real gitdir."""
    dot_git = root / ".git"
    if dot_git.is_file():  # a worktree or submodule: `.git` is a pointer
        text = dot_git.read_text(encoding="utf-8").strip()
        if not text.startswith("gitdir:"):
            raise FuxError(f"{dot_git} is a file but not a gitdir pointer")
        dot_git = Path(text.split(":", 1)[1].strip())
        if not dot_git.is_absolute():
            dot_git = (root / dot_git).resolve()
    if not dot_git.is_dir():
        raise FuxError(f"no git repository at {root} — hooks need one")
    return dot_git / "hooks"


def install(root: Path) -> HookReport:
    """Write the three hooks and register the merge driver. Never clobbers."""
    report = HookReport()
    directory = _hooks_dir(root)
    directory.mkdir(parents=True, exist_ok=True)

    for name, body in HOOKS.items():
        path = directory / name
        if path.exists():
            existing = path.read_text(encoding="utf-8", errors="replace")
            if MARKER not in existing:
                report.refused.append(name)
                continue
            if existing == body:
                report.kept.append(name)
                continue
        path.write_text(body, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        report.installed.append(name)

    report.merge_driver = _register_merge_driver(root)
    _write_gitattributes(root)
    return report


def _register_merge_driver(root: Path) -> str:
    """`git config merge.fux-index.driver` — local to this repo, never global."""
    command = "fux-merge-index %O %A %B"
    for key, value in (
        (f"merge.{MERGE_DRIVER_NAME}.name", "fux index: line-wise last-writer-wins on (ver, sha)"),
        (f"merge.{MERGE_DRIVER_NAME}.driver", command),
    ):
        result = subprocess.run(
            ["git", "config", "--local", key, value], cwd=root, capture_output=True, text=True
        )
        if result.returncode != 0:
            raise FuxError(f"git config {key} failed: {result.stderr.strip()}")
    return command


def _write_gitattributes(root: Path) -> None:
    """Add the driver line to `.gitattributes`, write-if-missing per line.

    Appends rather than rewrites: `.gitattributes` is the consumer's file and
    frequently already says things about their own tree.
    """
    path = root / ".gitattributes"
    line = f".fux/index/*.jsonl merge={MERGE_DRIVER_NAME}"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if line in existing:
        return
    prefix = "" if not existing or existing.endswith("\n") else "\n"
    path.write_text(
        existing + prefix + "\n# fux: the committed index merges line by line, never textually.\n"
        + line + "\n",
        encoding="utf-8",
    )


def status(root: Path) -> dict:
    directory = _hooks_dir(root)
    driver = subprocess.run(
        ["git", "config", "--local", "--get", f"merge.{MERGE_DRIVER_NAME}.driver"],
        cwd=root, capture_output=True, text=True,
    ).stdout.strip()
    attributes = (root / ".gitattributes")
    return {
        "hooks": {
            name: (
                "fux"
                if (directory / name).exists()
                and MARKER in (directory / name).read_text(encoding="utf-8", errors="replace")
                else "other" if (directory / name).exists() else "absent"
            )
            for name in HOOKS
        },
        "merge_driver": driver or "unregistered",
        "gitattributes": (
            f"merge={MERGE_DRIVER_NAME}" in attributes.read_text(encoding="utf-8")
            if attributes.exists() else False
        ),
    }


def uninstall(root: Path) -> HookReport:
    """Remove only what fux wrote. A hook it did not write is left alone."""
    report = HookReport()
    directory = _hooks_dir(root)
    for name in HOOKS:
        path = directory / name
        if not path.exists():
            continue
        if MARKER not in path.read_text(encoding="utf-8", errors="replace"):
            report.refused.append(name)
            continue
        path.unlink()
        report.installed.append(name)
    subprocess.run(
        ["git", "config", "--local", "--remove-section", f"merge.{MERGE_DRIVER_NAME}"],
        cwd=root, capture_output=True, text=True,
    )
    return report
