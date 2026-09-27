"""The one place a decoder can read committed configuration.

## Why this exists, and why it is not a parameter

A decoder is `EXTENSIONS` plus `decode(raw, rel_path)` — two names, and
[SR-DECODE](../../../records/0139_decode.md) decision 1 is emphatic that the
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
2026-09-11, Arpit — SR-TUNE decision 13). That file is **committed**, so `same
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

__all__ = ["bound_root", "max_table_rows", "limit", "check", "digest_lines", "template_limits"]

#: ⚠ The default lives in `tune.py`, not here, and is read lazily below:
#: `fux.tune` pulls in the query package, and this file must stay cheap to
#: import from a consumer decoder loaded by path.

_ROOT: ContextVar[Path | None] = ContextVar("fux_decode_root", default=None)
#: The bound repository's `[limits]`, loaded once per bind — `limit()` runs per
#: CSV cell, so it must be a dict lookup and never a file read.
_LIMITS: ContextVar[dict | None] = ContextVar("fux_decode_limits", default=None)
#: `(path, mtime_ns, size) -> [limits]`, so a walk over thousands of documents
#: parses `.fux/formats.toml` once, not once per document.
_CACHE: dict[tuple, dict] = {}


@contextmanager
def bound_root(root: Path | None):
    """Bind the repository root — and its decoder caps — for one decoder call."""
    token = _ROOT.set(root)
    limits_token = _LIMITS.set(_load(root) if root is not None else None)
    try:
        yield
    finally:
        _LIMITS.reset(limits_token)
        _ROOT.reset(token)


def _load(root: Path) -> dict | None:
    """`.fux/formats.toml [limits]`, or `None` when the file is absent — which
    `limit()` then reports, so a decoder that reads no cap never needs the file."""
    from ..constants import fixed
    from ..ingest import typesfile

    path = root / fixed("files", "formats")
    try:
        stamp = path.stat()
    except OSError:
        return None
    key = (str(path), stamp.st_mtime_ns, stamp.st_size)
    if key not in _CACHE:
        _CACHE.clear()
        _CACHE[key] = typesfile.read(root).limits
    return _CACHE[key]


#: What a missing key's error tells the reader to do — `tune.py`'s sentence.
_FIX_HINT = "`fux doctor --fix` writes every missing key from the template `fux setup` uses"


def limit(decoder: str, key: str) -> int:
    """`.fux/formats.toml [limits.<decoder>] <key>` — there is no default (L12).

    W-225 stage 4a (SR-LAW-12 decision 9b). Each built-in decoder reads its
    caps here instead of holding them as module constants, and every cap is in
    the extract-config digest, so an edited value re-extracts the corpus.
    """
    from ..constants import fixed
    from ..errors import FuxError

    limits = _LIMITS.get()
    if limits is None:
        where = "no repository in context" if _ROOT.get() is None else f"no {fixed('files', 'formats')}"
        raise FuxError(
            f"the {decoder} decoder asked for [limits.{decoder}] {key} with {where} - it is "
            f"read from .fux/formats.toml, and fux holds no copy of it in code. {_FIX_HINT}"
        )
    try:
        return limits[decoder][key]
    except KeyError:
        raise FuxError(
            f"{fixed('files', 'formats')}:\n  [limits.{decoder}] {key} is missing\n  {_FIX_HINT}"
        ) from None


def template_limits() -> dict:
    """The packaged `[limits]` — every cap a built-in decoder reads."""
    import tomllib

    return tomllib.loads(_template_text())["limits"]


def _template_text() -> str:
    from importlib import resources

    from ..constants import fixed

    return (resources.files("fux") / "templates" / fixed("templates", "formats_limits")).read_text(
        encoding="utf-8"
    )


def check(root: Path) -> None:
    """Every cap the built-in decoders read is present — ONE error naming each
    missing key, raised where ingest starts, before any decoder runs (the
    `[index]` precedent, SR-TABULAR decision 6)."""
    from ..constants import fixed
    from ..errors import FuxError
    from ..ingest import typesfile

    have = typesfile.read(root).limits
    missing = [
        f"[limits.{name}] {key} is missing"
        for name, keys in template_limits().items()
        for key in keys
        if key not in have.get(name, {})
    ]
    if missing:
        raise FuxError(f"{fixed('files', 'formats')}:\n  " + "\n  ".join(missing) + f"\n  {_FIX_HINT}")


def digest_lines(root: Path) -> str:
    """Every cap the built-ins read, as `limits.<decoder>.<key>=<value>` lines in
    sorted order — the extract-config digest's share (SR-LAW-12 decision 9b).

    Only the keys the built-ins read: a consumer's extra table changes nothing
    fux extracts, so it must not force a re-extraction."""
    from ..ingest import typesfile

    have = typesfile.read(root).limits
    return "\n".join(
        f"limits.{name}.{key}={have[name][key]}"
        for name, keys in sorted(template_limits().items())
        for key in sorted(keys)
    )


def max_table_rows() -> int:
    """`.fux/tune.toml [index] max_table_rows` — there is no default (L12).

    A malformed or missing `[index]` is reported by `tune.index_limits()` where
    ingest reads it first, before any decoder runs, so a walk over thousands of
    documents stops once, at the top, naming the key (SR-TABULAR decision 6).
    A decode with no repository in context has no file to read the cap from,
    and says so rather than inventing one.
    """
    from ..errors import FuxError
    from ..tune import index_limits

    root = _ROOT.get()
    if root is None:
        raise FuxError(
            "a decoder asked for [index] max_table_rows with no repository in context - "
            "it is read from .fux/tune.toml, and fux holds no copy of it in code"
        )
    return index_limits(root).max_table_rows
