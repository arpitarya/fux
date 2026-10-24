"""W-291: `fux setup` installs the git hooks through the one installer `fux hooks` uses.

Every repo here is a scratch `git init` under `tmp_path` — never this repo.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from fux import setup as setup_mod
from fux.cli import main
from fux.maintain import hooks as hooks_mod

NAMES = ("post-commit", "post-merge", "post-checkout")


def _repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "docs").mkdir()
    return tmp_path


def _hook(root: Path, name: str) -> Path:
    return root / ".git" / "hooks" / name


def test_setup_installs_the_hooks_and_announces_gitattributes(tmp_path, monkeypatch, capsys):
    root = _repo(tmp_path)
    monkeypatch.chdir(root)
    assert main(["setup", "--no-agents"]) == 0
    out = capsys.readouterr().out
    assert all(_hook(root, n).exists() and hooks_mod.MARKER in _hook(root, n).read_text() for n in NAMES)
    assert "merge=fux-index" in (root / ".gitattributes").read_text()
    assert ".gitattributes" in out and "OUTSIDE .fux/" in out


def test_setup_runs_the_same_installer_as_fux_hooks(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    monkeypatch.chdir(root)
    calls = []
    real = hooks_mod.install
    monkeypatch.setattr(hooks_mod, "install", lambda r: calls.append(r) or real(r))
    main(["setup", "--no-agents"])
    assert calls == [root]


def test_no_hooks_skips_everything(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    monkeypatch.chdir(root)
    assert main(["setup", "--no-agents", "--no-hooks"]) == 0
    assert not any(_hook(root, n).exists() for n in NAMES)
    assert not (root / ".gitattributes").exists()


def test_no_git_repository_is_one_line_and_exit_zero(tmp_path, monkeypatch, capsys):
    (tmp_path / "docs").mkdir()
    monkeypatch.chdir(tmp_path)
    assert main(["setup", "--no-agents"]) == 0
    assert "no git repository - run `fux hooks` after `git init`" in capsys.readouterr().out
    assert not (tmp_path / ".gitattributes").exists()


def test_a_foreign_hook_is_kept_and_named(tmp_path, monkeypatch, capsys):
    root = _repo(tmp_path)
    mine = _hook(root, "post-commit")
    mine.parent.mkdir(parents=True, exist_ok=True)
    mine.write_text("#!/bin/sh\necho theirs\n", encoding="utf-8")
    monkeypatch.chdir(root)
    assert main(["setup", "--no-agents"]) == 0
    assert "kept (yours) post-commit" in capsys.readouterr().out
    assert mine.read_text() == "#!/bin/sh\necho theirs\n"
    assert hooks_mod.MARKER in _hook(root, "post-merge").read_text()


def test_a_second_setup_changes_nothing_but_repins_our_own(tmp_path, monkeypatch, capsys):
    root = _repo(tmp_path)
    monkeypatch.chdir(root)
    main(["setup", "--no-agents"])
    capsys.readouterr()
    before = {n: _hook(root, n).read_bytes() for n in NAMES}
    attributes = (root / ".gitattributes").read_bytes()
    assert main(["setup", "--no-agents"]) == 0
    out = capsys.readouterr().out
    assert {n: _hook(root, n).read_bytes() for n in NAMES} == before
    assert (root / ".gitattributes").read_bytes() == attributes
    assert "OUTSIDE .fux/" not in out


def test_setup_never_starts_the_daemon(tmp_path, monkeypatch):
    from fux.maintain import daemon as daemon_mod

    root = _repo(tmp_path)
    monkeypatch.chdir(root)

    def boom(*a, **k):
        raise AssertionError("setup must not start the daemon")

    monkeypatch.setattr(daemon_mod, "start", boom)
    assert main(["setup", "--no-agents"]) == 0


def test_the_installed_hooks_never_fetch():
    """Decision 5a: setup installs the same bodies, which run --no-fetch."""
    assert "--no-fetch" in hooks_mod.HOOKS["post-merge"]
