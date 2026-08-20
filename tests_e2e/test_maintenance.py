"""M5 through the real CLI and real git: hooks, and the merge driver.

The load-bearing test is `test_the_driver_resolves_what_git_cannot`: it runs
the *same* merge twice, once without the driver and once with, and asserts git
conflicts in the first case. Without that control the driver could be doing
nothing and the test would still pass.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

DRIVER = shutil.which("fux-merge-index")


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=check)


def fux(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "fux.cli", *args], cwd=cwd, capture_output=True, text=True
    )


def doc(text: str) -> str:
    return f"---\ntitle: {text}\n---\n# {text}\n\n{text} body\n"


def make_repo(path: Path, *, hooks: bool) -> str:
    (path / ".fux" / "sources").mkdir(parents=True)
    (path / "docs").mkdir()
    (path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (path / ".fux" / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    # aa.md and gr.md land in the SAME shard, so an edit to each produces
    # adjacent changed lines — which is exactly what a textual merge cannot do.
    (path / "docs" / "aa.md").write_text(doc("aa one"), encoding="utf-8")
    (path / "docs" / "gr.md").write_text(doc("gr one"), encoding="utf-8")

    git(path, "init", "-q")
    git(path, "config", "user.email", "t@t.test")
    git(path, "config", "user.name", "T")
    # The developer's global config may sign commits; a fixture repo must not
    # depend on gpg being reachable (one test deliberately shrinks PATH).
    git(path, "config", "commit.gpgsign", "false")
    fux(path, "ingest")
    if hooks:
        fux(path, "hooks")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "init")
    return git(path, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def diverge(path: Path, base: str) -> None:
    """Two branches, each editing a different record in the same shard."""
    git(path, "checkout", "-qb", "x")
    (path / "docs" / "aa.md").write_text(doc("aa TWO"), encoding="utf-8")
    fux(path, "ingest")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "x")

    git(path, "checkout", "-q", base)
    git(path, "checkout", "-qb", "y")
    (path / "docs" / "gr.md").write_text(doc("gr TWO"), encoding="utf-8")
    fux(path, "ingest")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "y")


@pytest.mark.skipif(DRIVER is None, reason="fux-merge-index not on PATH (editable install needed)")
def test_the_driver_resolves_what_git_cannot(tmp_path):
    """The control and the treatment, same scenario."""
    plain = tmp_path / "plain"
    plain.mkdir()
    base = make_repo(plain, hooks=False)
    diverge(plain, base)
    conflicted = git(plain, "merge", "x", "-m", "merge", check=False)
    assert conflicted.returncode != 0, "control: git should conflict without the driver"
    assert "CONFLICT" in conflicted.stdout

    wired = tmp_path / "wired"
    wired.mkdir()
    base = make_repo(wired, hooks=True)
    diverge(wired, base)
    merged = git(wired, "merge", "x", "-m", "merge", check=False)
    assert merged.returncode == 0, f"treatment: the driver should resolve it\n{merged.stdout}"

    shard = next((wired / ".fux" / "index").glob("*.jsonl"))
    records = [json.loads(l) for l in shard.read_text().splitlines()[1:]]
    by_id = {r["id"]: r for r in records}
    # BOTH sides' work survives, each at the ver its own edit produced.
    assert by_id["file:docs/aa.md"]["ver"] == 2
    assert by_id["file:docs/gr.md"]["ver"] == 2


def test_hooks_install_and_report_their_state(tmp_path):
    base = make_repo(tmp_path, hooks=False)
    assert base
    out = fux(tmp_path, "hooks").stdout
    assert "post-commit" in out and "merge driver registered" in out

    state = json.loads(fux(tmp_path, "hooks", "--json").stdout)
    assert state["hooks"] == {"post-commit": "fux", "post-merge": "fux", "post-checkout": "fux"}
    assert state["gitattributes"] is True


def test_hooks_refuse_to_clobber_an_existing_hook(tmp_path):
    make_repo(tmp_path, hooks=False)
    theirs = tmp_path / ".git" / "hooks" / "post-commit"
    theirs.parent.mkdir(parents=True, exist_ok=True)
    theirs.write_text("#!/bin/sh\necho ours\n", encoding="utf-8")

    out = fux(tmp_path, "hooks").stdout
    assert "REFUSED post-commit" in out
    assert theirs.read_text() == "#!/bin/sh\necho ours\n"


def test_uninstall_leaves_a_foreign_hook_alone(tmp_path):
    make_repo(tmp_path, hooks=True)
    theirs = tmp_path / ".git" / "hooks" / "post-commit"
    theirs.write_text("#!/bin/sh\necho ours\n", encoding="utf-8")

    out = fux(tmp_path, "hooks", "--uninstall").stdout
    assert "kept    post-commit" in out
    assert theirs.exists()
    assert not (tmp_path / ".git" / "hooks" / "post-merge").exists()


def test_the_post_commit_hook_reindexes_after_a_commit(tmp_path):
    """The lag is one commit, and the hook says so rather than hiding it."""
    make_repo(tmp_path, hooks=True)
    env = dict(os.environ, PATH=f"{Path(sys.executable).parent}{os.pathsep}{os.environ['PATH']}")

    (tmp_path / "docs" / "new.md").write_text(doc("brandnewterm"), encoding="utf-8")
    git(tmp_path, "add", "-A")
    committed = subprocess.run(
        ["git", "commit", "-m", "add new"], cwd=tmp_path, capture_output=True, text=True, env=env
    )
    assert committed.returncode == 0, "a hook must never block a commit"

    found = fux(tmp_path, "find", "brandnewterm", "--json").stdout
    assert "new.md" in found, "post-commit should have re-indexed the committed tree"


def test_a_hook_never_blocks_a_commit_even_when_fux_is_absent(tmp_path):
    """`command -v fux || exit 0` — asserted by running with an empty PATH."""
    make_repo(tmp_path, hooks=True)
    (tmp_path / "docs" / "x.md").write_text(doc("x"), encoding="utf-8")
    git(tmp_path, "add", "-A")
    result = subprocess.run(
        ["git", "commit", "-m", "no fux on path"],
        cwd=tmp_path, capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin", "HOME": os.environ.get("HOME", "")},
    )
    assert result.returncode == 0, result.stderr
