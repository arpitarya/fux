"""`fux daemon` — the clock that refreshes the tail. W-82 ruling 10 (Arpit, 2026-08-27).

## What it is for, and why the detector was not enough

The detector ([`dirty.py`](dirty.py), W-82 §3.2) notices a changed URL **when
someone retrieves it**: the refer plane fetches a cited document, sees the sha
differ, and records the id. That is usage-weighted freshness for free — but it
only ever covers documents somebody asked about.

**It covers the head. The tail needs a clock, and this is the clock.** A URL
nobody has queried in three months is never cited, never fetched, and nothing
notices it changed. No amount of answer-time verification reaches it, because
verification only runs on documents that ranked.

## The shape Arpit ruled, and every clause of it is load-bearing

> *"like a dev server. `fux daemon start`, so it keeps running, and
> `fux daemon stop` to stop it. The code only lives inside the project, not
> globally."*

| clause | what it forces here |
|---|---|
| **`start` / `stop`** | explicitly begun, explicitly ended. Never auto-started by `fux setup`, install, or a hook |
| **keeps running** | resident — which is what made this need a veto ruling at all |
| **inside the project** | spawned as `sys.executable -m fux.cli`, the interpreter we are already inside. **No launchd plist, no systemd unit, no global binary, nothing written outside the repo** |

⚠ **`sys.executable` is the whole of "inside the project".** A bare `fux` would
resolve against whatever `PATH` the shell happens to carry — which is precisely
the failure the invocation ladder exists for. Pinning the interpreter pins the
`.venv` the caller is already running in.

## ADR-MAINTENANCE veto condition 6, fired and answered

Veto 6 reads: *"The detached runner turns into something always-on — a resident
process, a scheduler, or a watcher."* **This is resident, so the veto is fired
rather than sidestepped**, and the answer is recorded in ADR-MAINTENANCE rather
than argued here. Two facts that made it answerable:

- **This is not the runner.** `runner.py` stays one-shot and still exits;
  `MAX_PASSES` still bounds it. Veto 6's subject — the runner changing shape —
  is untouched.
- **The consent is real.** `maintenance-trigger`'s rejected option C was a
  filesystem watcher that fired on every save, with no moment of choosing. This
  starts because a human typed `start` and stops because a human typed `stop`,
  and `fux daemon status` says whether it is running.

## It writes the index, and that is the expensive half of the ruling

Arpit ruled the daemon **writes `.fux/index/` directly** rather than only
recording ids for the runner to pick up. That makes it a **second writer**, so:

- **It takes `runner.lock`** — the same lock, via the same `runner.acquire`.
  Two writers in `.fux/index/` is the failure that lock exists to prevent, and
  a daemon with its own lock would be two locks guarding one resource.
- **It releases between sweeps, never holds across the sleep.** Holding the
  lock while idle would block every `fux ingest` for an hour at a time.
- **The stop is cooperative and is never a kill.** A signal delivered inside
  `write_index` can leave a partial shard — the one path bytes reach a
  committed shard by. `stop` writes a file naming the pid; the loop polls it
  between units of work and returns at a safe point. This is `runner.py`'s
  reasoning applied unchanged, and it is also the portable answer, because
  Windows has no POSIX `SIGTERM`.
- **A killed daemon leaves a stale lock**, exactly as a killed runner does, and
  the answer is the same one ADR-MAINTENANCE decision 1c/1d already gives:
  `fux doctor` reports it and an explicit `fux ingest` takes over. **Nothing
  here silently decides a lock is dead.**

## L3 is not weakened, and the argument is §3.2's

A partial refresh means the `url:` half of the index holds documents fetched at
different moments. **It already did** — every record carries whatever its last
fetch produced, and no two were necessarily fetched together. L3 is *same
sources → same bytes*, and **a URL is not the same source twice**. The daemon
changes the spread of those moments, not the kind of object the index is.

**No wall clock reaches a committed byte.** The sweep interval, the pid file and
the status file all live in gitignored `.fux/runtime/`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from ..errors import FuxError
from ..store import fuxdir
from . import runner

#: All three live in the gitignored runtime plane. Nothing the daemon writes is
#: ever committed — that is L2 and L3 both, and it is why there is no
#: `daemon.toml` or committed state file anywhere in this module.
PID_NAME = "daemon.pid"
STOP_NAME = "daemon.stop"
STATUS_NAME = "daemon.status"

#: How long `stop` waits for a cooperative exit before reporting that the
#: daemon did not let go. Matches `runner.STOP_TIMEOUT_S` deliberately: a
#: consumer should not have to learn two numbers for the same gesture.
STOP_TIMEOUT_S = runner.STOP_TIMEOUT_S

#: The loop wakes this often to check for a stop, regardless of how long the
#: sweep interval is. A daemon that only noticed `stop` once an hour would be
#: indistinguishable from a hung one.
POLL_S = 1.0

#: Sweep cadence when `fux.toml` does not say. Sixty minutes is conservative on
#: purpose: this is the *tail*, documents nobody is asking about, so the cost of
#: being an hour late is an hour of staleness on a document with no reader.
DEFAULT_SWEEP_MINUTES = 60


def _runtime(root: Path) -> Path:
    return fuxdir.derived_dir(root, "runtime")


def pid_path(root: Path) -> Path:
    return _runtime(root) / PID_NAME


def _stop_path(root: Path) -> Path:
    return _runtime(root) / STOP_NAME


def _status_path(root: Path) -> Path:
    return _runtime(root) / STATUS_NAME


# -- who is running ---------------------------------------------------------


def live_pid(root: Path) -> int | None:
    """The pid of a running daemon, or `None`.

    A pid file whose process is gone is **reported as absent and left on
    disk** — deleting it here would make this surface a mutating one, which is
    ADR-MAINTENANCE veto 7. `fux doctor` is where a stale file gets named.
    """
    try:
        raw = pid_path(root).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    try:
        pid = int(json.loads(raw)["pid"])
    except (ValueError, KeyError, TypeError):
        return None
    return pid if runner.is_alive(pid) else None


def status(root: Path) -> dict:
    """Read-only. Never starts, stops, or cleans anything (veto 7)."""
    pid = live_pid(root)
    out: dict = {"running": pid is not None, "pid": pid}
    try:
        out["last"] = json.loads(_status_path(root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        out["last"] = None
    return out


# -- start ------------------------------------------------------------------


def start(root: Path) -> str:
    """Spawn a detached daemon. Returns `"started"` or `"already-running"`.

    The spawn mirrors `runner.spawn` rather than inventing a second way to
    detach — same `sys.executable -m fux.cli` (the interpreter we are inside,
    never a `PATH` lookup), same Windows flags, same closed file descriptors.
    """
    if live_pid(root) is not None:
        return "already-running"

    # A stop file from a previous daemon would stop this one on its first poll.
    _clear_stop(root)

    kwargs: dict = {}
    if sys.platform == "win32":  # pragma: no cover - exercised on the Windows CI arms
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True

    try:
        subprocess.Popen(
            [sys.executable, "-m", "fux.cli", "daemon", "--serve"],
            cwd=str(root),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            **kwargs,
        )
    except (OSError, ValueError) as exc:
        raise FuxError(f"could not start the daemon: {exc}") from exc
    return "started"


# -- stop, cooperatively ----------------------------------------------------


def _clear_stop(root: Path) -> None:
    try:
        _stop_path(root).unlink()
    except OSError:
        pass


def stop_requested(root: Path, pid: int) -> bool:
    """What the loop polls. True only for a stop aimed at *this* pid.

    Naming the target is what makes a restart safe: a stop aimed at the daemon
    that just exited can never silently kill the next one.
    """
    try:
        raw = _stop_path(root).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    try:
        return int(json.loads(raw)["pid"]) == pid
    except (ValueError, KeyError, TypeError):
        return False


def stop(root: Path, *, timeout: float = STOP_TIMEOUT_S) -> str:
    """Ask a live daemon to stop and wait for it to go.

    | result | meaning |
    |---|---|
    | `not-running` | nothing to stop |
    | `stopped` | it acknowledged and exited |
    | `timeout` | it did not exit in time — reported, **never escalated to a kill** |

    ⚠ **`timeout` is deliberately not followed by a signal.** A daemon slow to
    stop is usually one mid-`write_index`, which is exactly when killing it
    costs a partial shard.
    """
    pid = live_pid(root)
    if pid is None:
        return "not-running"

    directory = _runtime(root)
    directory.mkdir(parents=True, exist_ok=True)
    _stop_path(root).write_text(json.dumps({"pid": pid}), encoding="utf-8")

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if live_pid(root) is None:
            _clear_stop(root)
            return "stopped"
        time.sleep(runner._POLL_S)
    return "timeout"


# -- the loop ---------------------------------------------------------------


def sweep_minutes(root: Path) -> int:
    """`[sources.url] sweep_minutes`, or the default.

    Unlike `max_parallel` this one **has** a default, and the difference is
    deliberate: `max_parallel` bounds a blast radius and a repo that can fetch
    must state it (W-85), while this only decides how often. A missing cadence
    is not dangerous, merely unopinionated.
    """
    from ..config import load as load_config

    try:
        config = load_config(root)
    except FuxError:
        return DEFAULT_SWEEP_MINUTES
    url = getattr(config, "url", None)
    minutes = getattr(url, "sweep_minutes", None) if url else None
    return int(minutes) if minutes else DEFAULT_SWEEP_MINUTES


def _write_status(root: Path, outcome: str, **extra) -> None:
    directory = _runtime(root)
    try:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / STATUS_NAME).write_text(
            json.dumps({"outcome": outcome, **extra}, sort_keys=True), encoding="utf-8"
        )
    except OSError:
        pass  # status is a courtesy; failing to write it must not end the run


def _sweep(root: Path) -> str:
    """One pass: claim the lock, refresh every URL, release. Never raises.

    Returns `"ok"` · `"busy"` · `"failed"`. **`busy` is not an error** — an
    explicit `fux ingest` or a spawned runner holds the lock, and a human's
    command outranks a clock. The sweep simply comes round again.
    """
    if not runner.acquire(root):
        return "busy"
    try:
        # ⚠ **NOT `from ..ingest import run`.** `fux/ingest/__init__.py` line 11
        # re-exports the FUNCTION under the same name as the submodule, so that
        # form binds a function and `ingest_run.run(...)` raises
        # `AttributeError` -- which the broad handler below turns into a silent
        # `"failed"`. **Every sweep failed, forever, and the daemon looked
        # healthy the whole time.** `import_module` asks for the module by name
        # and cannot be shadowed; the indirection is also what lets a test
        # monkeypatch `fux.ingest.run.run` and have this call see it.
        from importlib import import_module

        ingest_run = import_module("fux.ingest.run")
        ingest_run.run(root, refresh_urls=True)
        return "ok"
    except Exception:  # noqa: BLE001 - a daemon must outlive one bad sweep
        return "failed"
    finally:
        # Released between sweeps, never held across the sleep: an hour-long
        # hold would block every `fux ingest` in the repository.
        runner.release(root)


def serve(root: Path) -> str:
    """The daemon's whole life. Called by `fux daemon --serve` in the child.

    Returns the reason it ended, for tests — a detached process's exit code is
    read by nobody.
    """
    pid = os.getpid()
    directory = _runtime(root)
    directory.mkdir(parents=True, exist_ok=True)
    pid_path(root).write_text(json.dumps({"pid": pid}), encoding="utf-8")

    interval = sweep_minutes(root) * 60
    try:
        while True:
            if stop_requested(root, pid):
                _write_status(root, "stopped")
                return "stopped"
            outcome = _sweep(root)
            _write_status(root, outcome)

            # Sleep in POLL_S slices so `stop` is noticed in about a second
            # rather than at the end of the interval.
            waited = 0.0
            while waited < interval:
                if stop_requested(root, pid):
                    _write_status(root, "stopped")
                    return "stopped"
                time.sleep(POLL_S)
                waited += POLL_S
    finally:
        # The pid file is this process's claim to be running; dropping it on
        # the way out is what makes `stop` return promptly and what stops
        # `status` reporting a ghost.
        try:
            pid_path(root).unlink()
        except OSError:
            pass
        _clear_stop(root)
