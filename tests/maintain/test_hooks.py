"""`fux hooks` — wires a repository up, and never clobbers what it did not write."""

from __future__ import annotations

import subprocess
import sys

import pytest

from fux.errors import FuxError
from fux.maintain import hooks


def _git(tmp_path, *args) -> str:
    return subprocess.run(
        ["git", *args], cwd=tmp_path, capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    return tmp_path


# -- installation -----------------------------------------------------------


def test_install_writes_all_three_hooks_executable(repo):
    report = hooks.install(repo)
    assert sorted(report.installed) == ["post-checkout", "post-commit", "post-merge"]
    for name in hooks.HOOKS:
        path = repo / ".git" / "hooks" / name
        assert path.exists(), name
        # NTFS has no POSIX execute bit — chmod is a no-op for it on Windows,
        # and git-for-windows runs a hook via its shebang regardless.
        if sys.platform != "win32":
            assert path.stat().st_mode & 0o111, name
        assert hooks.MARKER in path.read_text(encoding="utf-8")


def test_install_is_idempotent(repo):
    hooks.install(repo)
    second = hooks.install(repo)
    assert second.installed == [] and sorted(second.kept) == [
        "post-checkout",
        "post-commit",
        "post-merge",
    ]


def test_a_hook_fux_did_not_write_is_refused_not_replaced(repo):
    """Losing a team's own tooling to the tool they installed to help is the bug."""
    theirs = repo / ".git" / "hooks"
    theirs.mkdir(parents=True, exist_ok=True)
    (theirs / "post-commit").write_text("#!/bin/sh\necho mine\n", encoding="utf-8")

    report = hooks.install(repo)
    assert report.refused == ["post-commit"]
    assert (theirs / "post-commit").read_text(encoding="utf-8") == "#!/bin/sh\necho mine\n"
    assert "post-merge" in report.installed          # the others still land


def test_a_stale_fux_hook_is_upgraded_in_place(repo):
    path = repo / ".git" / "hooks"
    path.mkdir(parents=True, exist_ok=True)
    (path / "post-commit").write_text(hooks.MARKER + "\n# an older body\n", encoding="utf-8")
    report = hooks.install(repo)
    assert "post-commit" in report.installed
    assert (path / "post-commit").read_text(encoding="utf-8") == hooks.HOOKS["post-commit"]


def test_no_hook_can_block_the_operation_it_follows(repo):
    """Every hook body exits 0 on a fux that is missing or failing."""
    for name, body in hooks.HOOKS.items():
        assert "command -v fux" in body, name
        assert "exit 0" in body, name


def test_pre_commit_is_deliberately_not_installed(repo):
    """It reads the working tree, not the staged tree — see the module docstring."""
    hooks.install(repo)
    assert not (repo / ".git" / "hooks" / "pre-commit").exists()


# -- the merge driver wiring ------------------------------------------------


def test_install_registers_the_merge_driver_locally(repo):
    hooks.install(repo)
    driver = _git(repo, "config", "--local", "--get", f"merge.{hooks.MERGE_DRIVER_NAME}.driver")
    assert driver == "fux-merge-index %O %A %B"


def test_install_wires_gitattributes_and_keeps_what_was_there(repo):
    (repo / ".gitattributes").write_text("*.png binary\n", encoding="utf-8")
    hooks.install(repo)
    text = (repo / ".gitattributes").read_text(encoding="utf-8")
    assert "*.png binary" in text
    assert f".fux/index/*.jsonl merge={hooks.MERGE_DRIVER_NAME}" in text


def test_gitattributes_is_not_appended_to_twice(repo):
    hooks.install(repo)
    hooks.install(repo)
    text = (repo / ".gitattributes").read_text(encoding="utf-8")
    assert text.count(f"merge={hooks.MERGE_DRIVER_NAME}") == 1


# -- status and uninstall ---------------------------------------------------


def test_status_reports_absent_then_fux_then_other(repo):
    assert hooks.status(repo)["hooks"]["post-commit"] == "absent"
    assert hooks.status(repo)["merge_driver"] == "unregistered"

    hooks.install(repo)
    state = hooks.status(repo)
    assert state["hooks"]["post-commit"] == "fux"
    assert state["merge_driver"] == "fux-merge-index %O %A %B"
    assert state["gitattributes"] is True

    (repo / ".git" / "hooks" / "post-commit").write_text("#!/bin/sh\n", encoding="utf-8")
    assert hooks.status(repo)["hooks"]["post-commit"] == "other"


def test_uninstall_removes_only_what_fux_wrote(repo):
    hooks.install(repo)
    (repo / ".git" / "hooks" / "post-merge").write_text("#!/bin/sh\nmine\n", encoding="utf-8")

    report = hooks.uninstall(repo)
    assert sorted(report.installed) == ["post-checkout", "post-commit"]
    assert report.refused == ["post-merge"]
    assert (repo / ".git" / "hooks" / "post-merge").exists()
    assert hooks.status(repo)["merge_driver"] == "unregistered"


def test_uninstall_leaves_gitattributes_alone(repo):
    """It is the consumer's file; a tool that edits it on the way out is rude."""
    hooks.install(repo)
    hooks.uninstall(repo)
    assert f"merge={hooks.MERGE_DRIVER_NAME}" in (repo / ".gitattributes").read_text(encoding="utf-8")


# -- worktrees and non-repositories ----------------------------------------


def test_a_worktree_gitdir_pointer_is_followed(repo, tmp_path):
    (repo / "f.txt").write_text("x\n", encoding="utf-8")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "add", "f.txt")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
    linked = tmp_path / "linked"
    _git(repo, "worktree", "add", "-q", str(linked), "-b", "side")

    assert (linked / ".git").is_file()                 # a pointer, not a directory
    report = hooks.install(linked)
    assert sorted(report.installed) == ["post-checkout", "post-commit", "post-merge"]


def test_a_directory_that_is_not_a_repository_is_a_clean_error(tmp_path):
    with pytest.raises(FuxError, match="no git repository"):
        hooks.install(tmp_path)
