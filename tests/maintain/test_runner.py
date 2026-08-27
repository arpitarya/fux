"""The deferred runner — W-66 Phase 2: the lock, the cooperative stop, takeover.

Every failure this module guards is silent and rare: two writers in
`.fux/index/`, a stop that leaves a partial shard, a rebase that spawns fifty
runners. None of them raises on the machine that writes them, which is why
they are asserted here rather than trusted.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from fux.errors import FuxError
from fux.maintain import dirty, runner


def _corpus(root: Path, docs: int = 3) -> None:
    listing = root / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("docs\n", encoding="utf-8")
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (root / "docs").mkdir(exist_ok=True)
    for i in range(docs):
        (root / "docs" / f"d{i}.md").write_text(f"# Doc {i}\n\nbody {i} words here\n", encoding="utf-8")


# -- the lock ---------------------------------------------------------------


def test_the_lock_is_exclusive(tmp_path):
    assert runner.acquire(tmp_path) is True
    assert runner.acquire(tmp_path) is False, "two runners must never both hold it"
    runner.release(tmp_path)
    assert runner.acquire(tmp_path) is True


def test_the_lock_records_this_process(tmp_path):
    runner.acquire(tmp_path)
    assert runner.holder(tmp_path) == os.getpid()


def test_no_lock_reads_as_nobody_holding_it(tmp_path):
    assert runner.holder(tmp_path) is None


def test_an_unparseable_lock_reads_as_held_not_free(tmp_path):
    """Treating a lock we cannot parse as "nothing is running" is how two
    runners end up in the index. It reads as held-by-unknown instead."""
    path = tmp_path / ".fux" / "runtime" / runner.LOCK_NAME
    path.parent.mkdir(parents=True)
    path.write_text("not json at all", encoding="utf-8")
    assert runner.holder(tmp_path) == -1
    assert runner.holder(tmp_path) is not None


def test_release_of_a_missing_lock_does_not_raise(tmp_path):
    runner.release(tmp_path)  # a runner exiting must not fail on cleanup


# -- liveness ---------------------------------------------------------------


def test_is_alive_knows_this_process(tmp_path):
    assert runner.is_alive(os.getpid()) is True


def test_is_alive_rejects_nonsense_pids(tmp_path):
    assert runner.is_alive(None) is False
    assert runner.is_alive(0) is False
    assert runner.is_alive(-1) is False


def test_is_alive_on_a_reaped_process_is_false(tmp_path):
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()
    assert runner.is_alive(dead.pid) is False


def test_liveness_never_uses_os_kill_on_windows():
    """`os.kill(pid, 0)` TERMINATES on Windows — CPython routes it through
    `TerminateProcess`. A liveness probe that kills what it probes is the
    exact silent cross-platform failure this phase exists to avoid."""
    import inspect

    source = inspect.getsource(runner.is_alive)
    win_branch = source.split('sys.platform == "win32"', 1)[1].split("try:", 1)[0]
    assert "os.kill" not in win_branch
    assert "OpenProcess" in win_branch


# -- the cooperative stop ---------------------------------------------------


def test_stop_is_only_honoured_by_the_pid_it_names(tmp_path):
    """A stop aimed at a runner that already exited must not kill the next
    one — otherwise a 50-commit rebase indexes nothing."""
    runtime = tmp_path / ".fux" / "runtime"
    runtime.mkdir(parents=True)
    (runtime / "runner.stop").write_text(json.dumps({"pid": 4242}), encoding="utf-8")
    assert runner.stop_requested(tmp_path, 4242) is True
    assert runner.stop_requested(tmp_path, 9999) is False


def test_no_stop_file_means_no_stop(tmp_path):
    assert runner.stop_requested(tmp_path, os.getpid()) is False


def test_request_stop_with_nothing_running_is_idle(tmp_path):
    assert runner.request_stop(tmp_path) == "idle"


def test_request_stop_breaks_a_lock_whose_holder_is_gone(tmp_path):
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()
    runtime = tmp_path / ".fux" / "runtime"
    runtime.mkdir(parents=True)
    (runtime / runner.LOCK_NAME).write_text(json.dumps({"pid": dead.pid}), encoding="utf-8")

    assert runner.request_stop(tmp_path, timeout=0.5) == "stale"
    assert runner.holder(tmp_path) is None


def test_a_live_holder_that_ignores_the_stop_is_wedged_not_broken(tmp_path):
    """The lock is NOT broken here. Breaking a lock whose owner is provably
    alive is the two-writers failure the lock exists to prevent."""
    runtime = tmp_path / ".fux" / "runtime"
    runtime.mkdir(parents=True)
    # This process is alive and will never poll the stop file.
    (runtime / runner.LOCK_NAME).write_text(json.dumps({"pid": os.getpid()}), encoding="utf-8")

    assert runner.request_stop(tmp_path, timeout=0.2) == "wedged"
    assert runner.holder(tmp_path) == os.getpid(), "a wedged lock must survive"


def test_request_stop_clears_its_own_stop_file(tmp_path):
    """A leftover stop file would halt the next runner before it started."""
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()
    runtime = tmp_path / ".fux" / "runtime"
    runtime.mkdir(parents=True)
    (runtime / runner.LOCK_NAME).write_text(json.dumps({"pid": dead.pid}), encoding="utf-8")
    runner.request_stop(tmp_path, timeout=0.5)
    assert not (runtime / "runner.stop").exists()


# -- run_once ---------------------------------------------------------------


def test_run_once_indexes_and_releases(tmp_path):
    _corpus(tmp_path)
    assert runner.run_once(tmp_path) == "ok"
    assert runner.holder(tmp_path) is None, "the lock must not outlive the run"
    assert (tmp_path / ".fux" / "index").exists()


def test_run_once_exits_quietly_when_another_runner_holds_the_lock(tmp_path):
    _corpus(tmp_path)
    runner.acquire(tmp_path)
    assert runner.run_once(tmp_path) == "busy"


def test_run_once_records_its_outcome(tmp_path):
    _corpus(tmp_path)
    runner.run_once(tmp_path)
    assert runner.last_run(tmp_path)["outcome"] == "ok"


def test_run_once_clears_a_stop_aimed_at_a_previous_runner(tmp_path):
    _corpus(tmp_path)
    runtime = tmp_path / ".fux" / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / "runner.stop").write_text(json.dumps({"pid": 4242}), encoding="utf-8")
    assert runner.run_once(tmp_path) == "ok", "a stale stop must not halt a fresh runner"


def test_work_recorded_while_the_lock_was_held_is_not_stranded(tmp_path, monkeypatch):
    """The bug CI found, as a unit test.

    A commit landing while a runner holds the lock has its spawn refused —
    correctly — on the assumption that *"the live runner picks up the
    accumulated list anyway"*. That only holds if the live runner has not yet
    taken its start-time snapshot. If it has, it discards its own snapshot,
    exits, and the newer ids are stranded: no process holds them and no
    further commit is guaranteed to arrive.

    **Every Linux CI arm failed on this while Windows and macOS passed** — the
    race exists on all three, and the slower runner simply lost it more often.
    """
    _corpus(tmp_path)
    real_run = sys.modules["fux.ingest.run"].run
    landed = []

    def run_then_a_commit_lands(root, **kwargs):
        report = real_run(root, **kwargs)
        if not landed:  # exactly once, after the first pass has snapshotted
            landed.append(True)
            dirty.record(root, ["file:docs/late.md"])
        return report

    monkeypatch.setattr(sys.modules["fux.ingest.run"], "run", run_then_a_commit_lands)
    assert runner.run_once(tmp_path) == "ok"
    assert dirty.read(tmp_path) == [], (
        "a runner exited leaving recorded work behind and nobody to do it"
    )


def test_the_redrain_loop_is_bounded(tmp_path, monkeypatch):
    """Veto condition 6: the runner must terminate. A repository committing
    faster than it re-indexes must not keep one process alive forever."""
    _corpus(tmp_path)
    real_run = sys.modules["fux.ingest.run"].run
    passes = []

    def run_and_always_dirty(root, **kwargs):
        passes.append(1)
        report = real_run(root, **kwargs)
        dirty.record(root, [f"file:docs/never-ending-{len(passes)}.md"])
        return report

    monkeypatch.setattr(sys.modules["fux.ingest.run"], "run", run_and_always_dirty)
    assert runner.run_once(tmp_path) == "ok"
    assert len(passes) == runner.MAX_PASSES, "the loop did not stop at MAX_PASSES"
    assert dirty.read(tmp_path), "the leftovers must stay pending for the next spawn to find"
    assert runner.holder(tmp_path) is None, "the runner must still have exited"


def test_a_failed_run_is_recorded_and_still_raises(tmp_path, monkeypatch):
    """A detached process has no stderr anyone reads. Silence is the bug."""
    _corpus(tmp_path)

    def boom(*a, **k):
        raise RuntimeError("disk on fire")

    # Via `sys.modules`, not the dotted string: `fux.ingest.run` resolves to
    # the re-exported *function* in `fux/ingest/__init__.py`, which shadows
    # the module of the same name.
    monkeypatch.setattr(sys.modules["fux.ingest.run"], "run", boom)
    with pytest.raises(RuntimeError):
        runner.run_once(tmp_path)
    assert runner.last_run(tmp_path)["outcome"] == "failed"
    assert "disk on fire" in runner.last_run(tmp_path)["error"]
    assert runner.holder(tmp_path) is None, "a crashed run must still release the lock"


# -- the stop, end to end through ingest.run --------------------------------


def test_a_stopped_run_writes_no_index_and_keeps_the_dirty_list(tmp_path):
    """Veto 8, and the test that says the stop was cooperative, not a kill."""
    from fux.ingest.run import run

    _corpus(tmp_path)
    dirty.record(tmp_path, ["file:docs/d0.md"])

    report = run(tmp_path, should_stop=lambda: True)
    assert report is None
    assert not list((tmp_path / ".fux" / "index").glob("*.jsonl")) if (
        tmp_path / ".fux" / "index"
    ).exists() else True
    assert dirty.read(tmp_path) == ["file:docs/d0.md"], "a stopped run subtracts nothing"


def test_a_completed_run_subtracts_only_its_start_time_snapshot(tmp_path):
    """A commit landing mid-run must survive the run that was already flying."""
    from fux.ingest.run import run

    _corpus(tmp_path)
    dirty.record(tmp_path, ["file:docs/d0.md"])

    landed = []

    def mid_run_commit():
        if not landed:
            landed.append(True)
            dirty.record(tmp_path, ["file:docs/late.md"])
        return False

    run(tmp_path, should_stop=mid_run_commit)
    assert dirty.read(tmp_path) == ["file:docs/late.md"]


def test_run_without_should_stop_can_never_return_none(tmp_path):
    from fux.ingest.run import run

    _corpus(tmp_path)
    assert run(tmp_path) is not None


# -- record_head ------------------------------------------------------------


def _git(root, *args):
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True,
        env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
    )


def test_record_head_captures_the_first_commit(tmp_path):
    """`--root`: without it the very first commit has no parent to diff and
    a fresh repo would record nothing at all."""
    _corpus(tmp_path)
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "first")

    runner.record_head(tmp_path)
    assert "file:docs/d0.md" in dirty.read(tmp_path)


def test_record_head_ignores_fuxs_own_output(tmp_path):
    """Recording `.fux/` would make every re-index dirty the list it drains."""
    _corpus(tmp_path)
    _git(tmp_path, "init", "-q")
    runner.run_once(tmp_path)
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "with an index")

    runner.record_head(tmp_path)
    assert not [i for i in dirty.read(tmp_path) if i.startswith("file:.fux/")]


def test_record_head_outside_a_repo_does_not_raise(tmp_path):
    assert runner.record_head(tmp_path) == 0


# -- the takeover, through the CLI -----------------------------------------


def test_stop_with_nothing_running_exits_zero(tmp_path, monkeypatch, capsys):
    """A verb whose job is "make sure it is not running" has succeeded when
    it was not running (ADR-CLI, 2026-08-22)."""
    from fux.cli import main

    _corpus(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert main(["ingest", "--stop"]) == 0
    assert "no background re-index was running" in capsys.readouterr().out


def test_a_wedged_runner_refuses_the_write_rather_than_racing_it(tmp_path, monkeypatch):
    from fux.ingest import ingest_and_report

    _corpus(tmp_path)
    runtime = tmp_path / ".fux" / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / runner.LOCK_NAME).write_text(json.dumps({"pid": os.getpid()}), encoding="utf-8")
    monkeypatch.setattr(runner, "STOP_TIMEOUT_S", 0.1)

    class Args:
        progress = None

    with pytest.raises(FuxError, match="did not stop when asked"):
        ingest_and_report(tmp_path, Args())
