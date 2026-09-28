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

## SR-MAINTENANCE veto condition 6, fired and answered

Veto 6 reads: *"The detached runner turns into something always-on — a resident
process, a scheduler, or a watcher."* **This is resident, so the veto is fired
rather than sidestepped**, and the answer is recorded in SR-MAINTENANCE rather
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

- **It takes `write.lock`** — the same lock, via the same `runner.acquire`.
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
  the answer is the same one SR-MAINTENANCE decision 1c/1d already gives:
  `fux doctor` reports it and an explicit `fux ingest` takes over. **Nothing
  here silently decides a lock is dead.**

## L4 is not weakened, and the argument is §3.2's

A partial refresh means the `url:` half of the index holds documents fetched at
different moments. **It already did** — every record carries whatever its last
fetch produced, and no two were necessarily fetched together. L4 is *same
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
from datetime import timedelta
from pathlib import Path

from ..errors import FuxError
from ..store import fuxdir
from . import runner
from ..constants import fixed

#: All three live in the gitignored runtime plane. Nothing the daemon writes is
#: ever committed — that is L3 and L4 both, and it is why there is no
#: `daemon.toml` or committed state file anywhere in this module.
PID_NAME = fixed("maintain", "daemon_pid")
STOP_NAME = fixed("maintain", "daemon_stop")
STATUS_NAME = fixed("maintain", "daemon_status")

#: How long `stop` waits for a cooperative exit is the runner's own
#: `[maintain] stop_timeout_s`, deliberately: a consumer should not have to
#: learn two numbers for the same gesture. The loop wakes every `[maintain]
#: daemon_poll_s` to check for a stop, regardless of how long the sweep
#: interval is -- a daemon that only noticed `stop` once an hour would be
#: indistinguishable from a hung one (W-225 stage 5e).

#: ⚠ **`DEFAULT_SWEEP_MINUTES = 60` was deleted by W-225 stage 3b** (SR-LAW-12),
#: with its twin in `config.py`. The cadence is `[sources.url] sweep_minutes`,
#: required whenever the table exists; the template writes `60`.


def _runtime(root: Path) -> Path:
    """The path — **it does not create the directory.**

    🔴 **It called `derived_dir` until 2026-09-12 and that made `fux doctor`
    write** (W-140 row 7). `derived_dir` mkdir's and drops `CACHEDIR.TAG`, and
    `status()` → `live_pid()` → `pid_path()` reaches here on a pure READ — so
    running the read-only health command on a repo with no `.fux/` created
    `.fux/` and `.fux/runtime/CACHEDIR.TAG`. A diagnostic that modifies the
    thing it is diagnosing is the one property `doctor` advertises and did not
    have, and `runner.py`/`urlstate.py` had it right all along: a path helper
    returns a path.

    **The writers create it**, with `_writable_runtime()` below, which is where
    the tag belongs anyway — it marks a directory that HOLDS a cache."""
    return fuxdir.fux_dir(root) / "runtime"


def _writable_runtime(root: Path) -> Path:
    """The path, created and `CACHEDIR.TAG`-marked. **Writers only.**"""
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
    SR-MAINTENANCE veto 7. `fux doctor` is where a stale file gets named.
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
    # Before the spawn, so the refusal reaches the person who typed `start`
    # rather than a detached child's /dev/null.
    _interval_s(root)

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


def stop(root: Path, *, timeout: float | None = None) -> str:
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

    pace = runner.pacing(root)
    if timeout is None:
        timeout = pace.stop_timeout_s
    _writable_runtime(root)
    _stop_path(root).write_text(json.dumps({"pid": pid}), encoding="utf-8")

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if live_pid(root) is None:
            _clear_stop(root)
            return "stopped"
        time.sleep(pace.runner_poll_s)
    return "timeout"


# -- the loop ---------------------------------------------------------------


def sweep_minutes(root: Path) -> int | None:
    """`[sources.url] sweep_minutes` — `None` when there is no `[sources.url]`.

    ⚠ **It fell back to 60 until W-225 stage 3b**, on a missing key, a missing
    table, or a `fux.toml` that did not load. The key is now required with the
    table, and a `fux.toml` that does not load raises here as it does
    everywhere. A repo with no `[sources.url]` fetches nothing, so it has no
    tail to sweep and no cadence to state: `None`.
    """
    from ..config import load as load_config

    url = load_config(root).url
    return None if url is None else url.sweep_minutes


