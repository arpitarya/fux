"""`fux impact` — blast radius of a file change (governing rules + callers, $0)."""
from __future__ import annotations

from conftest import write_rule

from fux import build, impact

_AGG = "def value():\n    return 1\n\n\ndef total():\n    return value()\n"
_CALLER = "from src.agg import total\n\n\ndef report():\n    return total()\n"

_INVARIANT = (
    "---\nid: valuation\ntype: invariant\ndomain: portfolio\nstatus: active\n"
    "code_refs:\n  - src/agg.py\nrelated: [naming]\n"
    'check: "total == sum(values)"\n---\n'
    "**Invariant:** the total equals the sum of its values.\n"
)
_CONVENTION = (
    "---\nid: naming\ntype: convention\ndomain: code-quality\nstatus: active\n"
    "code_refs:\n  - src/caller.py\n---\n**Rule:** name things well.\n"
)


def _setup(project):
    (project / "src" / "agg.py").write_text(_AGG)
    (project / "src" / "caller.py").write_text(_CALLER)
    write_rule(project, "valuation", _INVARIANT)
    write_rule(project, "naming", _CONVENTION)
    build.run(project)


def test_impact_finds_governing_invariant_and_callers(project):
    _setup(project)
    im = impact.run(project, "src/agg.py")
    assert im.in_graph
    assert [r.id for r in im.invariants] == ["valuation"]
    assert "src/caller.py" in im.callers          # report() calls agg.total()
    assert "naming" in im.related                 # one-hop related of valuation


def test_impact_render_is_an_actionable_checklist(project):
    _setup(project)
    text = impact.render(impact.run(project, "src/agg.py"))
    assert "fux verify" in text                   # invariants section present
    assert "`total == sum(values)`" in text       # the check assertion is shown
    assert "src/caller.py" in text                # downstream caller listed


def test_impact_unknown_file_is_flagged_not_in_graph(project):
    _setup(project)
    im = impact.run(project, "src/nope.py")
    assert not im.in_graph
    assert im.empty
