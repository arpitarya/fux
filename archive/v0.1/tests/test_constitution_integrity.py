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


def test_supersession_keeps_predecessor_sealed_and_gate_clean(project):
    # The F3 amendment shape: change a constitutional rule by SUPERSESSION, not in-place edit.
    # Predecessor is deprecated + re-sealed; successor is ratified; both stay in the lock; clean.
    v1 = ("---\nid: con-v1\ntype: rule\nstatus: active\ntier: constitutional\n---\n"
          "**Rule:** the founding article.\n")
    write_rule(project, "con-v1", v1)
    _ratify(project, "con-v1")
    # Author the successor (single-concern additive change), deprecate + re-seal the predecessor.
    v2 = ("---\nid: con-v2\ntype: rule\nstatus: active\ntier: constitutional\n"
          "edges:\n  supersedes:\n    - con-v1\n---\n**Rule:** the founding article, plus a clause.\n")
    write_rule(project, "con-v2", v2)
    dep = ("---\nid: con-v1\ntype: rule\nstatus: deprecated\ntier: constitutional\n"
           "edges:\n  superseded-by:\n    - con-v2\n---\n**Rule:** the founding article.\n")
    write_rule(project, "con-v1", dep)
    _ratify(project, "con-v1")                         # re-seal the deprecated frontmatter
    _ratify(project, "con-v2")                         # ratify the successor
    lock = (project / ".fux" / "constitution.lock").read_text()
    assert "con-v1" in lock and "con-v2" in lock       # both on the record, sealed
    code, report = gate.run(project)
    assert code == 0, report                            # supersession lands clean — no tamper
