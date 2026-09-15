"""`scripts/commit-paths.py` refuses in both directions — the two-strikes gate.

**The failure class:** a commit on a shared checkout takes work that belongs to
another session, or leaves out a file its own change requires. Recorded twice
in [`work/LESSONS.md`](../work/LESSONS.md), both on 2026-09-15, so
[SR-WORK-SESSION](../records/0060_WORK-session.md) decision 13 owes a
mechanical check.

🔴 **The second occurrence is why the first lesson's rule was not enough.** It
followed *"commit with explicit pathspecs"* exactly — and built the pathspec
list from `git status`, which makes it `git commit -a` with more typing. These
tests are aimed at that shape specifically: a list that covers the whole tree
passes every *explicitness* check and still takes the wrong files.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "commit-paths.py"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=True
    ).stdout


def _run(repo: Path, *args: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=repo, text=True, capture_output=True
    )


@pytest.fixture
def repo(tmp_path):
    """A repo with one commit, then two dirty files — 'mine' and 'theirs'."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t.test")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "seed").write_text("seed\n", encoding="utf-8")
    _git(tmp_path, "add", "seed")
    _git(tmp_path, "commit", "-qm", "seed")

    (tmp_path / "mine.txt").write_text("mine\n", encoding="utf-8")
    (tmp_path / "theirs.txt").write_text("theirs\n", encoding="utf-8")
    # 🔴 **Staged, which is the whole point.** The other session's work is in
    # the shared INDEX, not merely in the worktree — that is what makes
    # `git add X && git commit` take it.
    _git(tmp_path, "add", "theirs.txt")
    return tmp_path


def test_it_refuses_a_path_it_was_not_told_about(repo):
    """Occurrence 1 and 2, in one assertion."""
    done = _run(repo, "-m", "feat: mine", "--", "mine.txt")
    assert done.returncode == 1
    assert "theirs.txt" in done.stderr
    assert "ANOTHER SESSION'S" in done.stderr
    assert _git(repo, "log", "--oneline").count("\n") == 1, "nothing may be committed"


def test_leaving_it_behind_is_allowed_and_said_out_loud(repo):
    done = _run(repo, "-m", "feat: mine", "--leave-behind", "theirs.txt", "--", "mine.txt")
    assert done.returncode == 0, done.stderr
    assert "leaving behind, deliberately" in done.stderr
    files = _git(repo, "show", "--name-only", "--format=", "HEAD").split()
    assert files == ["mine.txt"], "the left-behind path must not ride along"
    assert "theirs.txt" in _git(repo, "diff", "--cached", "--name-only")


def test_a_named_path_that_is_not_dirty_is_refused(repo):
    """The opposite error, from the same tool.

    An explicit pathspec will happily commit LESS than the change needs — a
    record's restamp, most easily — and report success. The working tree stays
    green while HEAD goes red, which is the state `git status` cannot show.
    """
    done = _run(repo, "-m", "feat: mine", "--leave-behind", "theirs.txt",
                "--", "mine.txt", "seed")
    assert done.returncode == 1
    assert "seed" in done.stderr
    assert "not dirty" in done.stderr


def test_a_directory_covers_what_is_under_it(repo):
    """A pathspec is a prefix, so the accounting has to be one too — otherwise
    every run of this tool on a real change is a wall of files under one dir."""
    (repo / "sub").mkdir()
    (repo / "sub" / "a.txt").write_text("a\n", encoding="utf-8")
    (repo / "sub" / "b.txt").write_text("b\n", encoding="utf-8")
    done = _run(repo, "-m", "feat: sub", "--leave-behind", "theirs.txt",
                "--leave-behind", "mine.txt", "--", "sub")
    assert done.returncode == 0, done.stderr
    assert sorted(_git(repo, "show", "--name-only", "--format=", "HEAD").split()) == [
        "sub/a.txt",
        "sub/b.txt",
    ]


def test_a_rename_is_accounted_at_both_ends(repo):
    """One edit to a person, two paths to git.

    Naming only the new path leaves the delete uncommitted and the tree half
    renamed — green locally, broken on a clone.
    """
    _git(repo, "mv", "seed", "renamed")
    done = _run(repo, "-m", "feat: rename", "--leave-behind", "theirs.txt",
                "--leave-behind", "mine.txt", "--", "renamed")
    assert done.returncode == 1
    assert "seed" in done.stderr, "the OLD path must be what it complains about"


def test_the_whole_tree_as_a_pathspec_still_takes_theirs(repo):
    """🔴 **The second occurrence, reproduced.**

    A pathspec list built from `git status` is explicit, complete, accounted
    for — and wrong. This tool cannot refuse it, and the test exists to say so
    rather than to imply a guarantee it does not give: what it buys is that the
    author had to *type* the other session's file, not that they could not.
    """
    done = _run(repo, "-m", "feat: everything", "--", "mine.txt", "theirs.txt")
    assert done.returncode == 0, done.stderr
    files = sorted(_git(repo, "show", "--name-only", "--format=", "HEAD").split())
    assert files == ["mine.txt", "theirs.txt"]
