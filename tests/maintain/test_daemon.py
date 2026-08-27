"""`fux daemon` — the URL freshness clock. W-82 ruling 10 (Arpit, 2026-08-27).

**What these tests are actually guarding**, because a daemon's real failures are
not the ones a unit test usually catches:

| the failure | the test |
|---|---|
| it installs something outside the repo | `test_nothing_is_written_outside_the_repository` |
| it resolves `fux` off `PATH` instead of the project venv | `test_the_spawn_pins_the_interpreter` |
| `stop` escalates to a kill and leaves a partial shard | `test_stop_is_cooperative_and_never_signals` |
| it holds the index lock while idle | `test_the_lock_is_released_between_sweeps` |
| a status surface mutates what it reports (veto 7) | `test_status_never_clears_a_stale_pid_file` |
| it starts itself | `test_setup_and_hooks_never_start_the_daemon` |

⚠ **`serve()` is never run to completion here.** Its loop ends only on a stop,
and a test that let it spin would be a test that hangs on a slow CI arm. The
loop's *parts* are exercised directly instead — which is why `_sweep` and
`stop_requested` are module-level functions rather than closures.
"""

from __future__ import annotations

import inspect
import io
import json
import os
import tokenize

import pytest

from fux.maintain import daemon, hooks, runner


def _code_only(source: str) -> str:
    """The source with every comment and string literal removed.

    ⚠ **Written because the first version of these guards failed on their own
    documentation.** A bare `"systemd" in source` check matched the docstring
    sentence *"no launchd plist, no systemd unit"* — the prose explaining the
    constraint tripped the test enforcing it. A module is then punished for
    documenting itself, and the obvious "fix" is to delete the explanation,
    which is exactly backwards.

    Dropping `COMMENT` and `STRING` tokens leaves only what actually executes,
    which is the only thing these assertions ever meant.
    """
    out = []
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        out.append(tok.string)
    return " ".join(out)


@pytest.fixture
def root(tmp_path):
    (tmp_path / ".fux").mkdir()
    return tmp_path


# -- "inside the project, not globally" -------------------------------------


def test_the_spawn_pins_the_interpreter():
    """Arpit, 2026-08-27: *"the code only lives inside the project, not globally."*

    `sys.executable` is the whole of that. A bare `fux` would resolve against
    whatever `PATH` the shell carries — the exact failure the invocation ladder
    exists for — and would happily start a *different* install's daemon against
    this repo.
    """
    source = inspect.getsource(daemon.start)
    assert "sys.executable" in source
    assert '"-m", "fux.cli"' in source
    # A `fux` argv[0] would mean a PATH lookup.
    assert '["fux"' not in source and "'fux'," not in source


def test_nothing_is_written_outside_the_repository():
    """No launchd plist, no systemd unit, no crontab, no global anything.

    A daemon that registers itself with the OS is the global install this verb
    was specified to avoid, and it would also survive a `git clean` — so the
    repo would no longer describe its own behaviour.
    """
    code = _code_only(inspect.getsource(daemon))
    forbidden = (
        "launchctl", "LaunchAgents", "systemctl", "systemd",
        "crontab", "site-packages", "Startup",
    )
    found = [needle for needle in forbidden if needle in code]
    assert not found, f"daemon.py reaches outside the repo: {found}"


def test_every_path_it_writes_is_inside_the_runtime_plane(root):
    """pid, stop and status all live in gitignored `.fux/runtime/`.

    Nothing the daemon writes may be committed: that is L2 and L3 together, and
    it is why there is no `daemon.toml` anywhere in this feature.
    """
    for path in (daemon.pid_path(root), daemon._stop_path(root), daemon._status_path(root)):
        assert "runtime" in path.parts
        assert path.is_relative_to(root)


# -- the cooperative stop ---------------------------------------------------


def test_stop_is_cooperative_and_never_signals():
    """A signal inside `write_index` can leave a partial shard.

    That is the one path bytes reach a committed shard by, so the stop is a
    file the loop polls, exactly as `runner.py` does it. A `timeout` is
    **reported and not escalated** — this asserts no signalling API is reachable
    from the stop path at all.
    """
    code = _code_only(inspect.getsource(daemon))
    for forbidden in ("os . kill", "SIGTERM", "SIGKILL", "terminate", "signal"):
        assert forbidden not in code, f"the stop escalated to {forbidden}"


def test_stop_on_a_dead_repo_is_not_an_error(root):
    assert daemon.stop(root) == "not-running"


def test_a_stop_names_its_target_pid(root):
    """A stop aimed at a daemon that already exited must never kill the next one.

    Without the pid, `start` right after `stop` would race a stale stop file and
    the new daemon would exit on its first poll — a restart that silently does
    nothing.
    """
    runtime = root / ".fux" / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / daemon.STOP_NAME).write_text(json.dumps({"pid": 999999}), encoding="utf-8")

    assert daemon.stop_requested(root, 999999) is True
    assert daemon.stop_requested(root, os.getpid()) is False


