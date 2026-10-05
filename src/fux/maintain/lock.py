"""The index write lock — the one mutex fux owns over the committed index.

**Owned by [SR-LOCKS](../../../records/0140_locks.md)** since 2026-10-05 (W-261,
Arpit's ruling that every `kind: component` record owns a file). A pure move out
of `maintain/runner.py`, which re-exports every name here so `runner.acquire`,
`runner.write_lock` and the rest keep their callers; the runner, its status file
and the cooperative stop (`runner.stop`) stay SR-MAINTENANCE's, and are not
locks (SR-LOCKS decision 8).

`.fux/runtime/write.lock` is a pid in JSON created with one `O_CREAT|O_EXCL`
syscall in the gitignored derived plane. Every writer holds it; every read verb
holds nothing. Its Node twin is `node/src/maintain/lock.mjs`.
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path

from ..errors import FuxError
from ..store import fuxdir
from ..constants import fixed

__all__ = ["LOCK_NAME", "acquire", "break_lock", "holder", "lock_path", "release", "write_lock"]

#: ⚠ **Renamed from `runner.lock` 2026-08-26 (W-86 P6, Arpit's ruling on fork
#: C).** It is no longer the *runner's* lock: every command that writes the
#: committed index holds it, so a name saying "runner" was about to become a
#: small lie the first time a foreground `fux ingest` took it. Gitignored, so
#: nothing cites the old path.
#:
#: **Not `index.lock`** — git keeps one of those feet away in the same repo,
#: and MACHINE.md already records an incident with a stranded one.
LOCK_NAME = fixed("maintain", "write_lock")


def lock_path(root: Path) -> Path:
    """Public because every message about a wedged runner has to name it —
    a status that says "something is stuck" without saying where is not a
    status (SR-MAINTENANCE decision 1c)."""
    return fuxdir.fux_dir(root) / "runtime" / LOCK_NAME


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


def acquire(root: Path, *, required: bool) -> bool:
    """Claim the write lock atomically. `False` means somebody else holds it.

    `O_CREAT|O_EXCL` is the whole mechanism — one syscall, no read-then-write
    window for a second writer to slip through. This is what makes a 50-commit
    `git rebase` produce one runner rather than fifty.

    ⚠ **`required` exists because the same line means opposite things to the
    two callers** (W-86 P6). A background runner that cannot take the lock
    should decline quietly — someone else is already doing the work. A
    **foreground writer** that cannot take it and proceeds anyway has inverted
    the point of the lock, so it raises instead.

    The `OSError` branch is the sharper half of that. Degrading on a read-only
    or full filesystem is right for a runner and **wrong for a writer**: the
    write is about to happen either way, and doing it unprotected is the
    outcome the lock exists to prevent.
    """
    directory = fuxdir.derived_dir(root, "runtime")
    try:
        fd = os.open(
            str(directory / LOCK_NAME), os.O_CREAT | os.O_EXCL | os.O_WRONLY, fixed("maintain", "lock_mode")
        )
    except FileExistsError:
        if required:
            raise FuxError(
                f"another fux process is writing this index (lock: {lock_path(root)}). "
                "Wait for it, or - if you are certain no fux process is running - "
                "delete that file and re-run"
            ) from None
        return False
    except OSError as exc:
        if required:
            raise FuxError(
                f"cannot create the index write lock at {lock_path(root)}: {exc}. "
                "Writing without it could corrupt the index if a second process starts"
            ) from exc
        return False  # a background runner degrades; a writer never does
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump({"pid": os.getpid()}, handle)
    return True


@contextmanager
def write_lock(root: Path):
    """Hold the write lock for the duration of one index write.

    **Every command that writes the committed index uses this** — `ingest`,
    `build`, `add`, `remove`, `update`. **Read verbs take nothing**: a lock on
    the read path would make a search fail because a re-index was running,
    which trades a real problem for a worse one.

    ⚠ A runner that already holds the lock (it called `acquire` itself) must
    not deadlock against this, so re-entry by the same pid is permitted.
    """
    if holder(root) == os.getpid():
        yield  # already ours; the runner path
        return
    acquire(root, required=True)
    try:
        yield
    finally:
        release(root)


def release(root: Path) -> None:
    """Drop the lock. Never raises — a runner exiting must not fail on cleanup."""
    try:
        lock_path(root).unlink()
    except OSError:
        pass


def break_lock(root: Path) -> None:
    """Remove a lock this process has decided is stale.

    **Only ever called from an explicit human command** (`fux ingest`, which is
    a takeover by SR-MAINTENANCE decision 1d) and only after the holder has
    been given the cooperative stop and found not to be running. The status
    surface never calls this — that is veto 7.
    """
    release(root)
