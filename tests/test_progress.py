"""The progress plane (W-64, ADR-CLI decision 9).

The load-bearing property is asserted end-to-end in
`tests_e2e/test_progress.py`: stdout is byte-identical with the bar on or off.
What is asserted here is the unit behaviour that property rests on — nothing
paints unless it should, and nothing is left half-painted when a phase dies.
"""

from __future__ import annotations

import io

import pytest

from fux.progress import NULL, THRESHOLD, Progress


class _Tty(io.StringIO):
    def isatty(self) -> bool:
        return True


def _big() -> int:
    return THRESHOLD + 1


def test_a_tty_stream_paints(monkeypatch):
    monkeypatch.delenv("FUX_NO_PROGRESS", raising=False)
    stream = _Tty()
    progress = Progress(stream=stream)
    with progress.phase("extract", _big()) as p:
        p.update(1)
    assert "extract" in stream.getvalue()
    assert f"1/{_big()}" in stream.getvalue()


def test_a_non_tty_stream_paints_nothing(monkeypatch):
    monkeypatch.delenv("FUX_NO_PROGRESS", raising=False)
    stream = io.StringIO()  # no isatty -> not a terminal
    progress = Progress(stream=stream)
    with progress.phase("extract", _big()) as p:
        p.update(1)
    assert stream.getvalue() == ""


def test_below_the_threshold_nothing_paints(monkeypatch):
    """A run where almost everything carries forward must not flash a bar."""
    monkeypatch.delenv("FUX_NO_PROGRESS", raising=False)
    stream = _Tty()
    with Progress(stream=stream).phase("extract", THRESHOLD) as p:
        p.update(THRESHOLD)
    assert stream.getvalue() == ""


def test_no_progress_beats_a_tty(monkeypatch):
    monkeypatch.delenv("FUX_NO_PROGRESS", raising=False)
    stream = _Tty()
    with Progress(no_progress=True, stream=stream).phase("extract", _big()) as p:
        p.update(1)
    assert stream.getvalue() == ""


def test_force_beats_a_pipe(monkeypatch):
    monkeypatch.delenv("FUX_NO_PROGRESS", raising=False)
    stream = io.StringIO()
    with Progress(force=True, stream=stream).phase("extract", _big()) as p:
        p.update(1)
    assert "extract" in stream.getvalue()


def test_the_env_var_disables_on_a_tty(monkeypatch):
    monkeypatch.setenv("FUX_NO_PROGRESS", "1")
    stream = _Tty()
    with Progress(stream=stream).phase("extract", _big()) as p:
        p.update(1)
    assert stream.getvalue() == ""


def test_the_env_var_set_to_zero_leaves_it_on(monkeypatch):
    """What the git hooks write: an explicit "checked, and left on" (W-64)."""
    monkeypatch.setenv("FUX_NO_PROGRESS", "0")
    stream = _Tty()
    with Progress(stream=stream).phase("extract", _big()) as p:
        p.update(1)
    assert "extract" in stream.getvalue()


def test_force_beats_the_env_var(monkeypatch):
    monkeypatch.setenv("FUX_NO_PROGRESS", "1")
    stream = io.StringIO()
    with Progress(force=True, stream=stream).phase("extract", _big()) as p:
        p.update(1)
    assert "extract" in stream.getvalue()


def test_a_completed_phase_commits_its_line(monkeypatch):
    monkeypatch.delenv("FUX_NO_PROGRESS", raising=False)
    stream = _Tty()
    with Progress(stream=stream).phase("extract", _big()) as p:
        p.update(_big())
    assert stream.getvalue().endswith("\n")


def test_an_interrupted_phase_leaves_no_partial_line(monkeypatch):
    """Ctrl-C already exits 130; it must not leave a half-painted bar."""
    monkeypatch.delenv("FUX_NO_PROGRESS", raising=False)
    stream = _Tty()
    progress = Progress(stream=stream)
    with pytest.raises(KeyboardInterrupt):
        with progress.phase("extract", _big()) as p:
            p.update(1)
            raise KeyboardInterrupt
    # The clear is `\r` + spaces + `\r`, so the terminal's last line is blank.
    assert stream.getvalue().endswith("\r")
    assert stream.getvalue().rsplit("\r", 2)[1].strip() == ""


def test_a_shrinking_line_is_padded_not_left_behind(monkeypatch):
    """`\\r` alone would leave the tail of a longer previous line on screen."""
    monkeypatch.delenv("FUX_NO_PROGRESS", raising=False)
    stream = _Tty()
    with Progress(stream=stream).phase("extract", _big()) as p:
        p.update(1, detail="a-very-long-document-path.md")
        p.update(1)
    frames = stream.getvalue().split("\r")
    assert len(frames[-2]) >= len(frames[-1].rstrip("\n"))


def test_a_long_detail_is_truncated_so_the_line_never_wraps(monkeypatch):
    """`\\r` returns to the start of the *terminal* line, so a wrapped line
    cannot be erased — the no-partial-line guarantee depends on this."""
    monkeypatch.delenv("FUX_NO_PROGRESS", raising=False)
    stream = _Tty()
    deep = "docs/" + "very-long-directory-name/" * 12 + "the-actual-document.md"
    with Progress(stream=stream).phase("extract", _big()) as p:
        p.update(1, detail=deep)
    for frame in stream.getvalue().split("\r"):
        assert len(frame.rstrip("\n")) <= 80


def test_truncation_keeps_the_end_of_the_path_and_marks_the_cut(monkeypatch):
    """The tail names the document; the leading directories do not."""
    monkeypatch.delenv("FUX_NO_PROGRESS", raising=False)
    stream = _Tty()
    with Progress(stream=stream).phase("extract", _big()) as p:
        p.update(1, detail="a/" * 60 + "findme.md")
    painted = stream.getvalue()
    assert "findme.md" in painted
    assert "…" in painted


def test_control_characters_in_a_path_cannot_break_the_line(monkeypatch):
    """A newline in a filename is legal on POSIX and would split the repaint
    into lines `\\r` can never take back."""
    monkeypatch.delenv("FUX_NO_PROGRESS", raising=False)
    stream = _Tty()
    with Progress(stream=stream).phase("extract", _big()) as p:
        p.update(1, detail="docs/evil\nname\rhere\x1b[2Jgone.md")
    painted = stream.getvalue()
    assert "\n" not in painted.rstrip("\n")
    assert "\x1b" not in painted
    assert painted.count("\r") == 2  # the two paints, and nothing else


def test_no_ansi_escape_sequences_anywhere(monkeypatch):
    """`\\r` + trailing spaces, not `\\x1b[2K` — old conhost has no ANSI."""
    monkeypatch.delenv("FUX_NO_PROGRESS", raising=False)
    stream = _Tty()
    with Progress(stream=stream).phase("extract", _big()) as p:
        p.update(1)
    assert "\x1b" not in stream.getvalue()


def test_a_unit_is_printed_when_the_count_is_not_documents(monkeypatch):
    """`252/252 shards` cannot be misread as losing 950 documents."""
    monkeypatch.delenv("FUX_NO_PROGRESS", raising=False)
    stream = _Tty()
    with Progress(stream=stream).phase("write", _big(), "shards") as p:
        p.update(1)
    assert f"1/{_big()} shards" in stream.getvalue()


def test_the_null_progress_is_inert():
    """`progress=None` everywhere means silent — every existing caller."""
    with NULL.phase("extract", 10_000, "shards") as p:
        p.update(500, detail="anything")
