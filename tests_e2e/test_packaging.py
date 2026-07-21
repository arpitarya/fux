"""Packaging: the wheel ships the model bundle and stays inside the size budget."""

from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

REPO = Path(__file__).parent.parent


def test_wheel_ships_bundle_under_budget(tmp_path):
    proc = subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(tmp_path)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    wheel = next(tmp_path.glob("*.whl"))
    assert wheel.stat().st_size <= 15 * 1024 * 1024  # wheel budget (handoff 0003)
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        assert "fux/embed/data/model.bin" in names
        info = archive.getinfo("fux/embed/data/model.bin")
        assert info.file_size <= 10 * 1024 * 1024  # bundle budget, hard
