"""UTF-8 on stdout and stderr — one encoding for every console script.

Core layer (W-282): `fux` (the CLI, `cli.py`) and `fux-merge-index` (the
writer's merge driver, `maintain/mergedriver.py`) both call it first, and
neither imports the other for it. [SR-CLI](../../records/0101_cli-surface.md).
"""

from __future__ import annotations

import sys


def stdio_utf8() -> None:
    """fux writes UTF-8, on every platform, named rather than inherited.

    🔴 **Found on 2026-09-13, by the Windows e2e suite's first run.** Python
    encodes `sys.stdout` with the *locale* encoding, which is cp1252 on a
    Windows runner — so `fux ask --json` piped to a file or to an agent emitted
    **cp1252 bytes**, and an em dash in a document title came out as `0x97`.
    Every consumer here reads UTF-8: the index is UTF-8, the Node reader is
    UTF-8, and JSON is UTF-8 by definition (RFC 8259 §8.1). One encoding for
    one artefact, decided rather than inherited from whoever's console it is.

    ⚠ **`errors="replace"` on purpose.** A character the stream cannot carry
    must not raise out of a verb that has already done its work. Nothing here
    can fail: a stream that refuses to reconfigure (a closed pipe, a
    replaced stdout in a test) is left exactly as it was.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):  # pragma: no cover - not ours to own
            pass
