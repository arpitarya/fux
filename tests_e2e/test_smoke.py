"""M0 smoke: the real CLI via subprocess, not the in-process API."""

from __future__ import annotations

import os
import subprocess
import sys

from fux import __version__


def test_fux_version_via_subprocess():
    result = subprocess.run(
        [sys.executable, "-m", "fux.cli", "--version"], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == f"fux {__version__}"


def test_fux_doctor_via_subprocess(tmp_path):
    (tmp_path / ".git").mkdir()
    result = subprocess.run(
        [sys.executable, "-m", "fux.cli", "doctor"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0
    assert "python version" in result.stdout


def test_fux_doctor_output_is_ascii_safe(tmp_path):
    """A non-ASCII character (e.g. a Unicode checkmark) crashes Windows'
    default console codepage ('charmap' can't encode U+2714) — the process
    exits 1 with a UnicodeEncodeError instead of printing. Force the
    strictest plausible stdout encoding to catch this on any platform."""
    (tmp_path / ".git").mkdir()
    env = {**os.environ, "PYTHONIOENCODING": "ascii"}
    result = subprocess.run(
        [sys.executable, "-m", "fux.cli", "doctor"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    result.stdout.encode("ascii")  # raises if anything non-ASCII slipped through
