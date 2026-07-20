"""Schema validation, scaffolding, and idempotent init wiring."""
from __future__ import annotations

import argparse
import json

import pytest

from fux import clicmds, initcmd, scaffold, paths, schema, settings
from conftest import monkeypatch_cwd


def test_schema_rejects_bad_enum_and_missing_required():
    assert any("type" in e for e in schema.validate({"id": "x", "type": "nope", "status": "active"}))
    assert any("missing required field" in e for e in schema.validate({"id": "x"}))
    assert schema.validate({"id": "ok-id", "type": "rule", "status": "active"}) == []


def test_scaffold_creates_valid_stub(project):
    monkeypatch_cwd(project)
    target = scaffold.make(project, "formula", "my-calc", domain="portfolio")
    assert target.exists()
    from fux import frontmatter
    fm, body = frontmatter.split(target.read_text())
    assert fm["type"] == "formula" and fm["id"] == "my-calc"
    assert schema.validate(fm) == []
    with pytest.raises(FileExistsError):
        scaffold.make(project, "formula", "my-calc")


def test_scaffold_rejects_unknown_type(project):
    with pytest.raises(ValueError):
        scaffold.make(project, "banana", "x")


def test_init_wires_hooks_idempotently(tmp_path):
    root = tmp_path / "p"
    (root).mkdir()
    initcmd.run(root)
    initcmd.run(root)  # second time must not duplicate
    data = json.loads((root / ".claude" / "settings.json").read_text())
    cmds = [h["command"] for e in data["hooks"]["SessionStart"] for h in e["hooks"]]
    assert len(cmds) == 1 and "fux" in cmds[0]   # exactly one Fux hook, not duplicated
    assert "<!-- fux:start -->" in (root / "CLAUDE.md").read_text()
    assert "<!-- fux:agents:start -->" in (root / "AGENTS.md").read_text()
    assert "<!-- fux:copilot:start -->" in (
        root / ".github" / "copilot-instructions.md").read_text()
    assert (root / ".github" / "prompts" / "fux.prompt.md").exists()
    assert (root / ".github" / "prompts" / "fux-plan.prompt.md").exists()


def test_setup_installs_codex_skills(tmp_path, capsys):
    assert clicmds.cmd_setup(argparse.Namespace()) == 0
    assert (paths.codex_home() / "skills" / "fux" / "SKILL.md").exists()
    assert (paths.codex_home() / "skills" / "fux-plan" / "SKILL.md").exists()
    out = capsys.readouterr().out
    assert "codex skills" in out
