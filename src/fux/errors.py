"""The single, flat error type for Fux.

Deliberately one class — no subclass hierarchy (see CLAUDE.md, error contract).
Raise `FuxError` for expected, user-facing failures. Internals keep raising;
errors are caught and rendered only at boundaries (CLI `main`, hook entrypoints).
"""

from __future__ import annotations


class FuxError(Exception):
    """An expected, user-facing failure.

    Carries an optional exit code so the CLI boundary can translate it directly:
    `0` ok · `1` error · `2` blocking (strict) · `130` interrupted.
    """

    def __init__(self, message: str, *, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code
