"""Unit-suite-wide fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _reset_debug_state(monkeypatch):
    """`config.load()` configures the global debug emitter as a side effect
    (handoff 0005) — reset it around every test so one test's `[debug]` toml
    (or a stray FUX_DEBUG env var) can never leak into the next.
    """
    from fux import debug

    monkeypatch.delenv("FUX_DEBUG", raising=False)
    debug.reset()
    yield
    debug.reset()
