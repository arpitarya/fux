"""The deferred re-index runner — W-66 Phase 2, ADR-MAINTENANCE decisions 1a/1d.

`post-commit` no longer re-indexes inline. It records what changed
([`dirty.py`](dirty.py)), spawns a **detached one-shot** re-index, and returns.
Commit cost becomes git's cost, constant in the corpus, which is the whole of
what R5's failure bought.

## One-shot, never resident

The spawned process **drains the dirty list and exits**. No scheduler, no
watcher, nothing resident — ADR-MAINTENANCE veto condition 6 fires on any of
those. It outlives the *commit* by design (that is what deferral means); what
it may never do is outlive the work it was started for.

**It does loop, and the loop is a correctness fix rather than a convenience.**
A commit landing while this runner holds the lock has its spawn refused, on the
documented assumption that *"the live runner picks up the accumulated list
anyway"*. That assumption is only true if the live runner has not already taken
its start-time snapshot — if it has, it clears *its* snapshot, exits, and the
newer work is stranded with nobody holding it and no guarantee another commit
will arrive. **CI found this: every Linux arm failed while Windows and macOS
passed**, which is what a race looks like when one platform is slower.

So `run_once` re-reads the list after each pass and runs again while there is
work, bounded absolutely by `MAX_PASSES`. That bound is what keeps this on the
right side of veto 6: the process provably terminates, and anything left over
stays in the list for `fux doctor` to report and the next commit's spawn to
collect — exactly where it would have been anyway.

## Single writer, and why the lock is a pid rather than an OS lock

Two runners writing `.fux/index/` at once is the failure this module exists to
prevent, so `runner.lock` is created with `O_CREAT|O_EXCL` — atomic on every
platform fux supports — and a second spawn that loses the race **exits
quietly**. It does not queue and it does not block: the live runner re-reads
the dirty list, which is a union, so the work is not lost by being dropped.

An OS-level advisory lock (`fcntl.flock`, `msvcrt.locking`) would release
itself when a holder dies and so could never go stale. It was **not** used, and
that is a decision rather than an oversight: ADR-MAINTENANCE decision 1c
requires the runner's state to be *reportable* — which pid, held or stale — and
an flock is held by a file descriptor nobody outside the process can name. The
cost is that a killed runner leaves a lock file behind; the answer to that is
`fux doctor` reporting it and `fux ingest` taking over, never a background
process silently deciding a lock is dead.

## The stop is cooperative, and it names its target

`request_stop` writes `runner.stop` carrying the pid it is aimed at; the runner
polls it between units of work and returns at a safe point. **Not a kill.** A
signal delivered inside `write_index` can leave a partial shard, and that is
the one path bytes reach a committed shard by. Cooperative is also the portable
answer — Windows has no POSIX `SIGTERM` — so L7 and the Windows-first litmus
point the same way.

The stop file naming its target pid is what makes takeover safe under a rebase:
a stop aimed at the runner that just exited can never silently kill the next
one, which would otherwise wedge a 50-commit rebase into indexing nothing.

## What a stopped run leaves behind

Nothing. The only stop points are **before** `write_index`, so a stopped run
has written no index bytes and has subtracted nothing from the dirty list. A
run that reaches `write_index` finishes it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from ..store import fuxdir

__all__ = [
    "LOCK_NAME",
    "STOP_NAME",
    "STATUS_NAME",
    "holder",
    "is_alive",
    "lock_path",
    "record_head",
    "release",
    "request_stop",
    "run_once",
    "spawn",
    "status",
    "stop_requested",
    "take_over",
]

LOCK_NAME = "runner.lock"
STOP_NAME = "runner.stop"
STATUS_NAME = "runner.status"

#: How long `request_stop` waits for a cooperative runner to reach a safe point.
#: Generous on purpose: the longest unit of work between stop checks is one
#: `write_index`, and a stop that gave up early would be a stop that leaves two
#: writers believing they hold the index.
STOP_TIMEOUT_S = 30.0
_POLL_S = 0.05

#: How many times one runner will re-drain the dirty list before exiting and
#: leaving the rest to the next commit's spawn.
#:
#: **A bound, not a tuning knob.** It exists so the loop in `run_once`
#: provably terminates: without it, a repository committing faster than it
#: re-indexes would keep one process alive indefinitely, which is precisely
#: the resident process ADR-MAINTENANCE veto condition 6 forbids. Reaching the
#: cap is not an error — the leftovers stay in the dirty list, `fux doctor`
#: reports them, and the next commit spawns a fresh runner.
MAX_PASSES = 5


def _runtime(root: Path) -> Path:
    return fuxdir.fux_dir(root) / "runtime"


def lock_path(root: Path) -> Path:
    """Public because every message about a wedged runner has to name it —
    a status that says "something is stuck" without saying where is not a
    status (ADR-MAINTENANCE decision 1c)."""
    return _runtime(root) / LOCK_NAME


def _stop_path(root: Path) -> Path:
    return _runtime(root) / STOP_NAME


def _status_path(root: Path) -> Path:
    return _runtime(root) / STATUS_NAME


# -- liveness ---------------------------------------------------------------


def is_alive(pid: int | None) -> bool:
    """Best-effort: is a process with this pid running right now?

    **Never `os.kill(pid, 0)` on Windows.** CPython implements `os.kill` there
    as `OpenProcess` + `TerminateProcess(handle, sig)` for any signal that is
    not a console control event — so the POSIX idiom for *"does this process
    exist"* **terminates the process** on Windows, with exit code 0. That is
    precisely the class of silent, rare, someone-else's-OS failure this phase
    was assigned to an Opus session for.

    The answer is advisory in both directions and is never acted on
    destructively: a pid can be reused, so `True` does not prove *our* runner
    is alive, and this is why the status surface reports rather than repairs
    (ADR-MAINTENANCE decision 1c, veto 7).
    """
    if not pid or pid <= 0:
        return False
    if sys.platform == "win32":  # pragma: no cover - exercised on the Windows CI arms
        import ctypes

        synchronize = 0x00100000
        handle = ctypes.windll.kernel32.OpenProcess(synchronize, False, pid)
        if not handle:
            return False
        try:
            # WAIT_TIMEOUT (258) means it has not exited; WAIT_OBJECT_0 (0) means it has.
            return ctypes.windll.kernel32.WaitForSingleObject(handle, 0) == 258
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # it exists; it just is not ours to signal
    except OSError:
        return False
    return True


# -- the lock ---------------------------------------------------------------


def holder(root: Path) -> int | None:
    """The pid recorded in the lock file, or `None` if no lock is present.

    A malformed lock reads as *held by an unknown pid* (`-1`) rather than as
    absent: treating a file we cannot parse as "nothing is running" is how two
    runners end up in `.fux/index/`.
    """
    try:
        raw = lock_path(root).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    try:
        return int(json.loads(raw)["pid"])
    except (ValueError, KeyError, TypeError):
        return -1


def acquire(root: Path) -> bool:
    """Claim the lock atomically. `False` means somebody else holds it.

    `O_CREAT|O_EXCL` is the whole mechanism — one syscall, no read-then-write
    window for a second runner to slip through. This is what makes a 50-commit
    `git rebase` produce one runner rather than fifty.
    """
    directory = fuxdir.derived_dir(root, "runtime")
    try:
        fd = os.open(str(directory / LOCK_NAME), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        return False
    except OSError:
        return False  # read-only or full filesystem: degrade, never block
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump({"pid": os.getpid()}, handle)
    return True


def release(root: Path) -> None:
    """Drop the lock. Never raises — a runner exiting must not fail on cleanup."""
    try:
        lock_path(root).unlink()
    except OSError:
        pass


def break_lock(root: Path) -> None:
    """Remove a lock this process has decided is stale.

    **Only ever called from an explicit human command** (`fux ingest`, which is
    a takeover by ADR-MAINTENANCE decision 1d) and only after the holder has
    been given the cooperative stop and found not to be running. The status
    surface never calls this — that is veto 7.
    """
    release(root)


# -- the cooperative stop ---------------------------------------------------


def stop_requested(root: Path, pid: int) -> bool:
    """What a running runner polls. True only for a stop aimed at *this* pid."""
    try:
        raw = _stop_path(root).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    try:
        return int(json.loads(raw)["pid"]) == pid
    except (ValueError, KeyError, TypeError):
        return False


def _clear_stop(root: Path) -> None:
    try:
        _stop_path(root).unlink()
    except OSError:
        pass


def request_stop(root: Path, *, timeout: float = STOP_TIMEOUT_S) -> str:
    """Ask a live runner to stop, and wait for it to let go of the lock.

    Returns one of:

    | result | meaning |
    |---|---|
    | `"idle"` | nothing was running — **this is success**, not an error |
    | `"stopped"` | a runner was asked to stop and released the lock |
    | `"stale"` | the lock's holder is not running; the lock was broken |
    | `"wedged"` | the holder is alive and did not stop inside `timeout` |

    `"wedged"` is the only unhappy answer and it is deliberately not resolved
    here: breaking a lock whose owner is demonstrably alive is the two-writers
    failure the lock exists to prevent. The caller reports it and names the
    lock file.
    """
    pid = holder(root)
    if pid is None:
        return "idle"

    directory = fuxdir.derived_dir(root, "runtime")
    try:
        (directory / STOP_NAME).write_text(json.dumps({"pid": pid}), encoding="utf-8")
    except OSError:
        return "wedged"  # cannot even ask; do not proceed to write the index

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if holder(root) is None:
            _clear_stop(root)
            return "stopped"
        if not is_alive(pid):
            break
        time.sleep(_POLL_S)

    _clear_stop(root)
    if holder(root) is None:
        return "stopped"
    if not is_alive(pid):
        break_lock(root)
        return "stale"
    return "wedged"


def take_over(root: Path, *, timeout: float = STOP_TIMEOUT_S) -> str:
    """Stop whatever is running so an explicit command can write the index.

    ADR-MAINTENANCE decision 1d: *the explicit instruction wins*. Refusing
    would make a person argue with a background job they did not start, and
    waiting would reintroduce on `fux ingest` exactly the latency deferral
    removed from `git commit`.
    """
    return request_stop(root, timeout=timeout)


# -- the last run's outcome -------------------------------------------------


def _write_status(root: Path, outcome: str, **extra) -> None:
    """Record how the last run ended. Best-effort; never raises.

    A detached process has nowhere to print, so without this a failed
    background re-index is completely silent — which is the opacity
    ADR-MAINTENANCE decision 1c exists to close.
    """
    try:
        directory = fuxdir.derived_dir(root, "runtime")
        (directory / STATUS_NAME).write_text(
            json.dumps({"outcome": outcome, **extra}, sort_keys=True), encoding="utf-8"
        )
    except OSError:
        pass


def last_run(root: Path) -> dict | None:
    try:
        return json.loads(_status_path(root).read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return None


def status(root: Path) -> dict:
    """Everything the runner knows about itself. **Read-only, always.**

    This is the whole of ADR-MAINTENANCE decision 1c's four questions, and it
    is a pure function of the filesystem: it opens no lock, clears nothing, and
    repairs nothing. `fux doctor` renders it; nothing else in the engine acts
    on it.
    """
    from . import dirty

    pid = holder(root)
    alive = is_alive(pid) if pid is not None else False
    return {
        "running": pid is not None and alive,
        "pid": pid,
        "lock": (
            "free" if pid is None else ("held" if alive else "stale")
        ),
        "lock_path": str(lock_path(root)),
        "pending": len(dirty.read(root)),
        "last_run": last_run(root),
    }


# -- what the hook records --------------------------------------------------


def record_head(root: Path) -> int:
    """Union HEAD's changed paths into the dirty list; return the pending count.

    **In Python rather than in the hook's shell**, which is where W-66 Phase 1
    first put it. Three reasons, and the third is the one that decided it:
    `sed`/`mv` pipelines are the part of a `#!/bin/sh` hook most likely to
    behave differently under git-for-windows; the union has to be read-then-
    write, which is fiddly to make crash-safe in shell; and a shell
    implementation cannot be unit-tested, while this can.

    `--root` makes the very first commit in a repository work: without it
    `git diff-tree HEAD` has no parent to diff against and prints nothing, so
    a fresh repo's first commit would record no dirty documents at all.

    Best-effort throughout. A failure here means the list under-reports, which
    costs a *report*, never correctness — `fux ingest` re-indexes the whole
    corpus regardless of what the list says.
    """
    from . import dirty

    try:
        result = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "--root", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return len(dirty.read(root))
    if result.returncode == 0:
        paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        # `.fux/` is fux's own output, not corpus content. Recording the index
        # it just wrote as "dirty" would make every re-index dirty the list it
        # is trying to drain, and the count would never reach zero.
        dirty.record(root, [f"file:{p}" for p in paths if not p.startswith(".fux/")])
    return len(dirty.read(root))


# -- the spawn --------------------------------------------------------------


def spawn(root: Path) -> bool:
    """Start a detached one-shot re-index. `False` if one is already live.

    Checked before spawning as a courtesy only — the spawned process races for
    the lock itself and exits quietly if it loses, which is the check that
    actually holds. Doing it here too keeps a rebase from paying 50 interpreter
    starts to discover the same thing 50 times.

    **Never raises.** A hook that could fail a commit because a spawn failed
    would have traded a slow commit for a broken one.
    """
    if holder(root) is not None:
        return False

    kwargs: dict = {}
    if sys.platform == "win32":  # pragma: no cover - exercised on the Windows CI arms
        # There is no `fork`. These two flags are the documented way to get a
        # process that survives its parent and owns no console.
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True  # setsid: survives the shell that spawned it

    try:
        subprocess.Popen(
            # `sys.executable -m fux.cli`, not the `fux` script: it pins the
            # interpreter and the install we are already running inside, where
            # a bare `fux` would resolve against whatever PATH the hook has.
            [sys.executable, "-m", "fux.cli", "ingest", "--runner"],
            cwd=str(root),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            **kwargs,
        )
    except (OSError, ValueError):
        return False
    return True


# -- the worker -------------------------------------------------------------


def run_once(root: Path) -> str:
    """The detached process's whole life: claim, ingest, release, exit.

    Returns `"busy"` · `"ok"` · `"stopped"` · `"failed"`. The caller is
    `fux ingest --runner` and the return value is for tests — a detached
    process's exit code is read by nobody.
    """
    from ..ingest.run import run as ingest_run

    if not acquire(root):
        return "busy"  # the live runner will pick up our additions: the list is a union
    pid = os.getpid()
    try:
        # A stop aimed at a *previous* runner must not kill this one before it
        # has done anything. We hold the lock, so nobody else can be racing us
        # for this file.
        if _stop_path(root).exists() and not stop_requested(root, pid):
            _clear_stop(root)

        from . import dirty

        passes = 0
        while True:
            passes += 1
            try:
                report = ingest_run(root, should_stop=lambda: stop_requested(root, pid))
            except Exception as exc:  # noqa: BLE001 - recorded, not swallowed; see below
                # A detached process has no stderr anyone reads, so an
                # unrecorded exception is an invisible failure. It is written
                # down and then re-raised: the traceback still goes to the
                # process's own (null) stderr, and nothing here decides the
                # error was unimportant.
                _write_status(root, "failed", error=f"{type(exc).__name__}: {exc}", passes=passes)
                raise
            if report is None:
                _write_status(root, "stopped", passes=passes)
                return "stopped"
            # **Re-check, and this is a correctness fix rather than a
            # nicety.** A commit landing while we held the lock had its spawn
            # refused — correctly, one writer — on the documented assumption
            # that "the live runner picks up the accumulated list anyway". That
            # assumption is only true if the live runner has not already taken
            # its start-time snapshot. If it has, it discards *its* snapshot,
            # exits, and the newer work is stranded with nobody left to run
            # it: no process holds it, and no further commit is guaranteed.
            #
            # **Found by CI, not by reasoning.** Every Linux arm failed while
            # Windows and macOS passed — the race is real on all three and the
            # slower runner simply lost it more often.
            #
            # **This is not veto condition 6.** The process still terminates:
            # it loops only while there is recorded work, and `MAX_PASSES`
            # bounds it absolutely. It is not resident, has no scheduler and
            # watches nothing — it drains what exists and exits. Leftovers are
            # reported by `fux doctor` and picked up by the next commit's
            # spawn, which is exactly where they were before this loop existed.
            if not dirty.read(root) or passes >= MAX_PASSES:
                break

        _write_status(root, "ok", docs=report.doc_count, changed=report.changed_count, passes=passes)
        return "ok"
    finally:
        release(root)
