"""Layered resolution + conflict detection (plan §5)."""
from __future__ import annotations

import os
from pathlib import Path

from fux import check, loader, paths
from conftest import write_rule

RULE = """---
id: shared-id
type: rule
status: active
created: 2026-06-01
updated: 2026-06-01
---
**Rule:** {who} wins.
"""


def test_project_overrides_global(tmp_path, monkeypatch, project):
    # Put a same-id rule in the (env-pointed) global layer and the project.
    global_rules = Path(os.environ["FUX_GLOBAL"]) / "rules"
    (global_rules / "shared-id.md").write_text(RULE.format(who="global"), encoding="utf-8")
    write_rule(project, "shared-id", RULE.format(who="project"))
    rs = loader.resolve(project)
    winner = rs.by_id()["shared-id"]
    assert winner.layer == "project"
    assert "project wins" in winner.body


def test_conflict_flagged_not_silently_shadowed(project, monkeypatch):
    global_rules = Path(os.environ["FUX_GLOBAL"]) / "rules"
    (global_rules / "shared-id.md").write_text(RULE.format(who="global"), encoding="utf-8")
    write_rule(project, "shared-id", RULE.format(who="project"))
    findings = check.run(project)
    assert any(f.kind == "conflict" and f.rule_id == "shared-id" for f in findings)