def test_start_clears_a_stale_stop_file(root):
    """The restart bug this prevents: `stop` then `start` and nothing runs."""
    runtime = root / ".fux" / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / daemon.STOP_NAME).write_text(json.dumps({"pid": 1}), encoding="utf-8")

    source = inspect.getsource(daemon.start)
    assert "_clear_stop" in source


# -- the lock, and the second writer ----------------------------------------


def test_it_takes_the_runner_lock_not_its_own(root):
    """Arpit ruled the daemon writes `.fux/index/` directly, so it is a SECOND
    writer — and two locks guarding one resource is not locking.

    It must be `runner.acquire`, the same `O_CREAT|O_EXCL` file the one-shot
    runner uses.
    """
    source = inspect.getsource(daemon._sweep)
    assert "runner.acquire" in source
    assert "runner.release" in source
    assert daemon.__dict__.get("LOCK_NAME") is None, "the daemon defined a second lock"


def test_the_lock_is_released_between_sweeps():
    """Held across an hour-long sleep, it would block every `fux ingest` in the
    repository for an hour. The release is in a `finally`, so a failed sweep
    releases too."""
    source = inspect.getsource(daemon._sweep)
    assert "finally:" in source
    sleep_source = inspect.getsource(daemon.serve)
    # The sleep must sit OUTSIDE _sweep, which is what makes the release land
    # before the wait rather than after it.
    assert "time.sleep" in sleep_source
    assert "time.sleep" not in source


def test_a_busy_lock_is_not_a_failure(root, monkeypatch):
    """A human's `fux ingest` outranks a clock. The sweep comes round again."""
    monkeypatch.setattr(runner, "acquire", lambda _root: False)
    assert daemon._sweep(root) == "busy"


def test_one_bad_sweep_does_not_end_the_daemon(root, monkeypatch):
    """A dev server that dies on one failed request is not a dev server."""
    monkeypatch.setattr(runner, "acquire", lambda _root: True)
    monkeypatch.setattr(runner, "release", lambda _root: None)

    def _boom(*_a, **_k):
        raise RuntimeError("the network went away")

    # ⚠ `import fux.ingest.run as X` binds the re-exported FUNCTION, not the
    # module, because `fux/ingest/__init__.py` exports `run` under the same
    # name. This test therefore patched a function object's attribute and
    # raised `AttributeError` on the patch line itself — so it never once
    # exercised the failing-sweep path it is named for.
    from importlib import import_module

    ingest_run = import_module("fux.ingest.run")

    monkeypatch.setattr(ingest_run, "run", _boom)
    assert daemon._sweep(root) == "failed"


# -- status is read-only (ADR-MAINTENANCE veto 7) ---------------------------


def test_status_never_clears_a_stale_pid_file(root):
    """Veto 7: a status surface that mutates what it reports is the defect.

    A pid file whose process is gone reads as *not running* and is **left on
    disk** for `fux doctor` to name.
    """
    runtime = root / ".fux" / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    pid_file = runtime / daemon.PID_NAME
    pid_file.write_text(json.dumps({"pid": 999999}), encoding="utf-8")

    assert daemon.live_pid(root) is None
    assert daemon.status(root)["running"] is False
    assert pid_file.exists(), "status deleted the file it was reporting on (veto 7)"


def test_a_corrupt_pid_file_reads_as_not_running(root):
    runtime = root / ".fux" / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / daemon.PID_NAME).write_text("{not json", encoding="utf-8")
    assert daemon.live_pid(root) is None


# -- it never starts itself -------------------------------------------------


def test_setup_and_hooks_never_start_the_daemon():
    """The L4 consent is the whole answer to ADR-MAINTENANCE veto 6.

    `maintenance-trigger` rejected an always-on process because it had no
    moment of choosing. This one is chosen — and stops being chosen the instant
    something else starts it for you.
    """
    import fux.setup as setup_mod

    for module in (setup_mod, hooks):
        source = inspect.getsource(module)
        code = _code_only(source)
        assert "daemon" not in code.lower(), (
            f"{module.__name__} mentions the daemon — nothing may start it but a human"
        )


@pytest.mark.parametrize("name", sorted(hooks.HOOKS))
def test_no_hook_starts_the_daemon(name):
    assert "daemon" not in hooks.HOOKS[name]


# -- cadence ----------------------------------------------------------------


def test_sweep_minutes_falls_back_when_there_is_no_config(root):
    assert daemon.sweep_minutes(root) == daemon.DEFAULT_SWEEP_MINUTES


def test_the_default_is_shared_with_config():
    """Two constants drifting apart is how a documented default stops being the
    real one."""
    from fux.config import DEFAULT_SWEEP_MINUTES

    assert daemon.DEFAULT_SWEEP_MINUTES == DEFAULT_SWEEP_MINUTES
