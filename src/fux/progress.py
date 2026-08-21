"""A progress plane for the write verbs — `ingest.run()` and `derive.build()`.

R5 measured 44.4 s of total silence on the commit-path ingest at 100 000
documents. This module exists to make that wait visible without touching
anything that could change what a caller reads.

Four rules, and every one of them is load-bearing (W-64):

1. **stderr only, never stdout.** stdout keeps meaning "the answer", so
   `--json` and every piped invocation stay byte-identical whether a bar is
   painted or not.
2. **Off automatically when stderr is not a TTY.** CI logs, pipes, and this
   repo's own captured CLI transcripts stay exactly what they are today.
3. **Counts, not clocks.** No ETA, no elapsed time, no rate — CLAUDE.md's
   "no wall-clock output anywhere on the maintenance path" applies here even
   though the bytes it protects are elsewhere. There is no timer anywhere in
   this file.
4. **A count threshold, not a delay onset.** A phase paints only once its
   total exceeds `THRESHOLD`, so a run where almost everything carries
   forward (`fux remove`, most `fux ingest` re-runs) never flashes a bar it
   would immediately clear.

`Progress(None)` — the default everywhere — means silent, so every existing
`run()`/`build()` caller and every existing test is unaffected by this file
existing at all.
"""

from __future__ import annotations

import os
import sys

__all__ = ["Progress", "NULL"]

#: Below this total, a phase's bar costs more terminal churn than it earns —
#: the count threshold rule (W-64, rule 4). No timer backs this: it is
#: checked once, against a total that is already known.
THRESHOLD = 200

_BAR_WIDTH = 20
_FULL = "█"  # █
_EMPTY = "░"  # ░

#: The widest a whole painted line may be. `\r` returns to the start of the
#: *terminal* line, so a line that wrapped cannot be erased — the tail stays
#: on screen and the "no partial line" guarantee quietly stops holding. 80 is
#: the narrowest terminal anyone still uses; staying inside it needs no
#: `os.get_terminal_size` call and behaves the same when there is no terminal
#: to ask (a pipe under `--progress`, a Windows console that reports 0).
_MAX_LINE = 80


def _clean(detail: str) -> str:
    """A path is data, not layout. Strip anything that would move the cursor.

    A `\\n`, `\\r` or `\\x1b` inside a filename — legal on POSIX, and a
    plausible thing to find in a corpus nobody curated — would break the
    single-line repaint into several lines that `\\r` can never take back.
    """
    return "".join(ch for ch in detail if ch.isprintable())


def _env_disables() -> bool:
    # Explicitly "0" (as the git hooks write) means "checked and left on" —
    # only a genuinely truthy value opts out. Absence does not disable.
    value = os.environ.get("FUX_NO_PROGRESS", "")
    return value not in ("", "0")


class Progress:
    """One bar at a time, painted on stderr, committed to scrollback on a
    phase's normal completion and erased on any other exit (Ctrl-C, an
    exception mid-phase) — the DoD's "no partial line left behind".

    `no_progress` and `force` are the CLI's `--no-progress`/`--progress`;
    either one is decisive over the environment and the TTY check. With
    neither given, `FUX_NO_PROGRESS` is decisive over the TTY check.
    """

    def __init__(
        self, *, no_progress: bool = False, force: bool = False, stream=None
    ) -> None:
        self._stream = stream if stream is not None else sys.stderr
        if no_progress:
            enabled = False
        elif force:
            enabled = True
        elif _env_disables():
            enabled = False
        else:
            enabled = bool(getattr(self._stream, "isatty", lambda: False)())
        self._enabled = enabled
        self._painted = False
        self._last_len = 0

    def phase(self, name: str, total: int, unit: str = "") -> "_Phase":
        """Open one phase. `total` must already be known — see the module
        docstring's rule 4; there is nothing here that waits and reveals a
        total later.

        `unit` names what is being counted when it is **not** documents, so a
        `write` phase reading `252/252 shards` cannot be misread as a loss of
        950 documents between it and the phase above.
        """
        return _Phase(self, name, total, unit)

    # -- internals, called only by _Phase -----------------------------------

    def _paint(self, name: str, count: int, total: int, detail: str, unit: str) -> None:
        if not self._enabled or total <= THRESHOLD:
            return
        filled = _BAR_WIDTH * min(count, total) // total if total else 0
        bar = _FULL * filled + _EMPTY * (_BAR_WIDTH - filled)
        line = f"  {name:<9}[{bar}] {count}/{total}"
        if unit:
            line = f"{line} {unit}"
        if detail:
            # The counts are the point and the detail is the courtesy, so the
            # detail is what gets truncated — from the left, because the tail
            # of a path identifies a document and its leading directories do
            # not. Ellipsis first, so a clipped path cannot be misread as a
            # real one.
            room = _MAX_LINE - len(line) - 2
            clean = _clean(detail)
            if room >= 4:
                line = f"{line}  {clean if len(clean) <= room else '…' + clean[-(room - 1):]}"
        line = line[:_MAX_LINE]
        pad = " " * max(0, self._last_len - len(line))
        self._stream.write(f"\r{line}{pad}")
        self._stream.flush()
        self._last_len = len(line)
        self._painted = True

    def _commit(self) -> None:
        if self._painted:
            self._stream.write("\n")
            self._stream.flush()
            self._painted = False
            self._last_len = 0

    def _clear(self) -> None:
        if self._painted:
            self._stream.write("\r" + " " * self._last_len + "\r")
            self._stream.flush()
            self._painted = False
            self._last_len = 0


class _Phase:
    def __init__(self, progress: Progress, name: str, total: int, unit: str = "") -> None:
        self._progress = progress
        self._name = name
        self._total = total
        self._unit = unit
        self._count = 0

    def __enter__(self) -> "_Phase":
        self._progress._paint(self._name, self._count, self._total, "", self._unit)
        return self

    def update(self, n: int = 1, detail: str = "") -> None:
        self._count += n
        self._progress._paint(self._name, self._count, self._total, detail, self._unit)

    def __exit__(self, exc_type, exc, tb) -> bool:
        # try/finally by construction: a `with` block always runs __exit__,
        # normal return or not — the mechanism this file's "no partial line"
        # requirement leans on.
        if exc_type is None:
            self._progress._commit()
        else:
            self._progress._clear()
        return False


class _NullPhase:
    def __enter__(self) -> "_NullPhase":
        return self

    def update(self, n: int = 1, detail: str = "") -> None:
        pass

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class _NullProgress:
    def phase(self, name: str, total: int, unit: str = "") -> _NullPhase:
        return _NULL_PHASE


_NULL_PHASE = _NullPhase()

#: What `run()`/`build()` use in place of `None` internally, so every phase
#: call site is unconditional — no `if progress:` scattered through them.
NULL = _NullProgress()
