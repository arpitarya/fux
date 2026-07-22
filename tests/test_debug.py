"""Unit suite for the debug emitter (`fux.debug`, handoff 0005).

Every existing golden must stay byte-identical with debug active — see
`tests_e2e/test_determinism.py::test_debug_trace_does_not_touch_stdout` for
that hard gate. This file covers the emitter's own contract: precedence,
levels/categories, redaction, truncation, and unwritable-output fallback.
"""

from __future__ import annotations

from fux import debug
from fux.config import DebugParams


def _params(**overrides) -> DebugParams:
    return DebugParams(**{**DebugParams().__dict__, **overrides})


# -- is_enabled --------------------------------------------------------------


def test_off_by_default():
    assert debug._state.level == "off"
    assert not debug.is_enabled("query", "info")


def test_level_ordinal_gates_emission():
    debug.apply_config(_params(level="debug"))
    assert debug.is_enabled("query", "info")
    assert debug.is_enabled("query", "debug")
    assert not debug.is_enabled("query", "trace")


def test_category_filter():
    debug.apply_config(_params(level="trace", categories=("query", "dense")))
    assert debug.is_enabled("query", "trace")
    assert debug.is_enabled("dense", "trace")
    assert not debug.is_enabled("graph", "trace")


def test_wildcard_category_matches_everything():
    debug.apply_config(_params(level="trace", categories=("*",)))
    assert debug.is_enabled("graph", "trace")
    assert debug.is_enabled("anything-not-a-real-category", "trace")


# -- dbg(): stdout purity + stderr content ------------------------------------


def test_dbg_never_writes_stdout(capsys):
    debug.apply_config(_params(level="trace"))
    debug.dbg("query", "trace", "candidate scored", doc="a.md", score=1.234)
    out, err = capsys.readouterr()
    assert out == ""
    assert "candidate scored" in err
    assert "doc=a.md" in err
    assert "score=1.234" in err


class _Boom:
    """A value whose formatting would blow up a careless `off` fast-path."""

    def __format__(self, spec):
        raise AssertionError("off must be free: a field was formatted while disabled")

    def __str__(self):
        raise AssertionError("off must be free: a field was formatted while disabled")


def test_off_never_formats_fields():
    debug.apply_config(_params(level="off"))
    debug.dbg("query", "trace", "msg", value=_Boom())  # must not raise


def test_dbg_silent_when_disabled(capsys):
    debug.apply_config(_params(level="info"))
    debug.dbg("query", "trace", "should not appear")
    out, err = capsys.readouterr()
    assert out == err == ""


def test_field_order_is_stable(capsys):
    debug.apply_config(_params(level="trace"))
    debug.dbg("query", "trace", "msg", b_field=2, a_field=1)
    _, err = capsys.readouterr()
    assert err.index("b_field") < err.index("a_field")  # insertion order, not sorted


# -- timer(): no wall-clock unless timing=true --------------------------------


def test_timer_noop_without_timing(capsys):
    debug.apply_config(_params(level="trace", timing=False))
    with debug.timer("index", "build"):
        pass
    out, err = capsys.readouterr()
    assert out == err == ""


def test_timer_emits_when_timing_enabled(capsys):
    debug.apply_config(_params(level="info", timing=True))
    with debug.timer("index", "build"):
        pass
    _, err = capsys.readouterr()
    assert "build done" in err
    assert "elapsed_ms=" in err


def test_timer_respects_category_filter(capsys):
    debug.apply_config(_params(level="info", timing=True, categories=("query",)))
    with debug.timer("index", "build"):  # not in categories
        pass
    _, err = capsys.readouterr()
    assert err == ""


# -- precedence: flag > env > toml > off --------------------------------------


def test_flag_beats_toml():
    debug.init_from_cli("trace")
    debug.apply_config(_params(level="off"))
    assert debug._state.level == "trace"
    assert debug._state.level_source == "flag"


def test_env_beats_toml(monkeypatch):
    monkeypatch.setenv("FUX_DEBUG", "info")
    debug.apply_config(_params(level="off"))
    assert debug._state.level == "info"
    assert debug._state.level_source == "env"


def test_env_back_compat_1_means_debug(monkeypatch):
    monkeypatch.setenv("FUX_DEBUG", "1")
    debug.apply_config(_params(level="off"))
    assert debug._state.level == "debug"


def test_toml_used_when_no_flag_or_env(monkeypatch):
    monkeypatch.delenv("FUX_DEBUG", raising=False)
    debug.apply_config(_params(level="trace"))
    assert debug._state.level == "trace"
    assert debug._state.level_source == "toml"


def test_flag_beats_env(monkeypatch):
    monkeypatch.setenv("FUX_DEBUG", "info")
    debug.init_from_cli("trace")
    debug.apply_config(_params(level="off"))
    assert debug._state.level == "trace"
    assert debug._state.level_source == "flag"


# -- redaction -----------------------------------------------------------------


def test_redact_off_warns_once(capsys):
    debug.apply_config(_params(level="debug", redact=False))
    _, err1 = capsys.readouterr()
    assert "redact = false" in err1
    debug.dbg("query", "debug", "another line")
    _, err2 = capsys.readouterr()
    assert "redact = false" not in err2  # warned once, not per line


def test_redact_on_by_default():
    debug.apply_config(_params())
    assert debug.redact_on() is True


# -- max_bytes truncation ------------------------------------------------------


def test_truncates_with_notice_not_silently(capsys):
    debug.apply_config(_params(level="trace", max_bytes=10))
    debug.dbg("query", "trace", "a longer line than the cap allows")
    debug.dbg("query", "trace", "a second line that must never appear")
    _, err = capsys.readouterr()
    assert "truncated" in err
    assert "second line" not in err


# -- unwritable output path ----------------------------------------------------


def test_unwritable_output_falls_back_to_stderr(capsys, tmp_path):
    bogus = tmp_path / "no-such-dir" / ".." / ".." / "\0invalid"  # will fail to open
    debug.apply_config(_params(level="trace", output=str(bogus)))
    debug.dbg("query", "trace", "still gets through")
    out, err = capsys.readouterr()
    assert out == ""
    assert "still gets through" in err
    assert "unwritable" in err


def test_file_output_writes_to_the_configured_path(tmp_path):
    target = tmp_path / "debug.log"
    debug.apply_config(_params(level="trace", output=str(target)))
    debug.dbg("query", "trace", "written to file")
    debug.reset()  # flush/close before reading
    assert "written to file" in target.read_text(encoding="utf-8")
