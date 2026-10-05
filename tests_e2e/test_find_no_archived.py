"""W-262 #3 — `fux find --no-archived`, through both shipped CLIs.

A REMOVE-only filter on the DECLARED `archived` fact ([SR-FIND](../records/0104_find.md)
decision 7's shape), with the confidence band computed on the UNFILTERED ranking
(decision 9). Every assertion is made on Python and Node alike, because the two
readers move in one change or the differential arm's ranking lane goes red.
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
    (sources / "dirs").write_text("docs\nold archived=true\n", encoding="utf-8")
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    write_config(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "old").mkdir()
    (tmp_path / "docs" / "live.md").write_text("# Cobalt\n\nCobalt alloy notes.\n", encoding="utf-8")
    (tmp_path / "old" / "retired.md").write_text(
        "# Cobalt, retired\n\nCobalt alloy notes from before.\n", encoding="utf-8")
    _py(tmp_path, "ingest")
    return tmp_path


@pytest.mark.parametrize("run", [_py, _node], ids=["python", "node"])
def test_no_archived_removes_only_the_declared_archived_documents(repo: Path, run) -> None:
    plain = run(repo, "find", "cobalt alloy").stdout.split()
    assert set(plain) == {"docs/live.md", "old/retired.md"}, "precondition: both rank"

    done = run(repo, "find", "cobalt alloy", "--no-archived")
    assert done.stdout.split() == ["docs/live.md"]
    assert "[filter] --no-archived removed 1 of the ranked results" in done.stderr


@pytest.mark.parametrize("run", [_py, _node], ids=["python", "node"])
def test_the_band_describes_the_unfiltered_ranking(repo: Path, run) -> None:
    full = json.loads(run(repo, "find", "cobalt alloy", "--band", "--json").stdout)
    cut = json.loads(run(repo, "find", "cobalt alloy", "--band", "--json", "--no-archived").stdout)
    assert [r["loc"] for r in cut["results"]] == ["docs/live.md"]
    assert all(not r["archived"] for r in cut["results"])
    assert cut["confidence"] == full["confidence"], "SR-FIND decision 9: band is computed unfiltered"


def test_both_readers_agree(repo: Path) -> None:
    py = _py(repo, "find", "cobalt alloy", "--json", "--no-archived").stdout
    node = _node(repo, "find", "cobalt alloy", "--json", "--no-archived").stdout
    assert json.loads(py) == json.loads(node)
