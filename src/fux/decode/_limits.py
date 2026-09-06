"""The one place a decoder can read committed configuration.

## Why this exists, and why it is not a parameter

A decoder is `EXTENSIONS` plus `decode(raw, rel_path)` — two names, and
[ADR-DECODE](../../../docs/adr/0049_decode.md) decision 1 is emphatic that the
protocol is the whole interface. Adding a third parameter for configuration
would break every consumer decoder in every repo to serve one setting.

But `decode()` at the registry level **does** know the root, because it takes
one. So the root is bound here for the duration of one decoder call and read
back by whichever decoder wants it. The protocol is untouched; a decoder that
ignores configuration never learns this module exists.

## Why a `ContextVar` rather than a module global

Ingest walks documents and nothing in this engine promises to stay
single-threaded forever. A `ContextVar` is stdlib, costs nothing, and is
correct under threads and async both — a global would be a latent
cross-document bleed that only shows up under concurrency, which is the worst
kind of defect to leave for someone else.

## L3 holds

`fux.toml` is **committed**, so `same sources -> same index` becomes `same
sources + same committed config -> same index`, which is the shape
`.fux/sources/` already has. This is not a tunable: `.fux/tune.toml` holds
knobs that change how results are **ordered**, and this one changes what is
**indexed**. ADR-TUNE decision 7 draws that line, and a row limit is on the
config side of it.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

__all__ = ["bound_root", "max_table_rows"]

#: ⚠ The default lives in `config.py`, not here, because `fux.decode` imports
#: that module and the reverse would be a cycle. Read lazily below so this file
#: stays importable from a consumer decoder loaded by path.

_ROOT: ContextVar[Path | None] = ContextVar("fux_decode_root", default=None)


@contextmanager
def bound_root(root: Path | None):
    """Bind the repository root for the duration of one decoder call."""
    token = _ROOT.set(root)
    try:
        yield
    finally:
        _ROOT.reset(token)


def max_table_rows() -> int:
    """`[decode] max_table_rows`, or the default.

    Never raises: a decoder runs inside a walk over thousands of documents, and
    a malformed `fux.toml` is reported by `config.load` on the paths that read
    configuration properly — failing the decode of every document as well would
    turn one bad line into an unreadable corpus.
    """
    from ..config import DEFAULT_MAX_TABLE_ROWS, load

    root = _ROOT.get()
    if root is None:
        return DEFAULT_MAX_TABLE_ROWS
    try:
        return load(root).max_table_rows
    except Exception:
        return DEFAULT_MAX_TABLE_ROWS
