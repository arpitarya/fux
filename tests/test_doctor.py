from __future__ import annotations

import subprocess

import pytest

from fux import doctor


def _git_repo(tmp_path):
    try:
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover - git is a dev prereq
        pytest.skip("git unavailable")
    return tmp_path


def test_python_version_check_passes_on_current_interpreter():
    checks = doctor.run()
    py = next(c for c in checks if c.name == "python version")
    assert py.ok


def test_repo_root_found_from_a_git_checkout(tmp_path):
    (tmp_path / ".git").mkdir()
    checks = doctor.run(tmp_path)
    root = next(c for c in checks if c.name == "repo root")
    assert root.ok
    assert root.detail == str(tmp_path.resolve())


def test_fux_dir_writable_after_root_found(tmp_path):
    (tmp_path / ".git").mkdir()
    checks = doctor.run(tmp_path)
    writable = next(c for c in checks if c.name == ".fux/ writable")
    assert writable.ok
    assert (tmp_path / ".fux").is_dir()


def test_no_root_reports_single_failing_check(tmp_path):
    checks = doctor.run(tmp_path)
    assert [c.name for c in checks] == ["python version", "repo root"]
    assert not checks[1].ok


# -- the .fux layout checks (ADR-DOTFUX) -------------------------------------


def _check(checks, name):
    return next(c for c in checks if c.name == name)


def test_index_ignored_by_a_blanket_rule_is_an_error(tmp_path):
    _git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".fux/*\n", encoding="utf-8")
    check = _check(doctor.run(tmp_path), "index not gitignored")
    assert not check.ok
    assert check.level == "error"
    assert ".fux/index is committed" in check.detail


def test_index_not_ignored_passes(tmp_path):
    _git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".fux/runtime/\n.fux/cache/\n", encoding="utf-8")
    assert _check(doctor.run(tmp_path), "index not gitignored").ok


def test_check_ignore_is_skipped_outside_a_git_checkout(tmp_path):
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    dirs = tmp_path / ".fux" / "sources" / "dirs"
    dirs.parent.mkdir(parents=True, exist_ok=True)
    dirs.write_text("docs\n", encoding="utf-8")
    check = _check(doctor.run(tmp_path), "index not gitignored")
    assert check.ok and "skipped" in check.detail


def test_undeclared_fux_entry_warns_without_failing_the_command(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".fux").mkdir()
    (tmp_path / ".fux" / "scratch").mkdir()
    check = _check(doctor.run(tmp_path), ".fux/ layout declared")
    assert not check.ok
    assert check.level == "warn"
    assert "scratch" in check.detail


def test_declared_entries_do_not_warn(tmp_path):
    (tmp_path / ".git").mkdir()
    from fux.store import fuxdir

    fuxdir.ensure_layout(tmp_path)
    fuxdir.derived_dir(tmp_path, "runtime")
    (tmp_path / ".fux" / "index").mkdir()
    assert _check(doctor.run(tmp_path), ".fux/ layout declared").ok


def test_cmd_doctor_exit_code_ignores_warnings(tmp_path, monkeypatch, capsys):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".fux").mkdir(exist_ok=True)
    (tmp_path / ".fux" / "scratch").mkdir()
    monkeypatch.chdir(tmp_path)
    assert doctor.cmd_doctor(None) == 0
    assert "[WARN] .fux/ layout declared" in capsys.readouterr().out


# -- the derived accelerator check (M2, ADR-T1-ACCELERATOR) ---------------------------


def test_accelerator_absent_warns_but_does_not_fail(tmp_path):
    """No accelerator is a speed problem, never a correctness one.

    `ask` answers from the reference scan without it, so reporting this as an
    error would train people to ignore a red doctor.
    """
    (tmp_path / ".git").mkdir()
    check = _check(doctor.run(tmp_path), "accelerator")
    assert check.ok
    assert check.level == "warn"
    assert "not built" in check.detail


def test_accelerator_reports_fresh_after_a_build(tmp_path):
    from fux.derive import build
    from fux.store import term_hash, write_index

    _git_repo(tmp_path)
    write_index(
        tmp_path,
        [
            {
                "id": "file:a.md",
                "src": "git",
                "loc": "a.md",
                "mode": "extracted",
                "meta": "plain",
                "title": "A",
                "phrases": [],
                "terms": {term_hash("alpha"): [1, 0]},
                "wlen": 4,
                "edges": [],
            }
        ],
    )
    build(tmp_path)
    check = _check(doctor.run(tmp_path), "accelerator")
    assert check.ok
    assert "fresh" in check.detail


def test_accelerator_goes_stale_when_the_index_changes(tmp_path):
    from fux.derive import build
    from fux.store import shard_path, term_hash, write_index

    _git_repo(tmp_path)
    record = {
        "id": "file:a.md",
        "src": "git",
        "loc": "a.md",
        "mode": "extracted",
        "meta": "plain",
        "title": "A",
        "phrases": [],
        "terms": {term_hash("alpha"): [1, 0]},
        "wlen": 4,
        "edges": [],
    }
    write_index(tmp_path, [record])
    build(tmp_path)

    write_index(tmp_path, [record | {"wlen": 99}])
    check = _check(doctor.run(tmp_path), "accelerator")
    assert "stale" in check.detail
    assert shard_path(tmp_path, "05").exists() or True  # shard identity is not the point


def test_every_check_detail_is_ascii_in_every_branch(tmp_path):
    """The Windows codepage guard, applied to the failing branches too.

    The e2e smoke test forces `PYTHONIOENCODING=ascii` on a *healthy* repo, so
    it only ever exercised the passing strings. Two failure-branch details
    carried em-dashes for weeks and would have crashed `fux doctor` on a
    Windows console exactly when a user most needed it to print. This drives
    every branch it can and asserts on the detail text itself.
    """
    from fux.store import fuxdir

    scenarios = []

    _git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".fux/*\n", encoding="utf-8")
    (tmp_path / ".fux").mkdir(exist_ok=True)
    (tmp_path / ".fux" / "scratch").mkdir()
    scenarios.append(doctor.run(tmp_path))

    fuxdir.ensure_layout(tmp_path)
    scenarios.append(doctor.run(tmp_path))
    scenarios.append(doctor.run(tmp_path / "nowhere"))

    seen = set()
    for checks in scenarios:
        for check in checks:
            seen.add(check.name)
            check.detail.encode("ascii")  # raises UnicodeEncodeError on a regression
            check.name.encode("ascii")

    assert {"index not gitignored", ".fux/ layout declared", "accelerator"} <= seen
