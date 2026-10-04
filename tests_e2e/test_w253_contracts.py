"""W-253 through the shipped CLIs, Python and Node side by side.

`find --under` is a component boundary and `find --json` writes `confidence`
before `fused`. The two readers move in one change or the differential arm's
ranking lane goes red, so every assertion here is made on both.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from l12_fixtures import write_config

NODE = Path(__file__).resolve().parents[1] / "node" / "fux.mjs"


def _py(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "fux.cli", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=True,
    )


def _node(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["node", str(NODE), *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=True,
    )


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    sources = tmp_path / ".fux" / "sources"
    sources.mkdir(parents=True)
    (sources / "dirs").write_text("docs\n", encoding="utf-8")
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    write_config(tmp_path)
    (tmp_path / "docs" / "a").mkdir(parents=True)
    (tmp_path / "docs" / "a" / "x.md").write_text("# Cobalt\n\nCobalt alloy notes.\n", encoding="utf-8")
    (tmp_path / "docs" / "ab.md").write_text("# Cobalt sibling\n\nCobalt alloy sibling notes.\n", encoding="utf-8")
    _py(tmp_path, "ingest")
    return tmp_path


@pytest.mark.parametrize("run", [_py, _node], ids=["python", "node"])
def test_under_is_a_component_boundary(repo: Path, run) -> None:
    plain = run(repo, "find", "cobalt alloy").stdout.split()
    assert {"docs/a/x.md", "docs/ab.md"} <= set(plain), "precondition: both documents rank"

    for under in ("docs/a", "docs/a/"):
        kept = run(repo, "find", "cobalt alloy", "--under", under).stdout.split()
        assert kept == ["docs/a/x.md"], f"--under {under} must not match docs/ab.md"


@pytest.mark.parametrize("run", [_py, _node], ids=["python", "node"])
def test_find_json_writes_confidence_before_fused(repo: Path, run) -> None:
    out = run(repo, "find", "cobalt alloy", "-q", "cobalt notes", "--band", "--json").stdout
    keys = list(json.loads(out))
    assert keys == ["results", "confidence", "fused"], keys
