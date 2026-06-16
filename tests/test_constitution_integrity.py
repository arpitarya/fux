"""Constitution layer — Phase 2: tamper-evidence, ratification, and the lock ($0)."""
from __future__ import annotations

from fux import check, config, constitution, gate, loader, paths
from conftest import write_rule

CON = """---
id: con-r
type: rule
status: active
tier: constitutional
---
**Rule:** money docs are never committed; plans live in elgar.
"""
STD = """---
id: std-r
type: rule
status: active
code_refs: [src/missing.py]
---
**Rule:** a normal convention.
"""


def _ratify(project, rid, by="Arpit", date="2026-06-17"):
    cfg = config.load(paths.Footprint(project).config)
    rules = loader.resolve(project, cfg).rules
    return constitution.ratify(project, rules, rid, by=by, date=date)


def test_ratify_then_clean(project):
    write_rule(project, "con-r", CON)
    _ratify(project, "con-r")
    assert (project / ".fux" / "constitution.lock").exists()
    code, _ = gate.run(project)
    assert code == 0                                   # ratified + untouched → clean


def test_tamper_on_body_blocks(project):
    write_rule(project, "con-r", CON)
    _ratify(project, "con-r")
    p = project / ".fux" / "rules" / "con-r.md"
    p.write_text(p.read_text().replace("never committed", "always committed"), encoding="utf-8")
    code, report = gate.run(project)
    assert code == 2 and "tampered" in report          # body edit → content_seal mismatch


def test_delete_ratified_rule_lock_mismatch_blocks(project):
    write_rule(project, "con-r", CON)
    _ratify(project, "con-r")
    (project / ".fux" / "rules" / "con-r.md").unlink()
    code, report = gate.run(project)
    assert code == 2 and "tampered" in report          # lock has con-r, disk doesn't


def test_only_ratify_mutates_lock(project):
    write_rule(project, "con-r", CON)
    _ratify(project, "con-r")
    lock = project / ".fux" / "constitution.lock"
    before = lock.read_text()
    gate.run(project)                                  # enforcement does NOT rewrite the lock
    check.run(project)
    assert lock.read_text() == before
    write_rule(project, "con-s", CON.replace("con-r", "con-s"))
    _ratify(project, "con-s")                          # only ratify mutates it
    after = lock.read_text()
    assert after != before and "con-s" in after


def test_non_constitutional_rules_unaffected(project):
    write_rule(project, "std-r", STD)
    findings = check.run(project)
    assert not [f for f in findings if f.kind == "tampered"]   # tamper/lock skip standard
    code, _ = gate.run(project)
    assert code == 0                                   # standard dead-ref is non-blocking under fix
