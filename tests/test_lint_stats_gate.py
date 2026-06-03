"""Rule-quality lint, the health dashboard, and the CI/pre-commit gate ($0)."""
from __future__ import annotations

import subprocess

from fux import build, gate, lint, stats
from conftest import write_rule

GOOD = """---
id: day-pnl
domain: portfolio
type: formula
status: active
created: 2026-06-01
updated: 2026-06-01
code_refs:
  - src/agg.py#L1-L2
---
**Rule:** Today's P&L uses current INR value.
**Why:** day_change_pct is relative to yesterday's close, so it multiplies today's value.
"""
# Missing **Why:**, no code_refs, dangling related → three distinct lint findings.
WEAK = """---
id: weak
type: formula
status: active
created: 2026-06-01
updated: 2026-06-01
related: [does-not-exist]
---
**Rule:** something happens here that is reasonably long but lacks a why.
"""


def _good(project):
    (project / "src" / "agg.py").write_text("def day_pnl(h):\n    return sum(h)\n")
    write_rule(project, "day-pnl", GOOD)


def test_lint_flags_quality_gaps(project):
    write_rule(project, "weak", WEAK)
    kinds = {f.kind for f in lint.run(project)}
    assert {"no-why", "no-code-refs", "dangling-edge"} <= kinds


def test_lint_clean_on_a_good_rule(project):
    _good(project)
    assert [f for f in lint.run(project) if f.rule_id == "day-pnl"] == []


def test_stats_scores_and_summarises(project):
    _good(project)
    build.run(project)
    st = stats.build(project)
    assert 0 <= st.score <= 100
    assert st.by_type.get("formula") == 1
    assert st.graph["nodes"] > 0          # graph.json was built
    assert "health" in stats.render(st)


def test_gate_passes_clean_and_blocks_on_dead_ref(project):
    _good(project)
    code, _ = gate.run(project)
    assert code == 0
    # Point a rule at a non-existent file → a blocking dead-ref finding.
    write_rule(project, "ghost", GOOD.replace("src/agg.py#L1-L2", "src/gone.py"))
    code, report = gate.run(project)
    assert code == 2 and "blocking" in report


def test_gate_installs_precommit_hook(project):
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    hook = gate.install_precommit(project)
    assert hook.exists() and hook.name == "pre-commit"
    assert hook.stat().st_mode & 0o111            # executable
    assert "fux gate" in hook.read_text()
