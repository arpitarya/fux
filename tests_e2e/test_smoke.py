"""M0 smoke: the real CLI via subprocess, not the in-process API."""

from __future__ import annotations

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
