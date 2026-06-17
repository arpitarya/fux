"""`fux constitution` status view — what's constitutional, what it governs, violations ($0)."""
from __future__ import annotations

from fux import config, constatus, constitution, loader, paths
from conftest import write_rule

CON = """---
id: con-r
type: rule
status: active
tier: constitutional
domain: finance
---
**Rule:** money amounts are integer cents, never floats.
"""


def _ratify(project, rid):
    cfg = config.load(paths.Footprint(project).config)
    rules = loader.resolve(project, cfg).rules
    return constitution.ratify(project, rules, rid, by="Arpit", date="2026-06-17")


def test_empty_apex(project):
    out = constatus.render(project)
    assert "no constitutional rules" in out


def test_ratified_rule_shown_clean(project):
    write_rule(project, "con-r", CON)
    _ratify(project, "con-r")
    out = constatus.render(project)
    assert "con-r" in out and "ratified" in out
    assert "domain: finance" in out               # what it governs
    assert "apex clean" in out                     # no violations


def test_unratified_rule_flagged(project):
    write_rule(project, "con-r", CON)              # never ratified
    out = constatus.render(project)
    assert "UN-RATIFIED" in out
    assert "blocking violations" in out            # the un-ratified-tier finding surfaces


def test_tamper_surfaces_as_violation(project):
    write_rule(project, "con-r", CON)
    _ratify(project, "con-r")
    p = project / ".fux" / "rules" / "con-r.md"
    p.write_text(p.read_text().replace("integer cents", "floats"), encoding="utf-8")
    out = constatus.render(project)
    assert "tampered" in out and "blocking violations" in out
