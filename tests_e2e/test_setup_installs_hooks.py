"""W-291 through the real CLI and real git: `fux setup` installs the hooks.

A fresh `git init` scratch repo (never this one), `fux setup`, then a commit —
and the hook it installed re-indexes. The unit half is `tests/test_setup_hooks.py`.
"""

from __future__ import annotations

import subprocess

from test_maintenance import _drain, _hook_env, doc, fux, git


def _scratch(path):
    git(path, "init", "-q")
    git(path, "config", "user.email", "t@t.test")
    git(path, "config", "user.name", "T")
    git(path, "config", "commit.gpgsign", "false")
    (path / "docs").mkdir()
    (path / "docs" / "aa.md").write_text(doc("aa one"), encoding="utf-8")


def test_setup_wires_the_hooks_and_a_commit_re_indexes(tmp_path):
    _scratch(tmp_path)
    done = fux(tmp_path, "setup", "--no-agents")
    assert done.returncode == 0, done.stderr
    assert "post-commit" in done.stdout and ".gitattributes" in done.stdout
    state = fux(tmp_path, "hooks", "--status").stdout
    for name in ("post-commit", "post-merge", "post-checkout"):
        assert f"{name}" in state
    assert "unregistered" not in state and "not wired" not in state

    (tmp_path / ".fux" / "sources.yaml").write_text("paths:\n  include:\n    - docs\n", encoding="utf-8")
    assert fux(tmp_path, "ingest").returncode == 0
    git(tmp_path, "add", "-A")
    subprocess.run(
        ["git", "commit", "-qm", "init"], cwd=tmp_path, capture_output=True, env=_hook_env(), check=True
    )
    assert _drain(tmp_path), "the detached runner never finished"

    (tmp_path / "docs" / "new.md").write_text(doc("setuphookterm"), encoding="utf-8")
    git(tmp_path, "add", "-A")
    committed = subprocess.run(
        ["git", "commit", "-qm", "add new"], cwd=tmp_path, capture_output=True, text=True,
        encoding="utf-8", env=_hook_env(),
    )
    assert committed.returncode == 0
    assert _drain(tmp_path), "the detached runner never finished"
    assert "new.md" in fux(tmp_path, "find", "setuphookterm", "--json").stdout


def test_setup_no_hooks_installs_nothing(tmp_path):
    _scratch(tmp_path)
    assert fux(tmp_path, "setup", "--no-agents", "--no-hooks").returncode == 0
    assert not (tmp_path / ".git" / "hooks" / "post-commit").exists()
    assert not (tmp_path / ".gitattributes").exists()


def test_setup_without_git_exits_zero_with_the_one_line(tmp_path):
    (tmp_path / "docs").mkdir()
    done = fux(tmp_path, "setup", "--no-agents")
    assert done.returncode == 0, done.stderr
    assert "no git repository - run `fux hooks` after `git init`" in done.stdout
