"""Dead-ref + staleness detection and mechanical auto-fix (plan §8, §10.2)."""
from __future__ import annotations

from fux import check, fix, frontmatter
from conftest import write_rule

DEAD = """---
id: r1
type: rule
status: active
created: 2026-06-01
updated: 2026-06-01
code_refs:
  - src/exists.py#L1
  - src/gone.py#L9
---
**Rule:** something.
"""


def test_dead_ref_detected_and_fixed(project):
    (project / "src" / "exists.py").write_text("x = 1\n", encoding="utf-8")
    path = write_rule(project, "r1", DEAD)
    findings = check.run(project)
    dead = [f for f in findings if f.kind == "dead-ref"]
    assert len(dead) == 1 and "src/gone.py" in dead[0].message and dead[0].fixable

    fix.apply(project, findings)
    fm, _ = frontmatter.split(path.read_text())
    assert fm["code_refs"] == ["src/exists.py#L1"]   # dead ref dropped, live kept
    assert not [f for f in check.run(project) if f.kind == "dead-ref"]
