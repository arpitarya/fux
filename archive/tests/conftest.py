"""Shared fixtures. Isolate the global/packs layers so counts are deterministic;
point the schema at the repo's schema.json regardless of install state.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))


@pytest.fixture(autouse=True)
def _isolated_layers(tmp_path, monkeypatch):
    """Empty global+packs by default so tests see only their project rules."""
    empty_global = tmp_path / "global"
    empty_packs = tmp_path / "packs"
    (empty_global / "rules").mkdir(parents=True)
    empty_packs.mkdir(parents=True)
    monkeypatch.setenv("FUX_GLOBAL", str(empty_global))
    monkeypatch.setenv("FUX_PACKS", str(empty_packs))
    monkeypatch.setenv("FUX_SCHEMA", str(REPO / "fux" / "data" / "schema.json"))
    # Isolate from any real ~/.claude install so hook wiring is deterministic.
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude_home"))
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex_home"))


@pytest.fixture
def project(tmp_path):
    """A bare initialised project root with a .fux/ footprint."""
    from fux import initcmd
    root = tmp_path / "proj"
    (root / "src").mkdir(parents=True)
    monkeypatch_cwd(root)
    initcmd.run(root)
    return root


def monkeypatch_cwd(path: Path) -> None:
    os.chdir(path)


def write_rule(root: Path, name: str, text: str) -> Path:
    target = root / ".fux" / "rules" / f"{name}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target
