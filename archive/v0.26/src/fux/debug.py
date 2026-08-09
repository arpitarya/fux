"""The debug emitter (handoff 0005) — structured, stderr/file-only, never stdout.

Three calls cover every instrumentation site:

    dbg(category, level, msg, **fields)   # structured line; fields become key=value
    timer(category, label)                # context manager; no-ops unless timing
    is_enabled(category, level) -> bool   # guard expensive formatting at call sites

Precedence for the *level* only: ``--debug[=LEVEL]`` (CLI flag) >
``FUX_DEBUG=<level|1>`` (env) > ``[debug] level`` (fux.toml) > ``off``.
``categories``/``output``/``timing``/``redact``/``max_bytes`` have no flag/env
override — toml is their only source, resolved by :func:`apply_config`.

Hand-rolled rather than stdlib ``logging``: the precedence rule (flag beats env
beats toml) and the max_bytes truncate-with-notice behaviour are simpler to keep
deterministic and stdout-safe as a plain module than to bolt onto ``logging``'s
handler/formatter machinery (open question 1 → ADR 0012).
"""

from __future__ import annotations

import os
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

LEVELS = ("off", "info", "debug", "trace")
_RANK = {level: i for i, level in enumerate(LEVELS)}

CATEGORIES = frozenset(
    {
        "config", "walk", "convert", "chunk", "index", "state", "lock",
        "query", "lexical", "dense", "graph", "answer", "hooks", "web",
    }
)


@dataclass
class _State:
    level: str = "off"
    categories: frozenset[str] = field(default_factory=lambda: frozenset({"*"}))
    output: str = "stderr"
    timing: bool = False
    redact: bool = True
    max_bytes: int = 5_000_000
    level_source: str = "default"  # default | env | flag | toml


_state = _State()
_file_streams: dict[str, TextIO] = {}
_bytes_written = 0
_truncated = False
_warned_unwritable = False
_warned_redact_off = False


def reset() -> None:
    """Restore module-global state — tests only; a real process inits once."""
    global _state, _file_streams, _bytes_written, _truncated
    global _warned_unwritable, _warned_redact_off
    for stream in _file_streams.values():
        if stream is not sys.stderr:
            try:
                stream.close()
            except OSError:
                pass
    _state = _State()
    _file_streams = {}
    _bytes_written = 0
    _truncated = False
    _warned_unwritable = False
    _warned_redact_off = False


def init_from_cli(flag_level: str | None) -> None:
    """Call once, early in ``cli.main()``, before config loads.

    Resolves the CLI-flag half of the precedence chain so tracing works even
    for commands that fail before ``fux.toml`` is read (e.g. a missing config).
    The env var is handled by :func:`apply_config` too, so library callers who
    never go through ``cli.main`` still get ``FUX_DEBUG`` back-compat.
    """
    global _state
    if flag_level is not None:
        _state = _State(level=_normalize(flag_level), level_source="flag")


def apply_config(debug_params) -> None:
    """Call once config has loaded; toml only wins the level if flag/env didn't."""
    global _state, _warned_redact_off
    if _state.level_source in ("flag", "env"):
        level, source = _state.level, _state.level_source
    else:
        env = os.environ.get("FUX_DEBUG")
        level, source = (_normalize_env(env), "env") if env else (debug_params.level, "toml")
    _state = _State(
        level=level,
        categories=frozenset(debug_params.categories),
        output=debug_params.output,
        timing=debug_params.timing,
        redact=debug_params.redact,
        max_bytes=debug_params.max_bytes,
        level_source=source,
    )
    if not _state.redact and _state.level != "off" and not _warned_redact_off:
        print(
            "fux: [debug] redact = false — document content may be logged",
            file=sys.stderr,
        )
        _warned_redact_off = True


def _normalize(level: str) -> str:
    level = level.strip().lower()
    return level if level in LEVELS else "debug"


def _normalize_env(val: str) -> str:
    val = val.strip().lower()
    if val in LEVELS:
        return val
    return "debug"  # back-compat: FUX_DEBUG=1 (or any other truthy value) means debug


def is_enabled(category: str, level: str) -> bool:
    if _state.level == "off":
        return False
    if _RANK[level] > _RANK[_state.level]:
        return False
    return "*" in _state.categories or category in _state.categories


def redact_on() -> bool:
    return _state.redact


def dbg(category: str, level: str, msg: str, **fields) -> None:
    if not is_enabled(category, level):
        return
    _emit(category, level, msg, fields)


@contextmanager
def timer(category: str, label: str):
    if not _state.timing or not is_enabled(category, "info"):
        yield
        return
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 3)
        _emit(category, "info", f"{label} done", {"elapsed_ms": elapsed_ms})


def _format(category: str, level: str, msg: str, fields: dict) -> str:
    tail = " ".join(f"{k}={v}" for k, v in fields.items())
    return f"[{category}] {level}: {msg}" + (f" {tail}" if tail else "")


def _get_stream() -> TextIO:
    global _warned_unwritable
    if _state.output == "stderr":
        return sys.stderr
    cached = _file_streams.get(_state.output)
    if cached is not None:
        return cached
    try:
        path = Path(_state.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        stream = open(path, "a", encoding="utf-8")
    except (OSError, ValueError) as exc:
        if not _warned_unwritable:
            print(
                f"fux: debug output {_state.output!r} is unwritable ({exc}) "
                "— falling back to stderr",
                file=sys.stderr,
            )
            _warned_unwritable = True
        stream = sys.stderr
    _file_streams[_state.output] = stream
    return stream


def _emit(category: str, level: str, msg: str, fields: dict) -> None:
    global _bytes_written, _truncated
    if _truncated:
        return
    line = _format(category, level, msg, fields)
    data = (line + "\n").encode("utf-8")
    stream = _get_stream()
    if _bytes_written + len(data) > _state.max_bytes:
        _truncated = True
        stream.write(
            f"[debug] output truncated at max_bytes={_state.max_bytes} "
            "— raise [debug] max_bytes to see more\n"
        )
        stream.flush()
        return
    stream.write(line + "\n")
    stream.flush()
    _bytes_written += len(data)
