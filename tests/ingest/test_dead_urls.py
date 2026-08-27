"""W-82 fork 8 — a dead URL is named by `update`, not only by `doctor`.

**The gap:** every failed fetch already prints as a skip with a reason, so a
URL dead for three weeks reads exactly like one that blipped once. The streak
that tells them apart was visible only to whoever thought to run `fux doctor`.
"""

from __future__ import annotations

import pytest

from importlib import import_module

from fux.maintain import urlstate

# ⚠ `from fux.ingest import run` gives the FUNCTION `fux.ingest.run`, not the
# module `fux.ingest.run` — the package re-exports a callable of the same name
# and it shadows the submodule. `import_module` is unambiguous.
run_mod = import_module("fux.ingest.run")

URL = "https://wiki.corp/handbook"


def _repo(tmp_path):
    (tmp_path / "fux.toml").write_text("[fux]\nversion = 1\n", encoding="utf-8")
    return tmp_path


def _fail_n_runs(root, url, n):
    """Drive the real observer, so the streak is the one the engine computes."""
    for _ in range(n):
        urlstate.observe(root, fetched={}, failed=[url], listed={url})


def test_a_single_failure_is_not_announced(tmp_path, capsys):
    """One failure is a flaky network. The skip line already covers it, and a
    second warning on every blip is how people learn to ignore warnings."""
    root = _repo(tmp_path)
    _fail_n_runs(root, URL, 1)
    run_mod._report_dead_urls(root, [URL])
    assert URL not in capsys.readouterr().err


def test_the_streak_is_announced_once_it_reaches_the_bar(tmp_path, capsys):
    root = _repo(tmp_path)
    _fail_n_runs(root, URL, urlstate.FAILING_STREAK)
    run_mod._report_dead_urls(root, [URL])
    err = capsys.readouterr().err
    assert URL in err
    assert f"failed {urlstate.FAILING_STREAK} runs in a row" in err


def test_it_says_what_to_do_about_it(tmp_path, capsys):
    """A warning that names a problem and no action is a warning people skip."""
    root = _repo(tmp_path)
    _fail_n_runs(root, URL, urlstate.FAILING_STREAK)
    run_mod._report_dead_urls(root, [URL])
    assert f"fux remove {URL}" in capsys.readouterr().err


def test_it_goes_to_stderr_never_stdout(tmp_path, capsys):
    """The query plane's standing contract: declarations never touch stdout."""
    root = _repo(tmp_path)
    _fail_n_runs(root, URL, urlstate.FAILING_STREAK)
    run_mod._report_dead_urls(root, [URL])
    captured = capsys.readouterr()
    assert captured.out == ""
    assert URL in captured.err


def test_a_url_that_did_not_fail_this_run_is_not_reported(tmp_path, capsys):
    """⚠ Only URLs that failed THIS run are considered.

    A success resets the streak, so a URL that succeeded cannot be dead — and
    walking the whole state would re-report URLs this run never touched.
    """
    root = _repo(tmp_path)
    _fail_n_runs(root, URL, urlstate.FAILING_STREAK)
    run_mod._report_dead_urls(root, [])
    assert capsys.readouterr().err == ""


def test_a_recovered_url_stops_being_reported(tmp_path, capsys):
    root = _repo(tmp_path)
    _fail_n_runs(root, URL, urlstate.FAILING_STREAK)
    urlstate.observe(root, fetched={URL: "a" * 40}, failed=[], listed={URL})
    run_mod._report_dead_urls(root, [URL])
    assert capsys.readouterr().err == "", "a success resets the streak"


def test_it_never_raises_when_the_state_is_unreadable(tmp_path, capsys):
    """Best-effort, like everything on this plane: a report must never be able
    to fail an ingest that otherwise succeeded."""
    root = _repo(tmp_path)
    _fail_n_runs(root, URL, urlstate.FAILING_STREAK)
    (root / ".fux" / "runtime" / urlstate.STATE_NAME).write_text("{ not json", encoding="utf-8")
    run_mod._report_dead_urls(root, [URL])  # must not raise
    assert capsys.readouterr().err == ""


def test_sys_is_actually_imported_by_the_module():
    """⚠ **Found by reading, after the import check passed.**

    `_report_dead_urls` writes to `sys.stderr`, and `run.py` did not import
    `sys`. `import fux.ingest.run` still succeeded, because the reference is
    inside a function body — so the module imported cleanly and would have
    raised `NameError` the first time a URL actually went dead. The same shape
    as the `find_root` defect in `cli.py` an hour earlier.
    """
    import inspect

    source = inspect.getsource(run_mod)
    assert "\nimport sys\n" in source, "run.py uses sys.stderr and must import sys"


@pytest.mark.parametrize("streak", [1, 2, 3, 4])
def test_below_the_bar_stays_quiet(tmp_path, capsys, streak):
    root = _repo(tmp_path)
    _fail_n_runs(root, URL, streak)
    run_mod._report_dead_urls(root, [URL])
    assert capsys.readouterr().err == ""
