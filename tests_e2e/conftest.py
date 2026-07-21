"""e2e fixtures: real CLI via subprocess, fixture corpus, normalized-JSON goldens.

Goldens compare *normalized* JSON (floats rounded to 3 dp, volatile provenance
keys stripped) and are updated deliberately with `FUX_UPDATE_GOLDENS=1` — never
regenerated blindly (CLAUDE.md).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

E2E_DIR = Path(__file__).parent
CORPUS = E2E_DIR / "corpus"
GOLDENS = E2E_DIR / "goldens"

_VOLATILE_KEYS = {"converted_at", "timestamp", "fux_version"}


def have_markitdown() -> bool:
    try:
        import markitdown  # noqa: F401

        return True
    except ImportError:
        return False


def run_fux(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        [sys.executable, "-m", "fux", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if check and proc.returncode != 0:
        raise AssertionError(
            f"fux {' '.join(args)} exited {proc.returncode}\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )
    return proc


@pytest.fixture
def project(tmp_path: Path) -> Path:
    proj = tmp_path / "proj"
    shutil.copytree(CORPUS, proj)
    run_fux(
        proj,
        "setup",
        "-y",
        "--docs", "docs,notes,office",
        "--code", "code",
        "--data", "data",
        "--images", "assets",
    )
    return proj


@pytest.fixture
def ingested(project: Path) -> Path:
    run_fux(project, "ingest")
    return project


@pytest.fixture
def ingested_sqlite(project: Path) -> Path:
    """The same corpus on the SQLite backend — for proving store parity."""
    config = project / "fux.toml"
    config.write_text(
        config.read_text(encoding="utf-8") + '\n[index]\nformat = "sqlite"\n',
        encoding="utf-8",
    )
    run_fux(project, "ingest")
    return project


def normalize(obj):
    if isinstance(obj, float):
        return round(obj, 3)
    if isinstance(obj, dict):
        return {k: normalize(v) for k, v in obj.items() if k not in _VOLATILE_KEYS}
    if isinstance(obj, list):
        return [normalize(v) for v in obj]
    return obj


def assert_golden(name: str, payload) -> None:
    actual = normalize(payload)
    path = GOLDENS / name
    if os.environ.get("FUX_UPDATE_GOLDENS"):
        path.write_text(
            json.dumps(actual, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return
    assert path.is_file(), f"golden {name} missing — run with FUX_UPDATE_GOLDENS=1"
    expected = json.loads(path.read_text(encoding="utf-8"))
    assert actual == expected, f"golden mismatch for {name}"


def fux_tree(proj: Path) -> dict[str, bytes]:
    return {
        p.relative_to(proj).as_posix(): p.read_bytes()
        for p in sorted((proj / ".fux").rglob("*"))
        if p.is_file()
    }