def _interval_s(root: Path) -> int:
    """The sweep interval in seconds, or a `FuxError` naming why there is none.

    ⚠ **A repo with no `[sources.url]` is refused** (W-225 stage 3b). The
    daemon covers the URL tail (SR-HOOKS decision 9c-i), and its cadence is a
    key in that table; until stage 3b such a repo swept every 60 minutes on a
    constant in code, re-walking only what the hooks already re-walk.
    """
    minutes = sweep_minutes(root)
    if minutes is None:
        raise FuxError(
            "fux daemon: this repo has no [sources.url] in fux.toml, so there are no URLs "
            "to keep fresh and no sweep_minutes to pace them. The git hooks keep "
            "directory sources current (`fux hooks install`)"
        )
    return timedelta(minutes=minutes).total_seconds()


def _write_status(root: Path, outcome: str, **extra) -> None:
    """Write `.fux/runtime/daemon.status`. Declared in `state.schema.json`."""
    try:
        directory = _writable_runtime(root)
        (directory / STATUS_NAME).write_text(
            json.dumps({"outcome": outcome, **extra}, sort_keys=True), encoding="utf-8"
        )
    except OSError:
        pass  # status is a courtesy; failing to write it must not end the run


def _sweep(root: Path) -> dict:
    """One pass: claim the lock, refresh every URL, release. Never raises.

    Returns the status dict — `outcome` plus whatever explains it. **`busy` is
    not an error**: an explicit `fux ingest` or a spawned runner holds the lock,
    a human's command outranks a clock, and the sweep comes round again.

    ⚠ **This returned a bare string until 2026-08-28**, and both halves of that
    cost something real:

    * A `FuxError` about `max_parallel` and a dead network were **the same
      `"failed"`**, so a misconfigured repository failed forever with nothing to
      go on.
    * **An `"ok"` sweep could skip URLs silently.** Two of seven did in the
      2026-08-27 real-network run, and the only surface that said so was a
      foreground `fux ingest` nobody runs.

    So `reason` explains a failure and `fetched`/`skipped` describe every
    outcome — an `"ok"` with `skipped: 2` is the case the old shape could not
    express at all. Ruled by Arpit 2026-08-28.
    """
    if not runner.acquire(root, required=False):
        return {"outcome": "busy"}
    try:
        # ⚠ `import_module` rather than `from ..ingest import run`. The
        # re-export that made the latter bind a FUNCTION was removed repo-wide
        # on 2026-08-27 (`tests/test_no_shadowed_submodules.py` keeps it gone),
        # but this form is kept for a second, still-live reason: it is what lets
        # a test monkeypatch `fux.ingest.run.run` and have this call see it.
        from importlib import import_module

        ingest_run = import_module("fux.ingest.run")
        report = ingest_run.run(root, refresh_urls=True, full=False)
    except Exception as exc:  # noqa: BLE001 - a daemon must outlive one bad sweep
        # The type is carried as well as the message: a `FuxError` is the repo's
        # own refusal (fix your config), anything else is a surprise (fix fux).
        return {"outcome": "failed", "reason": f"{type(exc).__name__}: {exc}"[:300]}
    finally:
        # Released between sweeps, never held across the sleep: an hour-long
        # hold would block every `fux ingest` in the repository.
        runner.release(root)

    skipped = list(getattr(report, "skipped", ()) or ())
    out: dict = {
        "outcome": "ok",
        "fetched": max(0, int(getattr(report, "doc_count", 0)) - len(skipped)),
        "skipped": len(skipped),
    }
    if skipped:
        # The FIRST skip's reason, not a list: the status file is a fixed-size
        # courtesy, and an unbounded field on a file written every sweep is how a
        # runtime file grows without anyone deciding it should. The count says
        # how many; `fux ingest` and the enrich queue carry the rest.
        first = skipped[0]
        out["reason"] = f"{len(skipped)} skipped, first: {getattr(first, 'reason', '?')}"[:300]
    return out


def serve(root: Path) -> str:
    """The daemon's whole life. Called by `fux daemon --serve` in the child.

    Returns the reason it ended, for tests — a detached process's exit code is
    read by nobody.
    """
    pid = os.getpid()
    _writable_runtime(root)
    pid_path(root).write_text(json.dumps({"pid": pid}), encoding="utf-8")

    interval = _interval_s(root)
    poll_s = runner.pacing(root).daemon_poll_s
    try:
        while True:
            if stop_requested(root, pid):
                _write_status(root, "stopped")
                return "stopped"
            result = _sweep(root)
            _write_status(root, **result)

            # Sleep in `daemon_poll_s` slices so `stop` is noticed in about a second
            # rather than at the end of the interval.
            waited = 0.0
            while waited < interval:
                if stop_requested(root, pid):
                    _write_status(root, "stopped")
                    return "stopped"
                time.sleep(poll_s)
                waited += poll_s
    finally:
        # The pid file is this process's claim to be running; dropping it on
        # the way out is what makes `stop` return promptly and what stops
        # `status` reporting a ghost.
        try:
            pid_path(root).unlink()
        except OSError:
            pass
        _clear_stop(root)
