"""Constitution layer — tier-aware blocking + the §5b migration baseline guard."""
from __future__ import annotations

from pathlib import Path

from fux import baseline, check, gate
from conftest import write_rule

REPO = Path(__file__).resolve().parents[1]

CON = """---
id: con-x
type: rule
status: active
tier: constitutional
code_refs: [src/missing.py]
---
**Rule:** must never break.
"""
STD = """---
id: std-x
type: rule
status: active
code_refs: [src/missing.py]
---
**Rule:** a normal convention.
"""


def _strict(project):
    (project / ".fux" / "config.toml").write_text('[fux]\nmode = "strict"\n', encoding="utf-8")


def test_constitutional_deadref_blocks_under_fix(project):
    """(a) any finding on a constitutional rule blocks regardless of mode (default=fix)."""
    write_rule(project, "con-x", CON)
    code, report = gate.run(project)            # default mode is "fix"
    assert code == 2 and "blocking" in report


def test_standard_deadref_blocks_only_under_strict(project):
    """(b) a standard-tier dead-ref does NOT block outside strict; it does under strict."""
    write_rule(project, "std-x", STD)
    code, _ = gate.run(project)
    assert code == 0                            # fix mode → standard dead-ref is non-blocking
    _strict(project)
    code, _ = gate.run(project)
    assert code == 2                            # strict mode → standard dead-ref blocks


def test_fux_own_rules_parse_and_validate():
    """(c) backward-compat: every existing rule in fux's .fux/ still parses + validates."""
    from fux import frontmatter, schema
    mds = list((REPO / ".fux" / "rules").glob("*.md"))
    assert mds, "expected fux's own rules to be present"
    for p in mds:
        fm, _ = frontmatter.split(p.read_text(encoding="utf-8"))
        assert schema.validate(fm) == [], f"{p.name}: {schema.validate(fm)}"
    fm, _ = frontmatter.split((REPO / ".fux" / "rules" / "con-amendment.md").read_text())
    assert fm["tier"] == "constitutional"


def test_baseline_guard_unchanged_then_new_blocker(project, tmp_path):
    """(d) baseline-write then gate --baseline: unchanged → 0; a new blocker → 2."""
    write_rule(project, "std-x", STD)           # a pre-existing (non-blocking) dead-ref
    snap = tmp_path / "baseline.txt"
    baseline.write(snap, check.run(project))
    code, _ = gate.run(project, baseline=snap)
    assert code == 0                            # nothing new since the snapshot
    write_rule(project, "con-x", CON)           # NEW constitutional dead-ref after snapshot
    code, report = gate.run(project, baseline=snap)
    assert code == 2 and "new (vs baseline)" in report
