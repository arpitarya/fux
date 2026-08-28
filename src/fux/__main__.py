"""`python -m fux` — the invocation ladder's last rung.

**Why this file exists at all.** The ladder ADR-AGENT-POLICY hands an agent
ends in a `python -m` form, so that a repo where `fux` is installed into a
`.venv` that is not active still resolves to *the engine is here* rather than
`command not found` — the failure that made an agent conclude "not installed"
and silently fall back to grep.

`python -m fux.cli` already worked and is what `tests_e2e/` spawns. **But it is
not what anyone types.** A user reaching for a module invocation types the
package name, gets `No module named fux.__main__`, and reads it as absence.
Arpit ruled the last rung should be the spelling a human guesses
(2026-08-27, W-82 §3.6 fork B).

**This is a delegate, not a second implementation.** There is exactly one
`main`, in `fux.cli`; both spellings reach it, and a test asserts the two
produce identical output. If this file ever grows argument handling of its own,
that test is the thing that should have stopped it.
"""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
