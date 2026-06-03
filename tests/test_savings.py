"""`fux savings` — measured token-cost estimate ($0, plan §12)."""
from __future__ import annotations

from fux import savings
from conftest import write_rule

RULE = """---
id: day-pnl
domain: portfolio
type: formula
status: active
created: 2026-06-01
updated: 2026-06-01
code_refs:
  - src/agg.py#L1-L2
---
**Rule:** Today's P&L uses current INR value, not invested cost.
"""


def _seed(project, big_lines: int = 400):
    # A governed file much larger than the rule that documents it.
    (project / "src" / "agg.py").write_text(
        "def day_pnl(h):\n" + "    x = 0\n" * big_lines, encoding="utf-8")
    write_rule(project, "day-pnl", RULE)


def test_aggregate_reports_measured_corpus(project):
    _seed(project)
    rep = savings.build(project)
    assert rep.n_rules == 1
    assert rep.index_tok > 0
    assert rep.topics == 1
    assert rep.governed_files == 1
    # The governed file is far larger than the rule → a real saving multiplier.
    assert rep.avg_without > rep.avg_rule
    assert rep.avg_ratio() > 1.0


def test_query_lookup_compares_with_vs_without(project):
    _seed(project)
    rep = savings.build(project, query="how is day pnl computed", top=3)
    lk = rep.lookup
    assert lk is not None and any(r.id == "day-pnl" for r in lk.rules)
    assert lk.without > lk.with_first > lk.with_later
    assert lk.ratio_later() > lk.ratio_first() > 1.0


def test_missing_code_ref_excluded_not_counted(project):
    write_rule(project, "ghost", RULE.replace("src/agg.py#L1-L2", "src/gone.py"))
    rep = savings.build(project)
    assert rep.topics == 0          # no existing governed file
    assert rep.governed_files == 0
    assert any("baseline" in n for n in rep.notes)


def test_render_is_stringable(project):
    _seed(project)
    text = savings.render(savings.build(project, query="day pnl"))
    assert "fux savings" in text and "cheaper" in text
