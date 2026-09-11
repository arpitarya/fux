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

The value lives in `.fux/tune.toml [index]` (moved from `fux.toml [decode]` on
2026-09-11, Arpit — ADR-TUNE decision 13). That file is **committed**, so `same
sources -> same index` becomes `same sources + same committed [index] -> same
index`. `[index]` is the one tune.toml table that changes what is **indexed**,
and it is read through `tune.index_limits()`, which `--no-tune` never reaches:
`refer` decodes fetched bytes here too, and must decode them under the value the
index was built with.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

__all__ = ["bound_root", "max_table_rows"]

#: ⚠ The default lives in `tune.py`, not here, and is read lazily below:
#: `fux.tune` pulls in the query package, and this file must stay cheap to
#: import from a consumer decoder loaded by path.

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
    """`.fux/tune.toml [index] max_table_rows`, or the default.

    Never raises: a decoder runs inside a walk over thousands of documents, and
    a malformed `[index]` is reported by `tune.index_limits()` where ingest
    reads it first — failing the decode of every document as well would turn
    one bad line into an unreadable corpus (ADR-TABULAR decision 6).
    """
    from ..tune import DEFAULT_MAX_TABLE_ROWS, index_limits

    root = _ROOT.get()
    if root is None:
        return DEFAULT_MAX_TABLE_ROWS
    try:
        return index_limits(root).max_table_rows
    except Exception:
        return DEFAULT_MAX_TABLE_ROWS
